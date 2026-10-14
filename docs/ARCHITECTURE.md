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

## 5. Security Architecture

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
| Cross-repo data leakage   | Scope all queries to the active repository ID                 |
| Secret exposure in UI     | API keys server-side only; never sent to browser              |

### Credential Handling

- All secrets in environment variables, never in source or docs.
- `.env.example` files contain placeholder keys, never real values.
- `.gitignore` excludes `.env`, `*.sqlite`, and workspace data.

## 6. Deployment (MVP)

For local development and demo:

```
docker-compose up       # Starts backend + frontend + SQLite
```

Or run separately:

```
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev    # port 3000
```

No Kubernetes, no microservices, no external databases required for MVP.

## 7. Cross-Cutting Concerns

- **Logging**: Structured JSON logging via Python `structlog`.
- **Error handling**: All API errors return `{ "error": { "code": ..., "message": ... } }`.
- **Health check**: `GET /api/health` returns backend status + AI provider status.
- **CORS**: Configured for local dev origins; restrictive in production.
- **Pagination**: Cursor-based for lists; configurable page size.
