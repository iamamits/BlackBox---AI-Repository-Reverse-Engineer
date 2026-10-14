"""BlackBox — Sandboxed Test Execution and Security Tests."""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.models import Investigation, InvestigationStatus, Patch, PatchStatus, Repository, RepoStatus, SandboxStatus, SourceType
from app.db.session import AsyncSessionLocal
from app.main import app
from app.sandbox.runner import execute_sandboxed_test, is_command_allowed


def test_command_allowlist_security():
    # Valid allowlisted commands
    assert is_command_allowed("pytest")
    assert is_command_allowed("pytest tests/test_smoke.py")
    assert is_command_allowed("npm test")
    assert is_command_allowed("cargo test --release")

    # Injections and dangerous attempts must be rejected
    assert not is_command_allowed("rm -rf /")
    assert not is_command_allowed("pytest; cat /etc/passwd")
    assert not is_command_allowed("pytest && whoami")
    assert not is_command_allowed("pytest | tee log.txt")
    assert not is_command_allowed("curl http://169.254.169.254/latest/meta-data/")
    assert not is_command_allowed("powershell -Command Remove-Item -Recurse C:\\")


@pytest.mark.asyncio
async def test_execute_sandboxed_test_disallowed():
    with tempfile.TemporaryDirectory() as tmp_dir:
        res = await execute_sandboxed_test("curl malicious.com", Path(tmp_dir))
        assert res.status == SandboxStatus.ERROR
        assert "rejected" in res.stderr.lower()


@pytest.mark.asyncio
async def test_patch_test_and_decision_endpoints():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        async with AsyncSessionLocal() as db:
            repo = Repository(
                name="test-sandbox-repo",
                source_type=SourceType.LOCAL,
                source_path=str(root),
                workspace_path=str(root),
                status=RepoStatus.READY,
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)

            inv = Investigation(
                repository_id=repo.id,
                question="Fix math error",
                status=InvestigationStatus.COMPLETE,
            )
            db.add(inv)
            await db.commit()
            await db.refresh(inv)

            patch = Patch(
                investigation_id=inv.id,
                diff="--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-1\n+2",
                explanation="Fix calculation",
                status=PatchStatus.PROPOSED,
            )
            db.add(patch)
            await db.commit()
            await db.refresh(patch)
            patch_id = patch.id

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test decision
            dec_resp = await client.post(
                f"/api/v1/patches/{patch_id}/decision",
                json={"decision": "accept"},
            )
            assert dec_resp.status_code == 200
            assert dec_resp.json()["status"] == "accepted"

            # Test sandbox test execution with rejected command
            test_resp = await client.post(
                f"/api/v1/patches/{patch_id}/test?command=curl+bad.com"
            )
            assert test_resp.status_code == 200
            t_data = test_resp.json()
            assert t_data["status"] == "error"
            assert "rejected" in t_data["stderr"].lower()

            # Test listing test runs
            runs_resp = await client.get(f"/api/v1/patches/{patch_id}/test_runs")
            assert runs_resp.status_code == 200
            assert len(runs_resp.json()) >= 1
