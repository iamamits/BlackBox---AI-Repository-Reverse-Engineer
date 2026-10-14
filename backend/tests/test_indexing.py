"""BlackBox — Indexing Pipeline Tests."""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from sqlalchemy import select

from app.core.models import Repository, RepoStatus, SourceType, Symbol
from app.db.session import AsyncSessionLocal
from app.indexing.parser import parse_python_file, parse_typescript_file
from app.indexing.scanner import scan_directory
from app.indexing.service import index_repository


def test_python_symbol_parsing():
    code = '''"""Sample module."""
import os
from pathlib import Path

class UserService:
    """Handles user operations."""
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int):
        return {"id": user_id}

def helper_func():
    return 42
'''
    result = parse_python_file(code, "sample.py")
    assert result.parse_status == "ok"
    names = [s.name for s in result.symbols]
    assert "UserService" in names
    assert "__init__" in names
    assert "get_user" in names
    assert "helper_func" in names
    dep_targets = [d.target_name for d in result.dependencies]
    assert "os" in dep_targets
    assert "pathlib" in dep_targets


def test_typescript_symbol_parsing():
    code = '''import React from 'react';
import { Button } from './ui';

export function Header() {
    return <header>BlackBox</header>;
}

export const fetchMetrics = async () => {
    return [];
};

class DashboardController {
    render() {}
}
'''
    result = parse_typescript_file(code, "component.tsx")
    assert result.parse_status == "ok"
    names = [s.name for s in result.symbols]
    assert "Header" in names
    assert "fetchMetrics" in names
    assert "DashboardController" in names
    targets = [d.target_name for d in result.dependencies]
    assert "react" in targets
    assert "./ui" in targets


def test_scanner_directory_skipping():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Normal file
        (root / "app.py").write_text("print('hello')", encoding="utf-8")

        # Ignored directory
        git_dir = root / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("dummy", encoding="utf-8")

        nm_dir = root / "node_modules" / "pkg"
        nm_dir.mkdir(parents=True)
        (nm_dir / "index.js").write_text("module.exports = {}", encoding="utf-8")

        scanned = scan_directory(root)
        paths = [f.path for f in scanned]

        assert "app.py" in paths
        assert not any(p.startswith(".git") for p in paths)
        assert not any(p.startswith("node_modules") for p in paths)


@pytest.mark.asyncio
async def test_full_repository_indexing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "calculator.py").write_text(
            '''def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

class MathEngine:
    def multiply(self, x, y):
        return x * y
''',
            encoding="utf-8",
        )

        async with AsyncSessionLocal() as db:
            repo = Repository(
                name="test-math-repo",
                source_type=SourceType.LOCAL,
                source_path=str(root),
                workspace_path=str(root),
                status=RepoStatus.PENDING,
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            repo_id = repo.id

        await index_repository(repo_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            indexed_repo = result.scalar_one()

            assert indexed_repo.status == RepoStatus.READY
            assert indexed_repo.file_count == 1
            assert indexed_repo.symbol_count >= 2
            assert indexed_repo.primary_language == "python"
            assert indexed_repo.index_progress == 1.0

            sym_result = await db.execute(select(Symbol).where(Symbol.repository_id == repo_id))
            symbols = sym_result.scalars().all()
            sym_names = [s.name for s in symbols]
            assert "add" in sym_names
            assert "MathEngine" in sym_names


@pytest.mark.asyncio
async def test_search_and_graph_endpoints():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "module_a.py").write_text("import module_b\ndef process_data(): return 100", encoding="utf-8")
        (root / "module_b.py").write_text("def fetch_data(): return 200", encoding="utf-8")

        async with AsyncSessionLocal() as db:
            repo = Repository(
                name="test-graph-repo",
                source_type=SourceType.LOCAL,
                source_path=str(root),
                workspace_path=str(root),
                status=RepoStatus.PENDING,
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            repo_id = repo.id

        await index_repository(repo_id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test Graph Endpoint
            g_resp = await client.get(f"/api/v1/graph/{repo_id}")
            assert g_resp.status_code == 200
            g_data = g_resp.json()
            assert g_data["node_count"] == 2
            assert any(n["symbol_count"] >= 1 for n in g_data["nodes"])

            # Test Search Endpoint
            s_resp = await client.post(
                "/api/v1/search/",
                json={"repository_id": repo_id, "q": "process_data"},
            )
            assert s_resp.status_code == 200
            s_data = s_resp.json()
            assert s_data["total"] >= 1
            assert s_data["hits"][0]["symbol_name"] == "process_data"
