"""BlackBox — AI Investigation API router."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Investigation, InvestigationStatus, Repository
from app.core.schemas import InvestigationCreate, InvestigationRead
from app.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post(
    "/",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an AI investigation",
)
async def create_investigation(
    payload: InvestigationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> InvestigationRead:
    settings = get_settings()

    # Verify repo
    repo_result = await db.execute(select(Repository).where(Repository.id == payload.repository_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    investigation = Investigation(
        repository_id=payload.repository_id,
        question=payload.question,
        status=InvestigationStatus.PENDING,
        model_used=settings.nebius_model if settings.ai_enabled else None,
        provider_used="nebius" if settings.ai_enabled else None,
    )
    db.add(investigation)
    await db.flush()
    await db.refresh(investigation)

    # Actual AI invocation wired in Milestone 4
    if not settings.ai_enabled:
        investigation.status = InvestigationStatus.ERROR
        investigation.error_message = (
            "AI provider not configured. Set NEBIUS_API_KEY in your .env file "
            "to enable AI-powered investigations."
        )
    else:
        investigation.status = InvestigationStatus.PENDING
        if settings.redis_enabled:
            from app.queue.jobs import enqueue_job
            background_tasks.add_task(
                enqueue_job, "run_investigation", {"investigation_id": investigation.id}
            )
        else:
            background_tasks.add_task(_run_investigation, investigation.id)

    return InvestigationRead.model_validate(investigation)


@router.get(
    "/{investigation_id}",
    response_model=InvestigationRead,
    summary="Get investigation details",
)
async def get_investigation(
    investigation_id: int,
    db: AsyncSession = Depends(get_db),
) -> InvestigationRead:
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")
    return InvestigationRead.model_validate(inv)


@router.get(
    "/repo/{repo_id}",
    response_model=list[InvestigationRead],
    summary="List investigations for a repository",
)
async def list_investigations(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[InvestigationRead]:
    result = await db.execute(
        select(Investigation)
        .where(Investigation.repository_id == repo_id)
        .order_by(Investigation.created_at.desc())
        .limit(50)
    )
    return [InvestigationRead.model_validate(i) for i in result.scalars().all()]


async def _run_investigation(investigation_id: int) -> None:
    """Execute AI investigation with Nebius / NVIDIA open model inference."""
    from app.ai.provider import NebiusAIProvider
    from app.core.models import Dependency, IndexedFile, Patch, PatchStatus, Symbol
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = res.scalar_one_or_none()
        if not inv:
            return

        inv.status = InvestigationStatus.RUNNING
        await db.commit()

        try:
            # 1. Fetch repo
            repo_res = await db.execute(select(Repository).where(Repository.id == inv.repository_id))
            repo = repo_res.scalar_one_or_none()
            if not repo:
                raise ValueError("Associated repository not found")

            # 2. Gather grounded context
            files_res = await db.execute(
                select(IndexedFile).where(IndexedFile.repository_id == repo.id).limit(25)
            )
            files = files_res.scalars().all()
            files_summary = [
                {"path": f.path, "language": f.language, "line_count": f.line_count}
                for f in files
            ]

            symbols_res = await db.execute(
                select(Symbol, IndexedFile)
                .join(IndexedFile, Symbol.file_id == IndexedFile.id)
                .where(Symbol.repository_id == repo.id)
                .limit(40)
            )
            symbols_summary = [
                {
                    "name": s.name,
                    "kind": s.kind.value,
                    "file": f.path,
                    "signature": s.signature,
                }
                for s, f in symbols_res.all()
            ]

            deps_res = await db.execute(
                select(Dependency).where(Dependency.repository_id == repo.id).limit(20)
            )
            edges_summary = [
                f"{d.dep_type.value}: {d.evidence or 'link'}" for d in deps_res.scalars().all()
            ]

            # 3. Call AI provider
            provider = NebiusAIProvider()
            output = await provider.investigate(
                repo_name=repo.name,
                question=inv.question,
                files_summary=files_summary,
                symbols_summary=symbols_summary,
                dependency_edges=edges_summary,
            )

            # 4. Save results
            inv.status = InvestigationStatus.COMPLETE
            inv.summary = output.summary
            inv.classification = output.classification
            inv.confidence = output.confidence
            inv.findings = json.dumps([f.model_dump() for f in output.findings])
            inv.evidence_refs = json.dumps([e.model_dump() for e in output.evidence_refs])
            inv.model_used = provider.model
            inv.provider_used = "nebius"

            # 5. Save proposed patch if present
            if output.proposed_patch_diff:
                patch = Patch(
                    investigation_id=inv.id,
                    diff=output.proposed_patch_diff,
                    explanation=output.proposed_patch_explanation,
                    status=PatchStatus.PROPOSED,
                )
                db.add(patch)

            await db.commit()

        except Exception as e:
            inv.status = InvestigationStatus.ERROR
            inv.error_message = str(e)
            await db.commit()
