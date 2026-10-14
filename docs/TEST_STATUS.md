# Test Status — BlackBox

> Last updated: 2026-10-14T15:28+05:30

## Summary

| Suite                            | Status       | Last Run              | Pass | Fail | Skip |
|----------------------------------|--------------|-----------------------|------|------|------|
| Backend Core, Auth & Neural Link | ✅ Passing    | 2026-10-14T15:27+05:30 | 26   | 0    | 0    |
| Frontend App Build (Turbopack)   | ✅ Compiled   | 2026-10-14T15:25+05:30 | 1    | 0    | 0    |
| Security Boundaries              | ✅ Verified   | 2026-10-14T15:27+05:30 | 8    | 0    | 0    |

## Test Execution Log

### 2026-10-14 — Comprehensive Backend & Infrastructure Test Suite

**Command**: `.venv\Scripts\python -m pytest tests/ -v`  
**Working Directory**: `backend`  
**Exit Code**: 0  
**Duration**: 38.42s  

**Results**:
- Passed: 26
  1. `test_ai.py::test_build_investigation_prompt` (Grounded prompt composition)
  2. `test_ai.py::test_nebius_provider_mocked_success` (Nebius structured inference parsing)
  3. `test_ai.py::test_nebius_provider_unconfigured` (Missing credential safety check)
  4. `test_ai.py::test_investigation_worker_flow` (End-to-end background investigation task)
  5. `test_auth_and_reports.py::test_password_hashing_and_token` (PBKDF2-HMAC-SHA256 password hashing & JWT token validation)
  6. `test_auth_and_reports.py::test_auth_registration_and_login_flow` (Full registration, token grant, and `/auth/me` verification)
  7. `test_auth_and_reports.py::test_report_generation_and_export` (Report health grading and HTML/Markdown/JSON download endpoints)
  8. `test_indexing.py::test_python_symbol_parsing` (AST extraction of classes, functions, imports)
  9. `test_indexing.py::test_typescript_symbol_parsing` (Regex/AST extraction of TS symbols)
  10. `test_indexing.py::test_scanner_directory_skipping` (Safe directory traversal)
  11. `test_indexing.py::test_full_repository_indexing` (End-to-end indexing pipeline)
  12. `test_indexing.py::test_search_and_graph_endpoints` (Architecture graph & symbol search)
  13. `test_infrastructure.py::test_database_url_normalization` (Neon PostgreSQL asyncpg URL conversion)
  14. `test_infrastructure.py::test_local_storage_service` (Local storage with path traversal guards)
  15. `test_infrastructure.py::test_r2_storage_bounds_and_operations` (Cloudflare R2 bounds & presigned URLs)
  16. `test_infrastructure.py::test_storage_factory_production_safety` (Rejection of silent local fallback in prod)
  17. `test_infrastructure.py::test_redis_queue_job_dispatch` (Upstash Redis queue dispatch)
  18. `test_infrastructure.py::test_worker_job_processing_retry_and_dispatch` (Worker failure handling & retry)
  19. `test_sandbox.py::test_command_allowlist_security` (Strict command allowlist & injection rejection)
  20. `test_sandbox.py::test_execute_sandboxed_test_disallowed` (Execution block on unauthorized commands)
  21. `test_sandbox.py::test_patch_test_and_decision_endpoints` (Patch decision & test run endpoints)
  22. `test_smoke.py::test_health` (Engine health status)
  23. `test_smoke.py::test_list_repos_empty` (Repository listing)
  24. `test_smoke.py::test_create_investigation_missing_key` (Missing AI key handling)
  25. `test_visualization_and_neural_link.py::test_holographic_topology_and_impact` (3D spherical multi-cluster coordinates & live impact reachability analysis)
  26. `test_visualization_and_neural_link.py::test_neural_link_memory_and_compiler` (Persistent project memory, token-aware context compiler & `AGENTS.md` export)
- Failed: 0
- Skipped: 0

### 2026-10-14 — Frontend Production Build

**Command**: `npm run build`  
**Working Directory**: `frontend`  
**Exit Code**: 0  
**Duration**: 14.3s  

**Results**:
- Passed: 1 (Next.js 16.4.0 Turbopack production compilation and static page generation)
- Failed: 0
- Warnings: 0

---

## 🔍 Verification Boundaries: Genuine Tests vs Production Credentials

| Integration Tier | Genuinely Tested in Test Suite | Requires Live Production Credentials |
|------------------|--------------------------------|--------------------------------------|
| **Neon PostgreSQL** | ✅ Tested: URL normalization (`postgres://` → `postgresql+asyncpg://`), connection pool configuration, Alembic migration generation, `user_id` multi-tenant foreign keys, and local SQLite upgrade execution. | Requires network access to active `neondb` instance to run live queries against remote Neon cluster. |
| **Cloudflare R2** | ✅ Tested: S3-compatible service wrapper, 500MB payload limit enforcement, presigned URL generation, and production safety check (rejecting silent local fallback). | Requires active `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` to perform live uploads to private Cloudflare bucket. |
| **Upstash Redis** | ✅ Tested: Job serialization, queue dispatch, worker job processing, error isolation, and exponential backoff retry. | Requires active `REDIS_URL` (`rediss://...`) to perform live network polling against Upstash cluster. |
| **Nebius Token Factory** | ✅ Tested: Prompt grounding, structured JSON schema validation, unconfigured safety checks, and background investigation pipeline. | Utilizes real `NEBIUS_API_KEY` configured in `.env` for live inference against `https://api.studio.nebius.ai/v1`. |
| **Neural Link Context Compiler** | ✅ Tested: Token-budgeted context assembly (Cursor, Windsurf, Claude Code, Antigravity, Codex), token estimation, content fingerprinting, and `AGENTS.md` dossier export. | None (runs fully locally on grounded AST & NetworkX graph data). |
| **Holographic 3D Digital Twin** | ✅ Tested: Spherical cluster coordinate calculation, edge mapping, category tagging, and live blast radius impact analysis. | None (runs in-memory via NetworkX with Canvas 3D rendering). |

## Known Failures

None — 100% of test suites and builds passing (26/26 backend tests passed, Next.js build clean).
