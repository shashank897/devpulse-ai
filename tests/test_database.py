import os
import subprocess
import sys
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateSchema
from backend import db, main


@pytest.mark.parametrize('database_url', [
    'postgres://test:test@example.oregon-postgres.render.com/test',
    '  postgresql://test:test@example.oregon-postgres.render.com/test\n',
    "'postgresql://test:test@example.oregon-postgres.render.com/test'",
    '"postgres://test:test@example.oregon-postgres.render.com/test"',
])
def test_postgres_schema_and_connection_budget(database_url):
    # Import in a separate process so the API tests keep their SQLite database.
    script = '''
from backend import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
assert db.SCHEMA == 'devpulse'
sql = str(CreateTable(db.Scan.__table__).compile(dialect=postgresql.dialect()))
assert 'CREATE TABLE devpulse.scans' in sql
assert db.engine.pool.size() == 2
assert db.engine.pool._max_overflow == 1
assert db.engine.url.drivername == 'postgresql+psycopg'
assert db.engine.url.query['sslmode'] == 'require'
'''
    env = dict(os.environ, DATABASE_URL=database_url)
    result = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_initializer_creates_only_app_schema(monkeypatch):
    statements = []
    class Connection:
        def execute(self, statement):
            statements.append(statement)
    connection = Connection()
    class Engine:
        @contextmanager
        def begin(self):
            yield connection
    monkeypatch.setattr(db, 'engine', Engine())
    monkeypatch.setattr(db, 'SCHEMA', 'devpulse')
    tables = []
    monkeypatch.setattr(db.Base.metadata, 'create_all', lambda c: tables.append(c))
    db.initialize_database()
    assert len(statements) == 1 and isinstance(statements[0], CreateSchema)
    assert statements[0].element == 'devpulse' and statements[0].if_not_exists
    assert tables == [connection]


def test_health_hides_database_failure_details(monkeypatch):
    class Unavailable:
        def connect(self):
            raise SQLAlchemyError('private connection details')
    monkeypatch.setattr(main, 'engine', Unavailable())
    with pytest.raises(HTTPException) as error:
        main.health()
    assert error.value.status_code == 503
    assert error.value.detail == 'Database is temporarily unavailable.'
