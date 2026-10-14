from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Investigation, Patch, PatchStatus, Repository, TestRun
from app.core.schemas import PatchCreate, PatchDecision, PatchRead, TestRunRead
from app.db.session import get_db
from app.sandbox.runner import execute_sandboxed_test

router = APIRouter(prefix="/patches", tags=["patches"])


@router.post(
    "/",
    response_model=PatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a patch proposal",
)
async def create_patch(
    payload: PatchCreate,
    db: AsyncSession = Depends(get_db),
) -> PatchRead:
    patch = Patch(
        investigation_id=payload.investigation_id,
        diff=payload.diff,
        explanation=payload.explanation,
        status=PatchStatus.PROPOSED,
    )
    db.add(patch)
    await db.flush()
    await db.refresh(patch)
    return PatchRead.model_validate(patch)


@router.get("/{patch_id}", response_model=PatchRead, summary="Get a patch")
async def get_patch(patch_id: int, db: AsyncSession = Depends(get_db)) -> PatchRead:
    result = await db.execute(select(Patch).where(Patch.id == patch_id))
    patch = result.scalar_one_or_none()
    if not patch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")
    return PatchRead.model_validate(patch)


@router.post("/{patch_id}/decision", response_model=PatchRead, summary="Accept or reject a patch")
async def decide_patch(
    patch_id: int,
    payload: PatchDecision,
    db: AsyncSession = Depends(get_db),
) -> PatchRead:
    if payload.decision not in ("accept", "reject"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="decision must be 'accept' or 'reject'",
        )
    result = await db.execute(select(Patch).where(Patch.id == patch_id))
    patch = result.scalar_one_or_none()
    if not patch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")

    patch.status = PatchStatus.ACCEPTED if payload.decision == "accept" else PatchStatus.REJECTED
    return PatchRead.model_validate(patch)


@router.post("/{patch_id}/test", response_model=TestRunRead, summary="Run tests in sandbox for a patch")
async def test_patch(
    patch_id: int,
    command: str = Query(default="pytest", description="Test command to execute"),
    db: AsyncSession = Depends(get_db),
) -> TestRunRead:
    result = await db.execute(select(Patch).where(Patch.id == patch_id))
    patch = result.scalar_one_or_none()
    if not patch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")

    # Fetch repo
    inv_res = await db.execute(select(Investigation).where(Investigation.id == patch.investigation_id))
    inv = inv_res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated investigation not found")

    repo_res = await db.execute(select(Repository).where(Repository.id == inv.repository_id))
    repo = repo_res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated repository not found")

    workspace = Path(repo.workspace_path or repo.source_path)
    run_result = await execute_sandboxed_test(command=command, cwd=workspace)

    test_run = TestRun(
        patch_id=patch.id,
        repository_id=repo.id,
        command=command,
        exit_code=run_result.exit_code,
        stdout=run_result.stdout,
        stderr=run_result.stderr,
        duration_seconds=run_result.duration_seconds,
        status=run_result.status,
    )
    db.add(test_run)
    await db.commit()
    await db.refresh(test_run)

    return TestRunRead.model_validate(test_run)


@router.get("/{patch_id}/test_runs", response_model=list[TestRunRead], summary="List test runs for a patch")
async def list_patch_test_runs(
    patch_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[TestRunRead]:
    result = await db.execute(
        select(TestRun)
        .where(TestRun.patch_id == patch_id)
        .order_by(TestRun.created_at.desc())
    )
    return [TestRunRead.model_validate(tr) for tr in result.scalars().all()]
