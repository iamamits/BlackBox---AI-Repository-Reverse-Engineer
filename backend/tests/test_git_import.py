"""BlackBox — Git Repository Ingestion & Clone Engine Tests."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.indexing.git_service import extract_repo_name, validate_git_url
from app.main import app


def test_validate_git_url():
    # Valid URLs
    ok, _ = validate_git_url("https://github.com/fastapi/fastapi")
    assert ok
    ok, _ = validate_git_url("https://github.com/Hack-with-Github/Awesome-Hacking.git")
    assert ok

    # Blocked SSRF URLs
    ok, reason = validate_git_url("http://localhost:8000/repo.git")
    assert not ok
    assert "blocked" in reason.lower() or "ssrf" in reason.lower()

    ok, _ = validate_git_url("http://127.0.0.1:3000/evil.git")
    assert not ok

    ok, _ = validate_git_url("http://169.254.169.254/latest/meta-data")
    assert not ok

    # Invalid scheme
    ok, _ = validate_git_url("file:///etc/passwd")
    assert not ok


def test_extract_repo_name():
    assert extract_repo_name("https://github.com/Hack-with-Github/Awesome-Hacking") == "Awesome-Hacking"
    assert extract_repo_name("https://github.com/fastapi/fastapi.git") == "fastapi"
    assert extract_repo_name("https://gitlab.com/group/sub/my-repo/") == "my-repo"


@pytest.mark.asyncio
async def test_git_import_endpoint_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Invalid URL scheme
        resp = await client.post("/api/v1/repos/import/git", json={"url": "ftp://bad-url.com/repo.git"})
        assert resp.status_code == 400

        # 2. SSRF URL
        resp = await client.post("/api/v1/repos/import/git", json={"url": "http://127.0.0.1/evil.git"})
        assert resp.status_code == 400
        assert "blocked" in resp.json()["detail"].lower() or "ssrf" in resp.json()["detail"].lower()

        # 3. Valid URL creation
        resp = await client.post(
            "/api/v1/repos/import/git",
            json={"url": "https://github.com/test-org/test-repo.git", "name": "test-repo"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-repo"
        assert data["source_type"] == "git"
        assert data["status"] in ("pending", "indexing")
