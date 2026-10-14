"""Tests for BlackBox User Auth, Data Isolation, and Report Engine."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing_and_token():
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert "$" in hashed
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    # Token creation & decoding
    token = create_access_token({"sub": "42", "username": "alice"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["username"] == "alice"


@pytest.mark.asyncio
async def test_auth_registration_and_login_flow():
    import uuid
    uid = uuid.uuid4().hex[:8]
    email = f"test_{uid}@example.com"
    username = f"user_{uid}"

    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register new user
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "Password123!",
                "full_name": "Test Architect",
            },
        )
        assert reg_resp.status_code == 201
        data = reg_resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == username
        token = data["access_token"]

        # 2. Login with valid credentials
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": username, "password": "Password123!"},
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

        # 3. Invalid password
        bad_login = await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": username, "password": "WrongPassword"},
        )
        assert bad_login.status_code == 401

        # 4. Check /auth/me with Bearer token
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user"]["email"] == email
        assert "repository_count" in me_data


@pytest.mark.asyncio
async def test_report_generation_and_export():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a repo
        repo_resp = await client.post(
            "/api/v1/repos/import/local",
            json={"name": "test-report-repo", "path": "C:\\Windows"},
        )
        repo_id = repo_resp.json().get("id", 1) if repo_resp.status_code == 201 else 1

        # Fetch report JSON
        rep_resp = await client.get(f"/api/v1/reports/{repo_id}")
        assert rep_resp.status_code == 200
        rep_data = rep_resp.json()
        assert "health_score" in rep_data
        assert "security_grade" in rep_data
        assert "metrics" in rep_data
        assert len(rep_data["metrics"]) >= 4

        # Download report as HTML
        html_resp = await client.get(f"/api/v1/reports/{repo_id}/download?format=html")
        assert html_resp.status_code == 200
        assert "text/html" in html_resp.headers["content-type"]
        assert "BlackBox Audit Report" in html_resp.text

        # Download report as Markdown
        md_resp = await client.get(f"/api/v1/reports/{repo_id}/download?format=markdown")
        assert md_resp.status_code == 200
        assert "text/markdown" in md_resp.headers["content-type"]
        assert "# BlackBox Repository Audit Report" in md_resp.text
