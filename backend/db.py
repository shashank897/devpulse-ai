import os
from sqlalchemy import create_engine, String, Text, DateTime, func, MetaData
from sqlalchemy.schema import CreateSchema
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

raw_url = os.getenv('DATABASE_URL', 'sqlite:///./devpulse.db').strip()
if len(raw_url) > 1 and raw_url[0] in ('"', "'") and raw_url[-1] == raw_url[0]:
    raw_url = raw_url[1:-1].strip()
url = raw_url.replace('postgres://', 'postgresql+psycopg://', 1)
if url.startswith('postgresql://'): url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
is_postgres = url.startswith('postgresql')
connection_url = make_url(url)
if is_postgres and (connection_url.host or '').endswith('.render.com') and 'sslmode' not in connection_url.query:
    connection_url = connection_url.update_query_dict({'sslmode': 'require'})
# Both products can share an instance without sharing application tables.
SCHEMA = 'devpulse' if is_postgres else None
engine_options = (
    {'pool_size': 2, 'max_overflow': 1, 'pool_timeout': 10, 'pool_recycle': 300,
     'connect_args': {'connect_timeout': 10, 'application_name': 'devpulse-ai'}}
    if is_postgres else {'connect_args': {'check_same_thread': False}}
)
engine = create_engine(connection_url, pool_pre_ping=True, **engine_options)
Session = sessionmaker(engine)
class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)
class Scan(Base):
    __tablename__ = 'scans'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(20), default='queued')
    payload: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())


def initialize_database():
    with engine.begin() as connection:
        if SCHEMA:
            connection.execute(CreateSchema(SCHEMA, if_not_exists=True))
        Base.metadata.create_all(connection)
