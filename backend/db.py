import os
from sqlalchemy import create_engine, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

url = os.getenv('DATABASE_URL', 'sqlite:///./devpulse.db').replace('postgres://', 'postgresql+psycopg://', 1)
if url.startswith('postgresql://'): url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {}, pool_pre_ping=True)
Session = sessionmaker(engine)
class Base(DeclarativeBase): pass
class Scan(Base):
    __tablename__ = 'scans'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(20), default='queued')
    payload: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
