"""SQLite engine, session management, and migration startup helpers."""

from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.sqlite_vec import load_sqlite_vec_extension


def create_database_engine(settings: Settings) -> Engine:
    """Create a SQLite engine configured for Rune's local desktop workload."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
        load_sqlite_vec_extension(dbapi_connection)
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield and always close a database session."""
    with session_factory() as session:
        yield session


def run_migrations(settings: Settings) -> None:
    """Upgrade the application's local database to the latest Alembic revision."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    backend_dir = Path(__file__).resolve().parents[2]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
