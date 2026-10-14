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


def _get_safe_workspace_dest(subfolder: str) -> Path:
    settings = get_settings()
    try:
        dest = settings.workspace_root / subfolder
        dest.mkdir(parents=True, exist_ok=True)
        return dest
    except (PermissionError, OSError):
        import tempfile
        dest = Path(tempfile.gettempdir()) / "blackbox_workspace" / subfolder
        dest.mkdir(parents=True, exist_ok=True)
        return dest


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
    dest = _get_safe_workspace_dest(f"repo_{src.name}")
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
    dest = _get_safe_workspace_dest(f"zip_{safe_name}")
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
    from app.indexing.git_service import extract_repo_name, validate_git_url
    import uuid

    url = payload.url.strip()
    is_valid, err_msg = validate_git_url(url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )

    clean_name = payload.name.strip() if payload.name and payload.name.strip() else extract_repo_name(url)
    dest = _get_safe_workspace_dest(f"repo_git_{clean_name}_{uuid.uuid4().hex[:6]}")

    repo = Repository(
        user_id=optional_user.id if optional_user else None,
        name=clean_name,
        source_type=SourceType.GIT,
        source_path=url,
        workspace_path=str(dest),
        status=RepoStatus.PENDING,
    )
    try:
        db.add(repo)
        await db.flush()
        await db.refresh(repo)
    except Exception as e:
        await db.rollback()
        err_str = str(e)
        # Self-heal Postgres native enum if missing 'git'
        if "sourcetype" in err_str.lower() or "enum" in err_str.lower():
            try:
                from sqlalchemy import text
                await db.execute(text("ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS 'git'"))
                await db.commit()
                db.add(repo)
                await db.flush()
                await db.refresh(repo)
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database enum migration error: {str(retry_err)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during repository creation: {err_str}",
            )

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
