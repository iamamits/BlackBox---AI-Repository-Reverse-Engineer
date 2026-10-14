"""BlackBox — AI Provider and Prompt Orchestration Tests."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import select

from app.ai.prompts import build_investigation_prompt
from app.ai.provider import NebiusAIProvider
from app.ai.schemas import InvestigationStructuredOutput
from app.api.investigate import _run_investigation
from app.core.models import Investigation, InvestigationStatus, Repository, RepoStatus, SourceType
from app.db.session import AsyncSessionLocal


def test_build_investigation_prompt():
    files = [{"path": "app/main.py", "language": "python", "line_count": 50}]
    symbols = [{"name": "lifespan", "kind": "function", "file": "app/main.py", "signature": "async def lifespan()"}]
    edges = ["import: app.config"]

    prompt = build_investigation_prompt(
        repo_name="TestRepo",
        question="How does startup initialization work?",
        files_summary=files,
        symbols_summary=symbols,
        dependency_edges=edges,
    )

    assert "REPOSITORY: TestRepo" in prompt
    assert "USER INVESTIGATION QUESTION: How does startup initialization work?" in prompt
    assert "app/main.py" in prompt
    assert "lifespan" in prompt
    assert "import: app.config" in prompt


@pytest.mark.asyncio
async def test_nebius_provider_mocked_success():
    provider = NebiusAIProvider(api_key="mock-key-123", model="meta-llama/Meta-Llama-3.1-70B-Instruct")
    assert provider.is_configured

    mock_llm_json = {
        "summary": "Verified startup lifespan context initializes database tables cleanly.",
        "classification": "architecture_query",
        "confidence": "high",
        "findings": [
            {
                "title": "Clean Lifespan Hook",
                "description": "Uses asynccontextmanager for graceful engine disposal.",
                "severity": "low",
                "file": "app/main.py",
                "line": 42,
            }
        ],
        "evidence_refs": [
            {
                "file": "app/main.py",
                "lines": "41-55",
                "snippet": "async with engine.begin() as conn: await conn.run_sync(...)",
            }
        ],
        "proposed_patch_diff": None,
        "proposed_patch_explanation": None,
    }

    from unittest.mock import MagicMock

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(
        return_value={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]}
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        output = await provider.investigate(
            repo_name="TestRepo",
            question="Explain startup",
            files_summary=[],
            symbols_summary=[],
        )

        assert isinstance(output, InvestigationStructuredOutput)
        assert output.confidence == "high"
        assert len(output.findings) == 1
        assert output.findings[0].title == "Clean Lifespan Hook"
        assert output.findings[0].file == "app/main.py"


@pytest.mark.asyncio
async def test_nebius_provider_unconfigured():
    provider = NebiusAIProvider(api_key="")
    assert not provider.is_configured
    with pytest.raises(ValueError, match="Nebius API key is not configured"):
        await provider.investigate(
            repo_name="TestRepo",
            question="Why is this broken?",
            files_summary=[],
            symbols_summary=[],
        )


@pytest.mark.asyncio
async def test_investigation_worker_flow():
    # 1. Create a repository
    async with AsyncSessionLocal() as db:
        repo = Repository(
            name="test-ai-repo",
            source_type=SourceType.LOCAL,
            source_path=".",
            status=RepoStatus.READY,
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

        # 2. Create an investigation
        inv = Investigation(
            repository_id=repo.id,
            question="Trace database engine disposal",
            status=InvestigationStatus.PENDING,
        )
        db.add(inv)
        await db.commit()
        await db.refresh(inv)
        inv_id = inv.id

    mock_output = InvestigationStructuredOutput(
        summary="Engine disposal is executed on application shutdown.",
        classification="architecture_query",
        confidence="high",
        findings=[],
        evidence_refs=[],
    )

    with patch.object(NebiusAIProvider, "investigate", return_value=mock_output):
        await _run_investigation(inv_id)

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Investigation).where(Investigation.id == inv_id))
        completed_inv = res.scalar_one()

        assert completed_inv.status == InvestigationStatus.COMPLETE
        assert "Engine disposal" in completed_inv.summary
        assert completed_inv.provider_used == "nebius"
