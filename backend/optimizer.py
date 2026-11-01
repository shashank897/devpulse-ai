"""Conservative, local code-edit previews. Never execute or retain submitted source."""
import ast


def _offset(source: str, line: int, column: int) -> int:
    lines = source.splitlines(keepends=True)
    prefix = sum(len(part) for part in lines[:line - 1])
    return prefix + len(lines[line - 1].encode("utf-8")[:column].decode("utf-8"))


def _span(source: str, node: ast.AST) -> tuple[int, int]:
    return (_offset(source, node.lineno, node.col_offset),
            _offset(source, node.end_lineno, node.end_col_offset))


def _apply(source: str, replacements: list[tuple[int, int, str]]) -> str:
    for start, end, value in sorted(replacements, reverse=True):
        source = source[:start] + value + source[end:]
    return source


def _sql_parts(query: ast.JoinedStr) -> tuple[str, list[str]] | None:
    pieces: list[str] = []
    parameters: list[str] = []
    literal_has_placeholder = False
    for item in query.values:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            pieces.append(item.value)
            literal_has_placeholder = literal_has_placeholder or "?" in item.value
        elif (isinstance(item, ast.FormattedValue) and isinstance(item.value, ast.Name)
              and item.conversion == -1 and item.format_spec is None):
            pieces.append("?")
            parameters.append(item.value.id)
        else:
            return None
    sql = "".join(pieces)
    if not parameters or literal_has_placeholder:
        return None
    return sql, parameters


def _sqlite_fstring_fix(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    sqlite_names = {alias.asname or alias.name for node in ast.walk(tree)
                    if isinstance(node, ast.Import) for alias in node.names
                    if alias.name == "sqlite3"}
    if not sqlite_names:
        return None
    connected_names = set()
    for node in ast.walk(tree):
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "connect" and isinstance(value.func.value, ast.Name)
                and value.func.value.id in sqlite_names):
            connected_names.update(target.id for target in targets if isinstance(target, ast.Name))
    if not connected_names:
        return None
    for call in ast.walk(tree):
        if (not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute)
                or call.func.attr != "execute" or call.keywords):
            continue
        receiver = call.func.value
        if not isinstance(receiver, ast.Name) or receiver.id not in connected_names:
            continue
        # Direct execute(f"...") form.
        if len(call.args) == 1 and isinstance(call.args[0], ast.JoinedStr):
            parts = _sql_parts(call.args[0])
            if not parts:
                continue
            sql, names = parts
            values = ", ".join(names) + ("," if len(names) == 1 else "")
            replacement = f"{receiver.id}.execute({sql!r}, ({values}))"
            start, end = _span(source, call)
            return {"title": "Bind SQL values instead of inserting them into the query",
                    "change": replacement, "code": _apply(source, [(start, end, replacement)]),
                    "note": "Preview applies to a simple SQLite call with plain variable values. Inspect the query and parameter order before using it."}
        # query = f"..." followed by connection.execute(query), used in the built-in example.
        if len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
            continue
        query_name = call.args[0].id
        assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))
                       and ((isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == query_name for t in node.targets))
                            or (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == query_name))]
        if len(assignments) != 1:
            continue
        assignment = assignments[0]
        value = assignment.value
        if not isinstance(value, ast.JoinedStr):
            continue
        parts = _sql_parts(value)
        if not parts:
            continue
        sql, names = parts
        # Only rewrite a query variable that is used by this execute call and nowhere else.
        other_uses = [node for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == query_name
                      and isinstance(node.ctx, ast.Load) and node is not call.args[0]]
        if other_uses:
            continue
        parameter_name = query_name + "_params"
        all_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        suffix = 2
        while parameter_name in all_names:
            parameter_name = f"{query_name}_params_{suffix}"
            suffix += 1
        values = ", ".join(names) + ("," if len(names) == 1 else "")
        new_assignment = f"{query_name}, {parameter_name} = {sql!r}, ({values})"
        new_call = f"{receiver.id}.execute({query_name}, {parameter_name})"
        start, end = _span(source, assignment)
        call_start, call_end = _span(source, call)
        return {"title": "Bind SQL values instead of inserting them into the query",
                "change": f"Parameterize {query_name} and pass its values separately.",
                "code": _apply(source, [(start, end, new_assignment), (call_start, call_end, new_call)]),
                "note": "Preview applies to a simple SQLite query variable with plain values and a single use. Review SQL dialect and parameter order before applying."}
    return None


def _enumerate_preview(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    if any(isinstance(node, ast.Name) and node.id in {"range", "len", "enumerate"}
           and isinstance(node.ctx, (ast.Store, ast.Del)) for node in ast.walk(tree)):
        return None
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    fresh = "devpulse_item"
    suffix = 2
    while fresh in names:
        fresh = f"devpulse_item_{suffix}"
        suffix += 1
    for loop in ast.walk(tree):
        if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name):
            continue
        iterator = loop.iter
        if not (isinstance(iterator, ast.Call) and isinstance(iterator.func, ast.Name)
                and iterator.func.id == "range" and len(iterator.args) == 1 and not iterator.keywords
                and isinstance(iterator.args[0], ast.Call)):
            continue
        length = iterator.args[0]
        if not (isinstance(length.func, ast.Name) and length.func.id == "len" and len(length.args) == 1
                and not length.keywords and isinstance(length.args[0], ast.Name)):
            continue
        index, sequence = loop.target.id, length.args[0].id
        body_nodes = [node for statement in loop.body for node in ast.walk(statement)]
        if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)) for node in body_nodes):
            continue
        if any(isinstance(node, ast.Name) and node.id in (index, sequence)
               and isinstance(node.ctx, (ast.Store, ast.Del)) for node in body_nodes):
            continue
        if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == sequence for node in body_nodes):
            continue
        uses = [node for node in body_nodes if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load)
                and isinstance(node.value, ast.Name) and node.value.id == sequence
                and isinstance(node.slice, ast.Name) and node.slice.id == index]
        if not uses:
            continue
        start, end = _span(source, iterator)
        target_start, target_end = _span(source, loop.target)
        replacements = [(start, end, f"enumerate({sequence})"),
                        (target_start, target_end, f"{index}, {fresh}")]
        replacements.extend((*_span(source, use), fresh) for use in uses)
        return {"title": "Avoid repeated indexing in this loop",
                "change": f"Iterate with enumerate({sequence}) and reuse {fresh}.",
                "code": _apply(source, replacements),
                "note": "This matches a simple read-only range(len(sequence)) loop. Confirm the sequence is not mutated indirectly and compare outputs. Benchmark both versions; enumerate is not guaranteed to be faster in every program."}
    return None


def preview(source: str, language: str, category: str):
    if len(source.encode("utf-8")) > 100_000:
        raise ValueError("Code exceeds 100 KB.")
    if language != "python":
        return {"category": category, "suggestions": [],
                "message": "Conservative previews currently support Python only. Review the analysis guidance and edit the code yourself."}
    if category == "security":
        fix = _sqlite_fstring_fix(source)
    elif category == "performance":
        fix = _enumerate_preview(source)
    else:
        raise ValueError("Choose security or performance suggestions.")
    if fix is None:
        return {"category": category, "suggestions": [],
                "message": "No conservative automatic preview matched. Review the analysis guidance and edit the code yourself."}
    return {"category": category, "suggestions": [dict(id=category + "-preview-1", **fix)],
            "message": "The code was not run, saved or sent to an external model."}
