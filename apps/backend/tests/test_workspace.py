from sqlalchemy import inspect

from app.db.database import create_database_engine, create_session_factory, run_migrations
from app.services.workspace import WorkspaceService


async def test_database_initialization_uses_initial_migration(app):
    settings = app.state.settings
    run_migrations(settings)
    engine = create_database_engine(settings)
    try:
        assert "workspaces" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


async def test_workspace_can_be_created_and_retrieved(client, tmp_path):
    workspace_path = tmp_path / "semester"
    workspace_path.mkdir()

    created = await client.put("/api/v1/workspace", json={"root_path": str(workspace_path)})
    assert created.status_code == 200
    data = created.json()
    assert data["name"] == "semester"
    assert data["root_path"] == str(workspace_path.resolve())

    retrieved = await client.get("/api/v1/workspace")
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == data["id"]


async def test_invalid_workspace_path_is_rejected(client, tmp_path):
    response = await client.put("/api/v1/workspace", json={"root_path": str(tmp_path / "missing")})
    assert response.status_code == 422
    assert response.json()["detail"] == "Workspace path must be an existing directory"


async def test_workspace_persists_across_separate_database_sessions(app, tmp_path):
    workspace_path = tmp_path / "coursework"
    workspace_path.mkdir()
    settings = app.state.settings
    run_migrations(settings)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    service = WorkspaceService()

    try:
        with session_factory() as first_session:
            created = service.set_current(
                first_session, root_path=str(workspace_path), name="Coursework"
            )

        with session_factory() as second_session:
            retrieved = service.get_current(second_session)
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.root_path == str(workspace_path.resolve())
            assert retrieved.name == "Coursework"
    finally:
        engine.dispose()


async def test_workspace_can_be_deleted(client, tmp_path):
    workspace_path = tmp_path / "to_delete"
    workspace_path.mkdir()

    await client.put("/api/v1/workspace", json={"root_path": str(workspace_path)})

    delete_resp = await client.delete("/api/v1/workspace")
    assert delete_resp.status_code == 204

    get_resp = await client.get("/api/v1/workspace")
    assert get_resp.status_code == 200
    assert get_resp.json() is None


async def test_workspace_can_be_updated(client, tmp_path):
    w1 = tmp_path / "w1"
    w2 = tmp_path / "w2"
    w1.mkdir()
    w2.mkdir()

    await client.put("/api/v1/workspace", json={"root_path": str(w1)})

    patch_resp = await client.patch(
        "/api/v1/workspace", json={"root_path": str(w2), "name": "Updated Workspace"}
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "Updated Workspace"
    assert data["root_path"] == str(w2.resolve())


def test_default_data_dir_resolves_to_user_appdata():
    from app.core.config import Settings

    settings = Settings()
    assert "Rune" in str(settings.data_dir)
    assert str(settings.database_path).endswith("rune.db")

