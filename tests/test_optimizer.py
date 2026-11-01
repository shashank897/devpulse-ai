import ast

from backend.optimizer import preview


def test_sqlite_query_variable_preview_parameterizes_and_preserves_source():
    source = '''import sqlite3
connection = sqlite3.connect("users.db")
query = f"SELECT * FROM users WHERE name = '{username}'"
connection.execute(query)
'''
    result = preview(source, 'python', 'security')
    suggestion = result['suggestions'][0]
    assert "query, query_params = \"SELECT * FROM users WHERE name = '?'\", (username,)" in suggestion['code']
    assert 'connection.execute(query, query_params)' in suggestion['code']
    ast.parse(suggestion['code'])
    assert 'query = f' not in suggestion['code']
    assert result['message'].startswith('The code was not run')


def test_sql_direct_preview_and_refuses_unproven_driver_or_formatting():
    safe_shape = 'import sqlite3\ndb = sqlite3.connect(":memory:")\ndb.execute(f"SELECT * FROM users WHERE id = {user_id}")'
    direct = preview(safe_shape, 'python', 'security')['suggestions'][0]['code']
    assert 'SELECT * FROM users WHERE id = ?' in direct and '(user_id,))' in direct
    assert preview('db.execute(f"SELECT {value}")', 'python', 'security')['suggestions'] == []
    assert preview('import sqlite3\ndb=sqlite3.connect(":memory:")\ndb.execute(f"SELECT {value!r}")', 'python', 'security')['suggestions'] == []


def test_performance_preview_updates_loop_target_and_keeps_valid_python():
    source = 'total = 0\nfor index in range(len(values)):\n    total += values[index]\n'
    result = preview(source, 'python', 'performance')
    updated = result['suggestions'][0]['code']
    assert 'for index, devpulse_item in enumerate(values):' in updated
    assert 'total += devpulse_item' in updated
    ast.parse(updated)
    assert 'Benchmark' in result['suggestions'][0]['note']


def test_previews_refuse_unsupported_and_oversize_inputs():
    assert preview('let x = 1', 'javascript', 'performance')['suggestions'] == []
    assert preview('for i in range(len(values)):\n    print(i)\n', 'python', 'performance')['suggestions'] == []
    shadowed_builtin = 'enumerate = custom\nfor i in range(len(values)):\n    print(values[i])\n'
    assert preview(shadowed_builtin, 'python', 'performance')['suggestions'] == []
    try:
        preview('x' * 100_001, 'python', 'security')
    except ValueError as error:
        assert '100 KB' in str(error)
    else:
        raise AssertionError('oversize code should be refused')
