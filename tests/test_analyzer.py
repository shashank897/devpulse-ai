import pytest
from backend.analyzer import analyze, sarif

def test_sql_unsafe_and_parameterized_safe():
    unsafe='query = f"SELECT * FROM users WHERE name = {name}"\nconnection.execute(query)'
    assert analyze(unsafe,'python')['findings'][0]['rule_id']=='PY-SQL-001'
    safe='connection.execute("SELECT * FROM users WHERE name = ?", (name,))'
    assert analyze(safe,'python')['findings']==[]

def test_no_execute_in_comments_or_strings():
    assert analyze('# eval(user_input)\ntext = "eval(x)"','python')['findings']==[]

@pytest.mark.parametrize('source,rule', [('eval(user_input)','PY-EVAL-001'),('pickle.loads(data)','PY-PICKLE-001'),('subprocess.run(command, shell=True)','PY-SHELL-001'),('tempfile.mktemp()','PY-TEMP-001')])
def test_unsafe_rules(source,rule):
    assert analyze(source,'python')['findings'][0]['rule_id']==rule

def test_shell_false_is_not_flagged():
    assert analyze('subprocess.run(["echo", user], shell=False)','python')['findings']==[]

def test_syntax_error_is_not_clean_scan():
    result=analyze('def broken(','python')
    assert result['warnings'] and result['complexity'] is None

def test_secret_redaction():
    f=analyze('api_key = "not-a-real-secret-value"','python')['findings'][0]
    assert f['evidence']=='[credential-like literal redacted]'

def test_resource_limits():
    with pytest.raises(ValueError): analyze('a'*100001,'python')

def test_language_specific_rules():
    assert analyze('strcpy(dest, src);','c')['findings'][0]['rule_id']=='C-MEM-001'
    assert analyze('el.innerHTML = user;','javascript')['findings'][0]['rule_id']=='JS-DOM-001'

def test_sarif_locations():
    result=analyze('eval(x)','python','app.py')
    export=sarif(result)
    assert export['runs'][0]['results'][0]['locations'][0]['physicalLocation']['region']['startLine']==1
