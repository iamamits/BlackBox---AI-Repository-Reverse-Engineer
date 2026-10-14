"""BlackBox — Repository API router."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import IndexedFile, Repository, RepoStatus, SourceType, User
from app.core.schemas import (
    RepoImportGit,
    RepoImportLocal,
    RepoList,
    RepoRead,
    RepoSummary,
)
from app.core.security import get_optional_user
from app.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/repos", tags=["repositories"])


async def _start_indexing(repo_id: int) -> None:
    """Run full repository scanning, symbol extraction, and indexing via Upstash Redis or local task."""
    settings = get_settings()
    if settings.redis_enabled:
        from app.queue.jobs import enqueue_job
        await enqueue_job("index_repository", {"repo_id": repo_id})
    else:
        from app.indexing.service import index_repository
        await index_repository(repo_id)


@router.get("/", response_model=RepoList, summary="List all repositories")
async def list_repos(
    optional_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> RepoList:
    query = select(Repository)
    if optional_user:
        # If user is authenticated, prioritize user-isolated repos + public unassigned repos
        query = query.where(or_(Repository.user_id == optional_user.id, Repository.user_id.is_(None)))
    query = query.order_by(Repository.created_at.desc())

    result = await db.execute(query)
    repos = result.scalars().all()
    return RepoList(
        items=[RepoSummary.model_validate(r) for r in repos],
        total=len(repos),
    )


@router.post(
    "/import/local",
    response_model=RepoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a local repository folder",
)
async def import_local(
    payload: RepoImportLocal,
    background_tasks: BackgroundTasks,
    optional_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> RepoRead:
    settings = get_settings()
    src = Path(payload.path).resolve()
    if not src.exists() or not src.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path does not exist or is not a directory: {payload.path}",
        )
    # Security: ensure path doesn't escape
    dest = settings.workspace_root / f"repo_{src.name}"
    repo = Repository(
        user_id=optional_user.id if optional_user else None,
        name=payload.name,
        source_type=SourceType.LOCAL,
        source_path=str(src),
        workspace_path=str(dest),
        status=RepoStatus.PENDING,
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)
    background_tasks.add_task(_start_indexing, repo.id)
    return RepoRead.model_validate(repo)


@router.post(
    "/import/zip",
    response_model=RepoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a repository from a ZIP upload",
)
async def import_zip(
    name: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    optional_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> RepoRead:
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip files are accepted",
        )
    settings = get_settings()
    safe_name = Path(file.filename).stem[:100]
    dest = settings.workspace_root / f"zip_{safe_name}"
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "upload.zip"

    # Write upload (Milestone 3 will add size + bomb limits)
    content = await file.read()
    zip_path.write_bytes(content)

    repo = Repository(
        user_id=optional_user.id if optional_user else None,
        name=name,
        source_type=SourceType.ZIP,
        source_path=str(zip_path),
        workspace_path=str(dest),
        status=RepoStatus.PENDING,
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)
    background_tasks.add_task(_start_indexing, repo.id)
    return RepoRead.model_validate(repo)


@router.post(
    "/import/git",
    response_model=RepoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a public Git repository",
)
async def import_git(
    payload: RepoImportGit,
    background_tasks: BackgroundTasks,
    optional_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> RepoRead:
    # URL validation — Milestone 3 adds full SSRF protection
    url = payload.url.strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only http:// and https:// Git URLs are supported",
        )
    repo = Repository(
        user_id=optional_user.id if optional_user else None,
        name=payload.name,
        source_type=SourceType.GIT,
        source_path=url,
        status=RepoStatus.PENDING,
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)
    background_tasks.add_task(_start_indexing, repo.id)
    return RepoRead.model_validate(repo)


@router.get("/{repo_id}", response_model=RepoRead, summary="Get a repository by ID")
async def get_repo(repo_id: int, db: AsyncSession = Depends(get_db)) -> RepoRead:
    repo = await _get_or_404(repo_id, db)
    return RepoRead.model_validate(repo)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, summary="Delete a repository")
async def delete_repo(repo_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    repo = await _get_or_404(repo_id, db)
    # Clean up workspace
    if repo.workspace_path:
        ws = Path(repo.workspace_path)
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)
    await db.delete(repo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_or_404(repo_id: int, db: AsyncSession) -> Repository:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repo
