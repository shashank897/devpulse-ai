"""Bounded evidence-based rules. No execution, shelling out or security certification."""
import ast
import hashlib
import re

MAX_BYTES = 100_000
LANGUAGES = {'.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript', '.c': 'c', '.cpp': 'cpp', '.h': 'c'}

def analyze(code: str, language: str, path: str = 'snippet.py') -> dict:
    if len(code.encode()) > MAX_BYTES:
        raise ValueError('Each file must be smaller than 100 KB.')
    lines = code.splitlines()
    findings = []
    complexity = 1
    functions = 0
    def add(rule, line, title, severity, description, fix):
        evidence = lines[line - 1].strip()[:250] if line <= len(lines) else ''
        if rule == 'SECRET-001': evidence = '[credential-like literal redacted]'
        findings.append(dict(id=hashlib.sha256(f'{path}:{rule}:{line}'.encode()).hexdigest()[:16], rule_id=rule, file_path=path, start_line=line, title=title, severity=severity, description=description, suggestion=fix, evidence=evidence, source='static-analysis', confidence=None, status='open'))
    if language == 'python':
        try: tree = ast.parse(code)
        except SyntaxError as exc: return {'findings': [], 'lines': len(lines), 'complexity': None, 'functions': 0, 'warnings': [f'{path}:{exc.lineno}: Python syntax error: {exc.msg}']}
        assignments = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name): assignments[target.id] = node.value
        for node in ast.walk(tree):
            complexity += isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp))
            functions += isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            if not isinstance(node, ast.Call): continue
            name = ast.unparse(node.func)
            if name in ('eval', 'exec'):
                add('PY-EVAL-001', node.lineno, 'Dynamic code execution', 'high', 'This call can execute arbitrary input as Python code. Verify whether untrusted input can reach it.', 'Use a structured parser such as json.loads, or a constrained allowlist.')
            if name in ('pickle.loads', 'pickle.load'):
                add('PY-PICKLE-001', node.lineno, 'Unsafe deserialization', 'high', 'Pickle can execute code during deserialization. Only trusted data is safe.', 'Use JSON for untrusted serialized data.')
            if name in ('os.system', 'os.popen') or (name.startswith('subprocess.') and any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords)):
                add('PY-SHELL-001', node.lineno, 'Shell command execution', 'high', 'Shell interpretation can turn untrusted input into executable commands.', 'Pass a list of arguments to subprocess.run with shell=False.')
            if name.endswith(('.execute', '.executemany')) and node.args:
                query = node.args[0]
                if isinstance(query, ast.Name): query = assignments.get(query.id, query)
                if isinstance(query, (ast.JoinedStr, ast.BinOp)) or (isinstance(query, ast.Call) and isinstance(query.func, ast.Attribute) and query.func.attr == 'format'):
                    add('PY-SQL-001', node.lineno, 'Potential SQL injection', 'high', 'A dynamically constructed query reaches a SQL execution call. Check whether interpolated values can be user-controlled.', 'Use parameter binding: connection.execute("SELECT * FROM users WHERE name = ?", (username,))')
            if name == 'tempfile.mktemp':
                add('PY-TEMP-001', node.lineno, 'Race-prone temporary file', 'medium', 'The returned path is not atomically created.', 'Use tempfile.NamedTemporaryFile or TemporaryDirectory.')
    elif language in ('javascript', 'typescript', 'c', 'cpp'):
        rules = [(r'\b(?:eval|Function)\s*\(', 'JS-EVAL-001', 'Dynamic code execution', 'high', 'Use JSON.parse or explicit dispatch instead.'), (r'\.innerHTML\s*=', 'JS-DOM-001', 'Potential unsafe HTML sink', 'medium', 'Use textContent for text; sanitize intentional HTML.')]
        if language in ('c', 'cpp'): rules = [(r'\b(?:strcpy|strcat|gets|sprintf)\s*\(', 'C-MEM-001', 'Unbounded memory operation', 'high', 'Use bounded operations and validate buffer sizes.')]
        for number, line in enumerate(lines, 1):
            if line.lstrip().startswith(('//', '/*', '*')): continue
            for pattern, rule, title, severity, fix in rules:
                if re.search(pattern, line): add(rule, number, title, severity, 'Pattern-based candidate; review input provenance and surrounding code. This rule is not a full data-flow analysis.', fix)
        complexity = None
    else: raise ValueError('Unsupported language.')
    for number, line in enumerate(lines, 1):
        if re.search(r'''(?i)\b(?:api_key|secret_key|password|access_token)\s*[:=]\s*["'][^"']{8,}["']''', line):
            add('SECRET-001', number, 'Credential-like literal', 'high', 'A credential-shaped value is embedded in source. Verify and rotate it if it is real.', 'Read secrets from environment variables or a secret manager.')
    return dict(findings=findings, lines=len(lines), complexity=complexity, functions=functions, warnings=[])

def sarif(scan):
    return {'version': '2.1.0', '$schema': 'https://json.schemastore.org/sarif-2.1.0.json', 'runs': [{'tool': {'driver': {'name': 'DevPulse AI', 'version': '0.1.0'}}, 'results': [{'ruleId': f['rule_id'], 'level': 'error' if f['severity'] in ('critical','high') else 'warning', 'message': {'text': f['title'] + ': ' + f['description']}, 'locations': [{'physicalLocation': {'artifactLocation': {'uri': f['file_path']}, 'region': {'startLine': f['start_line']}}}]} for f in scan['findings']]}]}
