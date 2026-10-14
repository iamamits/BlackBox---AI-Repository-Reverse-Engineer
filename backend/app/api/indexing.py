"""BlackBox — Indexing status API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import IndexedFile, Repository, RepoStatus
from app.core.schemas import IndexedFileRead, IndexingStatus
from app.db.session import get_db

router = APIRouter(prefix="/indexing", tags=["indexing"])


@router.get(
    "/{repo_id}/status",
    response_model=IndexingStatus,
    summary="Get indexing progress for a repository",
)
async def get_indexing_status(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
) -> IndexingStatus:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    files_result = await db.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repo_id)
    )
    files = files_result.scalars().all()

    return IndexingStatus(
        repository_id=repo_id,
        status=repo.status,
        progress=repo.index_progress,
        files_processed=len(files),
        files_total=repo.file_count,
        symbols_extracted=repo.symbol_count,
        current_file=None,
        error_message=repo.error_message,
    )


@router.get(
    "/{repo_id}/files",
    response_model=list[IndexedFileRead],
    summary="List indexed files for a repository",
)
async def list_indexed_files(
    repo_id: int,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[IndexedFileRead]:
    result = await db.execute(
        select(IndexedFile)
        .where(IndexedFile.repository_id == repo_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [IndexedFileRead.model_validate(f) for f in result.scalars().all()]


@router.post(
    "/{repo_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel an in-progress indexing job",
)
async def cancel_indexing(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    if repo.status == RepoStatus.INDEXING:
        repo.status = RepoStatus.ERROR
        repo.error_message = "Indexing cancelled by user"

    return {"message": "Cancellation requested", "repository_id": repo_id}
