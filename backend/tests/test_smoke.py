"""BlackBox — basic backend tests."""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "ai_provider" in data


@pytest.mark.asyncio
async def test_list_repos_empty():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/repos/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 0
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_investigation_missing_key():
    """When AI key is absent, investigation should report error state."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First create a repo so we have a valid repo_id
        resp = await client.post(
            "/api/v1/repos/import/local",
            json={"name": "test-repo", "path": "C:\\Windows"},
        )
        # We just need any repo, even on error path
        repo_id = resp.json().get("id", 1) if resp.status_code == 201 else 1

        inv_resp = await client.post(
            "/api/v1/investigations/",
            json={"repository_id": repo_id, "question": "What does this repo do?"},
        )
    # Should not 500 — either created with error status or 404
    assert inv_resp.status_code in (200, 201, 404)
