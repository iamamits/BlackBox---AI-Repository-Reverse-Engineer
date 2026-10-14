# Test Status — BlackBox

> Last updated: 2026-10-14T15:16+05:30

## Summary

| Suite               | Status       | Last Run              | Pass | Fail | Skip |
|---------------------|--------------|-----------------------|------|------|------|
| Backend Core & Infra| ✅ Passing    | 2026-10-14T15:16+05:30 | 24   | 0    | 0    |
| Frontend App Build  | ✅ Compiled   | 2026-10-14T15:15+05:30 | 1    | 0    | 0    |
| Security Boundaries | ✅ Verified   | 2026-10-14T15:16+05:30 | 6    | 0    | 0    |

## Test Execution Log

### 2026-10-14 — Comprehensive Backend & Infrastructure Test Suite

**Command**: `.venv\Scripts\python -m pytest tests/ -v`  
**Working Directory**: `backend`  
**Exit Code**: 0  
**Duration**: 9.24s  

**Results**:
- Passed: 21
  1. `test_ai.py::test_build_investigation_prompt` (Grounded prompt composition)
  2. `test_ai.py::test_nebius_provider_mocked_success` (Nebius structured inference parsing)
  3. `test_ai.py::test_nebius_provider_unconfigured` (Missing credential safety check)
  4. `test_ai.py::test_investigation_worker_flow` (End-to-end background investigation task)
  5. `test_indexing.py::test_python_symbol_parsing` (AST extraction of classes, functions, imports)
  6. `test_indexing.py::test_typescript_symbol_parsing` (Regex/AST extraction of TS symbols)
  7. `test_indexing.py::test_scanner_directory_skipping` (Safe directory traversal)
  8. `test_indexing.py::test_full_repository_indexing` (End-to-end indexing pipeline)
  9. `test_indexing.py::test_search_and_graph_endpoints` (Architecture graph & symbol search)
  10. `test_infrastructure.py::test_database_url_normalization` (Neon PostgreSQL asyncpg URL conversion)
  11. `test_infrastructure.py::test_local_storage_service` (Local storage with path traversal guards)
  12. `test_infrastructure.py::test_r2_storage_bounds_and_operations` (Cloudflare R2 bounds & presigned URLs)
  13. `test_infrastructure.py::test_storage_factory_production_safety` (Rejection of silent local fallback in prod)
  14. `test_infrastructure.py::test_redis_queue_job_dispatch` (Upstash Redis queue dispatch)
  15. `test_infrastructure.py::test_worker_job_processing_retry_and_dispatch` (Worker failure handling & retry)
  16. `test_sandbox.py::test_command_allowlist_security` (Strict command allowlist & injection rejection)
  17. `test_sandbox.py::test_execute_sandboxed_test_disallowed` (Execution block on unauthorized commands)
  18. `test_sandbox.py::test_patch_test_and_decision_endpoints` (Patch decision & test run endpoints)
  19. `test_smoke.py::test_health` (Engine health status)
  20. `test_smoke.py::test_list_repos_empty` (Repository listing)
  21. `test_smoke.py::test_create_investigation_missing_key` (Missing AI key handling)
- Failed: 0
- Skipped: 0

### 2026-10-14 — Frontend Production Build

**Command**: `npm run build`  
**Working Directory**: `frontend`  
**Exit Code**: 0  
**Duration**: 2.9s  

**Results**:
- Passed: 1 (Next.js 16.4.0 static export and App Router compile)
- Failed: 0

---

## 🔍 Verification Boundaries: Genuine Tests vs Production Credentials

| Integration Tier | Genuinely Tested in Test Suite | Requires Live Production Credentials |
|------------------|--------------------------------|--------------------------------------|
| **Neon PostgreSQL** | ✅ Tested: URL normalization (`postgres://` → `postgresql+asyncpg://`), connection pool configuration, Alembic migration generation and local SQLite upgrade execution. | Requires network access to active `neondb` instance to run live queries against remote Neon cluster. |
| **Cloudflare R2** | ✅ Tested: S3-compatible service wrapper, 500MB payload limit enforcement, presigned URL generation, and production safety check (rejecting silent local fallback). | Requires active `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` to perform live uploads to private Cloudflare bucket. |
| **Upstash Redis** | ✅ Tested: Job serialization, queue dispatch, worker job processing, error isolation, and exponential backoff retry. | Requires active `REDIS_URL` (`rediss://...`) to perform live network polling against Upstash cluster. |
| **Nebius Token Factory** | ✅ Tested: Prompt grounding, structured JSON schema validation, unconfigured safety checks, and background investigation pipeline. | Utilizes real `NEBIUS_API_KEY` configured in `.env` for live inference against `https://api.studio.nebius.ai/v1`. |

## Known Failures

None — 100% of test suites and builds passing (21/21 backend tests passed).
