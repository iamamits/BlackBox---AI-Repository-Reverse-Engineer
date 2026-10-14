"""BlackBox — Holographic 3D & 2D Repository Visualization Pipeline."""
from __future__ import annotations

import math
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Dependency, IndexedFile, Repository, Symbol, SymbolKind
from app.db.session import get_db

router = APIRouter(prefix="/visualization", tags=["visualization"])


@router.get("/{repo_id}/topology", summary="Compute 3D holographic topology with hierarchical clustering")
async def get_holographic_topology(
    repo_id: int,
    max_nodes: int = Query(default=150, le=400),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # 1. Fetch Repository
    repo_res = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # 2. Fetch Indexed Files with symbol counts
    stmt = (
        select(IndexedFile, func.count(Symbol.id).label("sym_count"))
        .outerjoin(Symbol, IndexedFile.id == Symbol.file_id)
        .where(IndexedFile.repository_id == repo_id)
        .group_by(IndexedFile.id)
        .limit(max_nodes)
    )
    rows = (await db.execute(stmt)).all()
    files = [r[0] for r in rows]
    file_map = {f.id: f for f in files}
    file_ids = set(file_map.keys())

    # 3. Categorize into Package/Module Clusters
    clusters: dict[str, list[int]] = {}
    for f in files:
        parts = f.path.replace("\\", "/").split("/")
        package = parts[0] if len(parts) > 1 else "root"
        clusters.setdefault(package, []).append(f.id)

    # 4. Compute 3D Coordinates using Spherical Multi-Cluster Layout
    nodes_3d = []
    cluster_names = list(clusters.keys())
    num_clusters = max(1, len(cluster_names))

    for c_idx, (cluster_name, c_file_ids) in enumerate(clusters.items()):
        # Compute cluster center in 3D
        c_theta = (2 * math.pi * c_idx) / num_clusters
        c_radius = 240.0 if num_clusters > 1 else 0.0
        cx = c_radius * math.cos(c_theta)
        cy = (c_idx % 2 * 60.0) - 30.0
        cz = c_radius * math.sin(c_theta)

        # Distribute files around cluster center
        num_in_cluster = len(c_file_ids)
        for f_idx, fid in enumerate(c_file_ids):
            f = file_map[fid]
            f_sym_count = next((sym_count for fl, sym_count in rows if fl.id == fid), 0)

            # Golden ratio spiral around cluster center
            phi = math.acos(1 - 2 * (f_idx + 0.5) / max(1, num_in_cluster))
            theta = math.pi * (1 + 5**0.5) * f_idx
            r_local = 45.0 + min(60.0, num_in_cluster * 4.0)

            nx = cx + r_local * math.sin(phi) * math.cos(theta)
            ny = cy + r_local * math.sin(phi) * math.sin(theta)
            nz = cz + r_local * math.cos(phi)

            # Node category heuristic
            path_lower = f.path.lower()
            if "route" in path_lower or "api" in path_lower or "endpoint" in path_lower:
                category = "api_route"
            elif "model" in path_lower or "schema" in path_lower or "entity" in path_lower:
                category = "data_model"
            elif "worker" in path_lower or "job" in path_lower or "queue" in path_lower:
                category = "worker"
            elif "test" in path_lower:
                category = "test"
            else:
                category = "core_logic"

            nodes_3d.append({
                "id": f"file:{f.id}",
                "file_id": f.id,
                "label": f.path.split("/")[-1],
                "path": f.path,
                "language": f.language or "Unknown",
                "category": category,
                "cluster": cluster_name,
                "symbol_count": f_sym_count,
                "size_bytes": f.size_bytes,
                "lines": f.line_count,
                "position": {"x": round(nx, 2), "y": round(ny, 2), "z": round(nz, 2)},
            })

    # 5. Fetch Dependencies & Directional Edges
    deps_res = await db.execute(
        select(Dependency).where(
            Dependency.repository_id == repo_id,
            Dependency.source_file_id.in_(file_ids),
            Dependency.target_file_id.in_(file_ids),
        )
    )
    deps = deps_res.scalars().all()

    edges = [
        {
            "id": f"dep:{d.id}",
            "source": f"file:{d.source_file_id}",
            "target": f"file:{d.target_file_id}",
            "type": d.dep_type.value,
            "confidence": d.confidence.value,
            "evidence": d.evidence,
        }
        for d in deps
    ]

    return {
        "repository_id": repo.id,
        "repository_name": repo.name,
        "primary_language": repo.primary_language,
        "clusters": [{"name": k, "count": len(v)} for k, v in clusters.items()],
        "node_count": len(nodes_3d),
        "edge_count": len(edges),
        "nodes": nodes_3d,
        "edges": edges,
    }


@router.get("/{repo_id}/impact", summary="Compute change impact reachability for a file")
async def get_change_impact(
    repo_id: int,
    file_path: str = Query(..., description="Target file path to analyze impact"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    file_res = await db.execute(
        select(IndexedFile).where(IndexedFile.repository_id == repo_id, IndexedFile.path == file_path)
    )
    target_file = file_res.scalar_one_or_none()
    if not target_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {file_path}")

    # Fetch upstream callers (files that import or call target)
    upstream_res = await db.execute(
        select(IndexedFile)
        .join(Dependency, Dependency.source_file_id == IndexedFile.id)
        .where(Dependency.target_file_id == target_file.id)
    )
    upstream_files = upstream_res.scalars().all()

    # Fetch downstream dependencies (files that target imports or calls)
    downstream_res = await db.execute(
        select(IndexedFile)
        .join(Dependency, Dependency.target_file_id == IndexedFile.id)
        .where(Dependency.source_file_id == target_file.id)
    )
    downstream_files = downstream_res.scalars().all()

    risk_level = "low"
    if len(upstream_files) >= 5:
        risk_level = "critical"
    elif len(upstream_files) >= 2:
        risk_level = "high"
    elif len(upstream_files) >= 1:
        risk_level = "medium"

    return {
        "repository_id": repo_id,
        "target_file": target_file.path,
        "risk_level": risk_level,
        "impact_score": round(min(100, (len(upstream_files) * 18 + len(downstream_files) * 5)), 1),
        "upstream_dependents_count": len(upstream_files),
        "downstream_dependencies_count": len(downstream_files),
        "upstream_dependents": [{"id": f.id, "path": f.path, "language": f.language} for f in upstream_files],
        "downstream_dependencies": [{"id": f.id, "path": f.path, "language": f.language} for f in downstream_files],
        "recommended_test_files": [f.path for f in upstream_files if "test" in f.path.lower()],
    }
