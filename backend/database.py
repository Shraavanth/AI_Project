"""
Database connection.

Default: a local SQLite file at data/environmental_mas.db (no account needed).
Production: set DATABASE_URL to a PostgreSQL / Supabase connection string, e.g.
    postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DEFAULT_SQLITE_PATH = os.path.join(PROJECT_ROOT, "data", "environmental_mas.db")
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_SQLITE_PATH}"

# Render / Heroku style URLs use postgres:// which SQLAlchemy no longer accepts
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_SQLITE = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False, "timeout": 15} if IS_SQLITE else {}
if IS_SQLITE:
    os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        # WAL lets the API read history while the simulation loop is writing
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def database_label() -> str:
    if IS_SQLITE:
        return "SQLite (local file)"
    return "PostgreSQL"


def init_db():
    from backend import models  # noqa: F401  (registers the tables)
    Base.metadata.create_all(bind=engine)
