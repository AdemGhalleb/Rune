import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.database import create_database_engine, create_session_factory, run_migrations
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    settings = Settings(data_dir=tmp_path / "rune-data")
    return create_app(settings=settings)


@pytest.fixture
async def client(app):
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def session_factory(app):
    settings = app.state.settings
    run_migrations(settings)
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    yield factory
    engine.dispose()


@pytest.fixture
def db_session(session_factory):
    with session_factory() as session:
        yield session

