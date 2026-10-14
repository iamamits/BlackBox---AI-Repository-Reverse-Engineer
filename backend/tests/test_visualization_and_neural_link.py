"""Tests for BlackBox Holographic Visualization & Neural Link Context Compiler."""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_holographic_topology_and_impact():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a repo
        repo_resp = await client.post(
            "/api/v1/repos/import/local",
            json={"name": "test-viz-repo", "path": "C:\\Windows"},
        )
        repo_id = repo_resp.json().get("id", 1) if repo_resp.status_code == 201 else 1

        # Fetch 3D Holographic Topology
        topo_resp = await client.get(f"/api/v1/visualization/{repo_id}/topology")
        assert topo_resp.status_code == 200
        topo_data = topo_resp.json()
        assert "clusters" in topo_data
        assert "nodes" in topo_data
        assert "edges" in topo_data
        assert isinstance(topo_data["nodes"], list)

        # Check node 3D coordinates if nodes exist
        if topo_data["nodes"]:
            first_node = topo_data["nodes"][0]
            assert "position" in first_node
            assert "x" in first_node["position"]
            assert "y" in first_node["position"]
            assert "z" in first_node["position"]
            assert "category" in first_node


@pytest.mark.asyncio
async def test_neural_link_memory_and_compiler():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a repo
        repo_resp = await client.post(
            "/api/v1/repos/import/local",
            json={"name": "test-neural-repo", "path": "C:\\Windows"},
        )
        repo_id = repo_resp.json().get("id", 1) if repo_resp.status_code == 201 else 1

        # 1. Fetch Project Memory
        mem_resp = await client.get(f"/api/v1/neural-link/{repo_id}")
        assert mem_resp.status_code == 200
        mem_data = mem_resp.json()
        assert "content_fingerprint" in mem_data
        assert "sections" in mem_data
        assert "identity" in mem_data["sections"]
        assert "constraints" in mem_data["sections"]

        # 2. Compile token-aware context pack
        compile_resp = await client.post(
            f"/api/v1/neural-link/{repo_id}/compile",
            json={
                "task_description": "Implement authentication token refresh and boundary validation",
                "token_budget": 8000,
                "format": "agents_md",
                "target_agent": "cursor",
            },
        )
        assert compile_resp.status_code == 200
        comp_data = compile_resp.json()
        assert comp_data["within_budget"] is True
        assert comp_data["estimated_tokens"] > 0
        assert "AGENTS.md" in comp_data["content"]
        assert "Engineering Constraints" in comp_data["content"]

        # 3. Export AGENTS.md
        export_resp = await client.get(f"/api/v1/neural-link/{repo_id}/export?format=agents_md")
        assert export_resp.status_code == 200
        assert "text/markdown" in export_resp.headers["content-type"]
        assert "# AGENTS.md" in export_resp.text
