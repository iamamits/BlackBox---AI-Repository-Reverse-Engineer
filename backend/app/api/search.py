"""BlackBox — Search API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import IndexedFile, Repository, Symbol
from app.core.schemas import SearchQuery, SearchResponse, SearchHit, SymbolKind
from app.db.session import get_db

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse, summary="Search symbols and code")
async def search(
    query: SearchQuery,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Full-text search across indexed symbols and source files.

    Milestone 3 will replace this with a real FTS5 index.
    Currently performs SQL LIKE-based search as a placeholder.
    """
    # Verify repo exists
    repo_result = await db.execute(
        select(Repository).where(Repository.id == query.repository_id)
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # Symbol search
    stmt = (
        select(Symbol, IndexedFile)
        .join(IndexedFile, Symbol.file_id == IndexedFile.id)
        .where(Symbol.repository_id == query.repository_id)
        .where(Symbol.name.ilike(f"%{query.q}%"))
    )
    if query.kinds:
        stmt = stmt.where(Symbol.kind.in_(query.kinds))

    result = await db.execute(stmt.limit(query.page_size).offset((query.page - 1) * query.page_size))
    rows = result.all()

    hits = [
        SearchHit(
            symbol_id=sym.id,
            file_id=f.id,
            file_path=f.path,
            symbol_name=sym.name,
            symbol_kind=sym.kind,
            line_start=sym.line_start,
            line_end=sym.line_end,
            snippet=sym.signature or sym.name,
            language=f.language,
            score=1.0,
        )
        for sym, f in rows
    ]

    return SearchResponse(
        query=query.q,
        repository_id=query.repository_id,
        total=len(hits),
        hits=hits,
    )
