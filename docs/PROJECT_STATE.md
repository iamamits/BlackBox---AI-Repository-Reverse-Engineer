# Project State — BlackBox

> Last updated: 2026-10-14T13:52+05:30

## Current Phase

**Milestone 6 — Integration Tests, End-to-End Hardening, Docker & Demo Setup** ✅ Complete

## Milestone Tracker

| #  | Milestone                                              | Status         |
|----|--------------------------------------------------------|----------------|
| 0  | Project continuity system and documentation            | ✅ Complete     |
| 1  | Workspace inspection, PRD, threat model, architecture  | ✅ Complete     |
| 2  | App skeleton, config, database, API contracts, UI shell| ✅ Complete     |
| 3  | Repo ingestion, indexing, parsing, search, dep graph   | ✅ Complete     |
| 4  | AI investigation + Nebius/NVIDIA inference             | ✅ Complete     |
| 5  | Patch proposal, diff review, sandbox, impact analysis  | ✅ Complete     |
| 6  | Integration tests, security, responsive UI, Docker, demo| ✅ Complete     |
| 7  | Cloud infrastructure adaptation (Neon, R2, Upstash)    | ✅ Complete     |
| 8  | Auth, Data Isolation, 3D Landing Page & Report Engine   | ✅ Complete     |

## Completed Work

### Milestone 0 & 1 — Continuity & Architecture
- [x] Canonical documentation suite: `AGENTS.md`, `PRD.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `PROJECT_STATE.md`, `HANDOFF.md`, `TEST_STATUS.md`.
- [x] Security & threat modeling: untrusted repo ingestion, SSRF protection, command allowlists.

### Milestone 2 — App Skeleton & Core Foundations
- [x] **Backend**: FastAPI 0.115.6 with Python 3.14 compatibility layer (`greenlet==3.5.6`, `sqlalchemy==2.0.36` typing patches).
- [x] **Database**: SQLAlchemy async ORM with complete domain schema (`Repository`, `IndexedFile`, `Symbol`, `Dependency`, `Investigation`, `Patch`, `TestRun`).
- [x] **API Endpoints**: Full routing structure (`/api/health`, `/api/ready`, `/repos`, `/indexing`, `/search`, `/graph`, `/investigate`, `/patches`).
- [x] **Frontend**: Next.js 16 (App Router, Turbopack), TypeScript `strict: true`, Tailwind CSS v4, Lucide React icons.
- [x] **Interactive UI Shell**: Architecture Graph, Symbol Explorer, AI Investigation studio, and Patch Review & Sandbox views.

### Milestone 3 — Ingestion & Parsing Engine
- [x] **Safe Directory Scanner** (`app/indexing/scanner.py`): recursive discovery with automatic exclusion of `.git`, `node_modules`, `.venv`, and binary files.
- [x] **Multi-Language AST & Symbol Parser** (`app/indexing/parser.py`): Python AST + TypeScript/JavaScript symbol & import extraction with line spans, docstrings, and signatures.
- [x] **Background Indexing Worker** (`app/indexing/service.py`): orchestrates file scanning, symbol storage, progress updates, and inter-file dependency resolution.
- [x] **Architecture Graph & Search API**: dynamic symbol counts and symbol search endpoints verified.

### Milestone 4 — AI Investigation & Nebius / NVIDIA Open Models
- [x] **Nebius Adapter** (`app/ai/provider.py`): HTTP client calling Nebius Token Factory with Bearer token authentication, concurrency limiter (`asyncio.Semaphore(5)`), and structured JSON parsing.
- [x] **Grounded Prompt Orchestration** (`app/ai/prompts.py`): system prompts and grounded context injection incorporating extracted symbols, files, and call edges.
- [x] **Structured Reasoning Schemas** (`app/ai/schemas.py`): Pydantic models for executive summaries, findings with severity, and unified diff proposals.
- [x] **Background Investigation Worker** (`app/api/investigate.py`): persists AI diagnosis and creates proposed patches in the database.

### Milestone 5 — Patch Proposal, Sandbox & Impact Analysis
- [x] **Sandbox Runner** (`app/sandbox/runner.py`): subprocess execution with strict command allowlists, credential stripping, and timeout enforcement.
- [x] **Patch Review API** (`app/api/patches.py`): accept/reject decisions and sandboxed test execution endpoints with `TestRun` records.
- [x] **Security Hardening**: blocks command injections, shell chaining (`;`, `&&`, `|`), and unauthorized external network calls.

### Milestone 6 — Integration Hardening, Docker & Demo Setup
- [x] **Containerization**: `backend/Dockerfile`, `backend/Dockerfile.worker`, and `frontend/Dockerfile` configured with multi-stage caching.
- [x] **Multi-Service Composition**: `docker-compose.yml` linking frontend (port 3000), backend (port 8000), and worker process with volume persistence.
- [x] **Sample Fixture**: `fixtures/sample_repo/` with calculator, inter-file service dependencies, and tests for instant demo verification.
- [x] **Complete Test Suite**: 21/21 backend unit and integration tests passing (`pytest tests/ -v`). Next.js production build passing with 0 errors.

### Milestone 7 — Cloud Infrastructure Adapters
- [x] **Neon PostgreSQL**: Connection pooling, timeouts, clean shutdown, asyncpg URL normalization, and Alembic migrations. SQLite local dev fallback.
- [x] **Cloudflare R2**: S3-compatible storage service with boto3, presigned URL generation, 500MB payload guard, and strict rejection of local fallback in production.
- [x] **Upstash Redis**: Serverless Redis task queue (`rediss://` TLS supported) with standalone worker process (`app/worker.py`), bounded retries, and exponential backoff.
- [x] **Nebius Token Factory**: Production-ready inference client with concurrency limits, bounded retries on 429/5xx, and structured Pydantic outputs.

## Active Blockers

None.

## Environment

- **OS**: Windows (PowerShell)
- **Git branch**: `main`
- **Python**: 3.14.7 (active in `backend/.venv`)
- **Node.js**: v20+ / Next.js 16.4.0 (active in `frontend`)

## Next Step

→ Platform is fully operational and verified across all requested infrastructure tiers. Ready for live demo, repo reverse engineering, and hackathon submission.
