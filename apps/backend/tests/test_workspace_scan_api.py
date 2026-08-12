import asyncio
import pytest
from httpx import AsyncClient


async def test_scan_endpoints_without_workspace_return_404(client: AsyncClient):
    resp = await client.post("/api/v1/workspace/scan")
    assert resp.status_code == 404

    resp = await client.get("/api/v1/workspace/overview")
    assert resp.status_code == 404

    resp = await client.get("/api/v1/workspace/files")
    assert resp.status_code == 404


async def test_scan_overview_and_files_workflow(client: AsyncClient, tmp_path):
    ws_dir = tmp_path / "research_notes"
    ws_dir.mkdir()

    (ws_dir / "paper.pdf").write_text("dummy pdf content")
    (ws_dir / "notes.md").write_text("# Notes\nSome content")
    sub = ws_dir / "code"
    sub.mkdir()
    (sub / "main.py").write_text("print('hello')")

    # Set workspace
    set_resp = await client.put("/api/v1/workspace", json={"root_path": str(ws_dir)})
    assert set_resp.status_code == 200

    # Overview before scan should have 0 files
    overview_before = await client.get("/api/v1/workspace/overview")
    assert overview_before.status_code == 200
    assert overview_before.json()["total_files"] == 0

    # Trigger scan
    scan_resp = await client.post("/api/v1/workspace/scan")
    assert scan_resp.status_code == 202
    job_data = scan_resp.json()
    assert job_data["status"] in ("running", "completed")

    # Poll for completion
    for _ in range(50):
        latest_resp = await client.get("/api/v1/workspace/scan/latest")
        assert latest_resp.status_code == 200
        latest_data = latest_resp.json()
        if latest_data["status"] in ("completed", "failed", "cancelled"):
            break
        await asyncio.sleep(0.1)

    assert latest_data["status"] == "completed"
    assert latest_data["files_discovered"] == 3

    # Check Overview after scan
    overview_after = await client.get("/api/v1/workspace/overview")
    assert overview_after.status_code == 200
    data = overview_after.json()
    assert data["total_files"] == 3
    assert data["files_by_category"]["document"] == 1  # .pdf
    assert data["files_by_category"]["note"] == 1  # .md
    assert data["files_by_category"]["code"] == 1  # .py
    assert len(data["recent_files"]) <= 5

    # Check File List
    files_resp = await client.get("/api/v1/workspace/files")
    assert files_resp.status_code == 200
    files_data = files_resp.json()
    assert files_data["total"] == 3
    assert len(files_data["items"]) == 3

    # Filter by category
    code_files = await client.get("/api/v1/workspace/files?category=code")
    assert code_files.status_code == 200
    assert code_files.json()["total"] == 1
    assert code_files.json()["items"][0]["filename"] == "main.py"

    # Search filter
    search_resp = await client.get("/api/v1/workspace/files?search=paper")
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["filename"] == "paper.pdf"


async def test_scan_cancel_endpoint(client: AsyncClient, tmp_path):
    ws_dir = tmp_path / "big_ws"
    ws_dir.mkdir()
    for i in range(100):
        (ws_dir / f"file_{i}.txt").write_text(f"content {i}")

    await client.put("/api/v1/workspace", json={"root_path": str(ws_dir)})

    await client.post("/api/v1/workspace/scan")
    cancel_resp = await client.post("/api/v1/workspace/scan/cancel")
    assert cancel_resp.status_code == 200
    assert "cancelled" in cancel_resp.json()
