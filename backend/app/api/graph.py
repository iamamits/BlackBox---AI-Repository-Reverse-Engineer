"""BlackBox — Architecture graph API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Dependency, IndexedFile, Repository, Symbol
from app.core.schemas import GraphEdge, GraphNode, GraphResponse
from app.db.session import get_db

router = APIRouter(prefix="/graph", tags=["graph"])

MAX_NODES = 500


@router.get(
    "/{repo_id}",
    response_model=GraphResponse,
    summary="Get the dependency graph for a repository",
)
async def get_graph(
    repo_id: int,
    max_nodes: int = Query(default=200, le=MAX_NODES),
    db: AsyncSession = Depends(get_db),
) -> GraphResponse:
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # Fetch files (nodes) with symbol counts
    stmt = (
        select(IndexedFile, func.count(Symbol.id).label("sym_count"))
        .outerjoin(Symbol, IndexedFile.id == Symbol.file_id)
        .where(IndexedFile.repository_id == repo_id)
        .group_by(IndexedFile.id)
        .limit(max_nodes)
    )
    result = await db.execute(stmt)
    rows = result.all()
    files = [r[0] for r in rows]
    file_ids = {f.id for f in files}

    nodes = [
        GraphNode(
            id=f"file:{f.id}",
            label=f.path.split("/")[-1],
            kind="file",
            language=f.language,
            path=f.path,
            line_start=1,
            symbol_count=sym_count,
        )
        for f, sym_count in rows
    ]

    # Fetch edges (dependencies between visible files)
    deps_result = await db.execute(
        select(Dependency).where(
            Dependency.repository_id == repo_id,
            Dependency.source_file_id.in_(file_ids),
            Dependency.target_file_id.in_(file_ids),
        )
    )
    deps = deps_result.scalars().all()

    edges = [
        GraphEdge(
            id=f"dep:{d.id}",
            source=f"file:{d.source_file_id}",
            target=f"file:{d.target_file_id}",
            dep_type=d.dep_type,
            confidence=d.confidence,
            evidence=d.evidence,
        )
        for d in deps
    ]

    total_files_result = await db.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repo_id)
    )
    total = len(total_files_result.scalars().all())

    return GraphResponse(
        repository_id=repo_id,
        nodes=nodes,
        edges=edges,
        truncated=total > max_nodes,
        node_count=len(nodes),
        edge_count=len(edges),
    )
