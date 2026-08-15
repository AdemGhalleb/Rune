from sqlalchemy import text

from app.db.database import create_database_engine


def test_sqlite_vec_loads_on_application_engine(app):
    engine = create_database_engine(app.state.settings)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT vec_version()")).scalar()
    finally:
        engine.dispose()
