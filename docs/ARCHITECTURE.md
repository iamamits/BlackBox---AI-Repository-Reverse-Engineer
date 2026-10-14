# Architecture — BlackBox

> Modular monolith: Next.js frontend + FastAPI backend

## 1. High-Level Overview

```
┌──────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
│  Next.js App Router · TypeScript · Tailwind · shadcn/ui  │
│  React Flow (graphs) · Monaco Editor (code/diff)         │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  ┌────────┐ ┌──────────┐ ┌──────┐ ┌─────────┐ ┌───────┐ │
│  │  API   │ │ Indexing  │ │  AI  │ │ Sandbox │ │Search │ │
│  │Routers │ │ Pipeline  │ │Layer │ │  Exec   │ │Engine │ │
│  └───┬────┘ └────┬─────┘ └──┬───┘ └────┬────┘ └───┬───┘ │
│      │           │          │           │          │      │
│  ┌───▼───────────▼──────────▼───────────▼──────────▼───┐ │
│  │              Core Domain Layer                      │ │
│  │  Models · Services · Schemas · Graph (NetworkX)     │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼──────────────────────────────┐ │
│  │           Data Layer (SQLAlchemy + Alembic)          │ │
│  │           SQLite (dev) → PostgreSQL (prod)           │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## 2. Directory Structure

```
blackbox/
├── AGENTS.md                   # Agent instructions (this continuity system)
├── docs/
│   ├── PRD.md                  # Product requirements
│   ├── ARCHITECTURE.md         # This file
│   ├── DECISIONS.md            # Architectural decisions log
│   ├── PROJECT_STATE.md        # Implementation status
│   ├── HANDOFF.md              # Agent handoff instructions
│   └── TEST_STATUS.md          # Test execution evidence
│
├── frontend/                   # Next.js application
│   ├── app/                    # App Router pages and layouts
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── graph/              # React Flow graph components
│   │   ├── editor/             # Monaco Editor wrappers
│   │   └── investigation/      # AI investigation UI
│   ├── lib/                    # Client utilities, API client, types
│   ├── public/                 # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── .env.example
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── api/                # Routers
│   │   │   ├── repos.py        # Repository CRUD and import
│   │   │   ├── indexing.py     # Indexing status and control
│   │   │   ├── search.py       # Symbol and code search
│   │   │   ├── graph.py        # Architecture graph queries
│   │   │   ├── investigate.py  # AI investigation endpoints
│   │   │   ├── patches.py      # Patch proposal and review
│   │   │   ├── tests.py        # Test execution and logs
│   │   │   └── impact.py       # Change impact analysis
│   │   ├── core/               # Domain logic
│   │   │   ├── models.py       # SQLAlchemy ORM models
│   │   │   ├── schemas.py      # Pydantic request/response schemas
│   │   │   └── services/       # Business logic services
│   │   ├── indexing/           # Repository analysis pipeline
│   │   │   ├── pipeline.py     # Orchestrator
│   │   │   ├── discovery.py    # File discovery and filtering
│   │   │   ├── language.py     # Language detection
│   │   │   ├── parser.py       # Tree-sitter parsing
│   │   │   ├── symbols.py      # Symbol extraction
│   │   │   └── graph.py        # Dependency graph construction
│   │   ├── ai/                 # AI provider abstraction
│   │   │   ├── provider.py     # Abstract provider interface
│   │   │   ├── nebius.py       # Nebius Token Factory adapter
│   │   │   ├── schemas.py      # Structured response schemas
│   │   │   └── prompts.py      # Prompt templates
│   │   ├── sandbox/            # Isolated test execution
│   │   │   ├── executor.py     # Docker sandbox manager
│   │   │   └── policy.py       # Execution policy and limits
│   │   └── db/                 # Database layer
│   │       ├── session.py      # Session factory
│   │       └── migrations/     # Alembic migrations
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── .env.example
│
├── tests/                      # Cross-cutting test assets
│   ├── fixtures/               # Sample repos for testing
│   └── e2e/                    # Playwright E2E tests
│
├── docker-compose.yml          # Local dev stack
├── Dockerfile.backend
├── Dockerfile.frontend
├── .gitignore
└── .env.example                # Root-level env template
```

## 3. Module Boundaries

### Frontend → Backend API

All communication is over HTTP REST (JSON). WebSocket may be added for real-time indexing progress. The frontend never accesses the database or file system directly.

### API Routers → Core Services

Routers handle HTTP concerns (validation, serialization, status codes). Business logic lives in `core/services/`. Routers are thin.

### Indexing Pipeline

The indexing pipeline is a sequential, stage-based process:
1. **Discovery** → eligible files
2. **Language Detection** → language per file
3. **Parsing** → AST via Tree-sitter
4. **Symbol Extraction** → definitions, imports, calls
5. **Graph Construction** → dependency graph (NetworkX)
6. **Index Building** → FTS5 search index

Each stage is independently testable. The pipeline reports progress and handles errors per-file (no single-file failure crashes the pipeline).

### AI Layer

The AI layer has a **provider abstraction** (`AIProvider` interface) with a concrete **Nebius adapter**. The rest of the application calls the abstraction, never the adapter directly.

When AI credentials are absent, the application disables AI-dependent features gracefully and clearly communicates this to the user.

### Sandbox

Test execution happens **only** inside a disposable Docker container. The sandbox module enforces:
- No host filesystem access beyond the approved workspace copy
- No network access by default
- Resource limits (CPU, memory, time)
- Explicit user approval before execution

If Docker is unavailable, execution is disabled and the UI explains why.

## 4. Data Model (Key Entities)

```
Repository
  ├── id, name, source_type, source_path, status, created_at
  │
  ├── IndexedFile (1:N)
  │   ├── id, repo_id, path, language, size, hash, parse_status
  │   │
  │   └── Symbol (1:N)
  │       ├── id, file_id, name, kind, line_start, line_end, parent_id
  │       └── SymbolReference (1:N) — where this symbol is used
  │
  ├── Dependency (N:N via edges)
  │   ├── source_file_id, target_file_id, relationship_type, evidence
  │   └── confidence (verified | heuristic)
  │
  ├── Investigation (1:N)
  │   ├── id, repo_id, question, classification, status, created_at
  │   ├── findings, evidence_refs, confidence
  │   └── Patch (0:N)
  │       ├── id, investigation_id, diff, status, created_at
  │       └── TestRun (0:N)
  │           ├── id, patch_id, command, exit_code, stdout, stderr
  │           └── duration, sandbox_id, status
  │
  └── SearchIndex (FTS5 virtual table)
      └── file_id, content, symbols
```

## 5. Holographic Visualization & Neural Link Architecture

### Holographic Codebase Explorer Pipeline
```
Indexed AST & Symbol Graph (NetworkX)
  ├── 1. Category Classification (api_route, data_model, core_logic, worker, test)
  ├── 2. Multi-Cluster Spherical Projection (Golden-ratio Fibonacci sphere layout in 3D)
  ├── 3. Edge Evidence Mapping (import, calls, inherits with confidence weight)
  └── 4. Live Change Impact Reachability (Upstream blast radius & downstream dependency tracing)
```
- **Spatial Topology**: Nodes are placed into 3D orbital space based on architectural role clusters (`(x, y, z)` coordinates normalized between `-120` and `+120`).
- **Interactive Digital Twin**: Rendered via an optimized native HTML5 3D projection engine with camera orbit, pan, pitch/yaw, and zoom controls.
- **Blast Radius Analysis**: Traces both downstream dependencies (what breaks if this node changes) and upstream callers (what depends on this node) with risk scoring (`Low`, `Medium`, `High`, `Critical`).
- **2D Fallback**: Automatic detection and one-click toggle to a high-contrast 2D dependency layout for accessibility or reduced-motion environments.

### Neural Link: Persistent Project Context & Compiler
```
Repository Index + Architectural Summaries
  ├── 1. Content Fingerprinting (SHA-256 hash of repository state)
  ├── 2. Persistent Memory (PostgreSQL / R2 storage of architecture, decisions, test status)
  ├── 3. Token-Aware Context Compiler:
  │      ├── Input: User task / bug description + Token budget (2K to 64K tokens)
  │      ├── Target Agent: Cursor, Windsurf, Claude Code, Antigravity, Codex
  │      └── Output: Grounded system instructions + verified AST symbols + test instructions
  └── 4. Multi-Agent Export Center (One-click AGENTS.md, Markdown dossier, or structured JSON)
```
- **Context Freshness**: Invalidation occurs automatically when repository file hashes or commit fingerprints drift from indexed memory.
- **Strict Budget Packing**: Allocates 20% to identity & architecture, 40% to task-relevant symbols, 25% to file paths & decisions, and 15% to test/build instructions.

## 6. Authentication & Tenant Data Isolation

- **Password Hashing**: PBKDF2-HMAC-SHA256 with 100,000 iterations and a cryptographically secure 16-byte random salt.
- **Session Tokens**: URL-safe HMAC-SHA256 signed JWT tokens with 7-day expiration.
- **Data Isolation**: All `Repository` records link to `user_id`. Authenticated sessions can only query and mutate their own repositories. Unauthenticated visitors are supported gracefully in Guest Demo Mode.
- **Institutional Audit Reports**: Generates formal repository health ratings (0-100 scale, letter grades A+ to D), severity-ranked security vulnerability indicators, and exportable reports in HTML (print/PDF-ready), GitHub Markdown, and raw JSON.

## 7. Security Architecture

### Threat Model Summary

| Threat                    | Mitigation                                                    |
|---------------------------|---------------------------------------------------------------|
| Path traversal            | Canonicalize paths; reject outside repo root                  |
| ZIP bomb                  | Limit total extracted size and file count                     |
| SSRF via Git URL          | Allowlist schemes (http, https, git); block private ranges    |
| Symlink escape            | Never follow symlinks outside repo root                       |
| Secret ingestion          | Ignore common secret patterns; never index `.env`, key files  |
| Prompt injection          | Repo content is untrusted data; system prompt isolation       |
| Arbitrary code execution  | No repo code execution outside approved sandbox               |
| AI tool-call injection    | Validate all AI-generated arguments; allowlist commands       |
| Cross-tenant data leakage | Tenant isolation via `user_id` foreign key & session scoping |
| Secret exposure in UI     | API keys server-side only; never sent to browser              |

### Credential Handling

- All secrets in environment variables, never in source or docs.
- `.env.example` files contain placeholder keys, never real values.
- `.gitignore` excludes `.env`, `*.sqlite`, and workspace data.

## 8. Deployment & Cloud Infrastructure

BlackBox supports both a zero-dependency local development workflow and a resilient serverless cloud production deployment:

### Production Cloud Architecture
- **Neon PostgreSQL**: Serverless relational database configured via `DATABASE_URL` with SQLAlchemy `asyncpg`, connection pooling (`pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`), and Alembic migrations.
- **Cloudflare R2**: Private S3-compatible durable object storage configured via `R2_*` environment variables for repository archives and investigation reports. Enforces strict payload limits (max 500MB) and rejects silent local fallbacks in production.
- **Upstash Redis**: Serverless Redis task queue configured via `REDIS_URL` (`rediss://...` with TLS) powering a separately deployable worker process (`python -m app.worker`) with bounded retries and exponential backoff.
- **Nebius Token Factory**: GPU inference endpoint hosting NVIDIA open models (`meta-llama/Meta-Llama-3.1-70B-Instruct`) with structured JSON schema validation.

### Deployment Options

```bash
# 1. Multi-Service Container Setup (API + Worker + Web UI)
docker compose up --build

# 2. Local Modular Monolith (FastAPI + Next.js)
cd backend && uvicorn app.main:app --reload --port 8000
cd backend && python -m app.worker  # Optional if Upstash Redis is active
cd frontend && npm run dev          # Next.js UI on port 3000
```

## 9. Cross-Cutting Concerns

- **Logging**: Structured JSON logging via Python `structlog` with ISO timestamps.
- **Smart Error Diagnostics**: Client-side `ErrorDiagnosticBanner` provides explicit error codes, root cause categorization, actionable troubleshooting tips, expandable raw HTTP details, and direct retry triggers.
- **Health & Readiness**: `GET /api/health` returns status of Neon PostgreSQL, Cloudflare R2, Upstash Redis, Nebius AI, and Docker Sandbox. `GET /api/ready` validates live database connectivity.
- **CORS**: Configured with strict origins (`ALLOWED_ORIGINS`).
- **Security Boundaries**: Shell metacharacter prevention, credential sanitization in sandbox runs, and path traversal guards.

