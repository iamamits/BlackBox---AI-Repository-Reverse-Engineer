# AGENTS.md — BlackBox Project Instructions

> **Every coding agent must read this file first, then the files it references, before editing any source code.**

## 1. Mandatory Pre-Work

Before writing or modifying any code, read **all** of the following in order:

1. [`docs/HANDOFF.md`](docs/HANDOFF.md) — the previous agent's handoff: next task, context, blockers.
2. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — current implementation status and milestones.
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module boundaries, tech stack, data flow.
4. [`docs/DECISIONS.md`](docs/DECISIONS.md) — accepted architectural decisions and rationale.
5. [`docs/PRD.md`](docs/PRD.md) — product requirements and acceptance criteria.
6. [`docs/TEST_STATUS.md`](docs/TEST_STATUS.md) — last test run results, known failures.

If any of these files are missing or stale, update them before proceeding.

## 2. Project Identity

- **Product**: BlackBox — AI Repository Reverse Engineering & Autonomous Debugging Platform
- **Architecture**: Modular monolith (Next.js frontend + FastAPI backend)
- **Competition**: Nebius / NVIDIA hackathon entry
- **Repository**: This repo is the single source of truth.

## 3. Technology Stack

### Frontend
- Next.js (App Router), TypeScript (strict), Tailwind CSS, shadcn/ui
- React Flow (architecture graphs), Monaco Editor (code/diff inspection)
- Vitest (unit), Playwright (E2E)

### Backend
- Python 3.13, FastAPI, Pydantic, SQLAlchemy + Alembic
- SQLite (dev) → PostgreSQL (prod path)
- Tree-sitter (parsing), ripgrep + SQLite FTS5 (search)
- NetworkX (dependency/impact graphs)
- pytest

### AI / Inference
- Provider abstraction with Nebius Token Factory adapter
- NVIDIA open models via Nebius
- Structured Pydantic response schemas
- Configurable via `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEBIUS_MODEL`

## 4. Environment Variables

These are required at runtime (never commit actual values):

| Variable               | Purpose                                  |
|------------------------|------------------------------------------|
| `NEBIUS_API_KEY`       | Nebius inference API key                 |
| `NEBIUS_BASE_URL`      | Nebius API endpoint                      |
| `NEBIUS_MODEL`         | Model identifier (NVIDIA open model)     |
| `DATABASE_URL`         | SQLAlchemy connection string             |
| `BLACKBOX_WORKSPACE_ROOT` | Root directory for imported repos     |

Optional:
| Variable      | Purpose                          |
|---------------|----------------------------------|
| `REDIS_URL`   | Only if async job queue is added |

## 5. Coding Conventions

- **Python**: PEP 8, type hints on all public APIs, docstrings for modules and public functions.
- **TypeScript**: `strict: true`, explicit return types on exported functions, no `any` unless justified.
- **SQL**: Use Alembic migrations. Never modify the database schema outside a migration.
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Never commit secrets.
- **Imports**: Absolute imports; no circular dependencies across module boundaries.
- **Error handling**: Return structured error responses; no bare `except` or swallowed errors.

## 6. Security Rules

1. Never write secret values (API keys, tokens, passwords) into source files, docs, or Git history.
2. Treat all repository contents ingested by BlackBox as **untrusted data**.
3. Never execute imported repository code during indexing or analysis unless in an approved sandbox.
4. Validate and restrict Git URL schemes. Block private-network and metadata endpoints (SSRF).
5. Prevent path traversal and ZIP bombs during archive extraction.
6. Do not expose backend API keys to the browser.
7. Use explicit command allowlists; never interpolate untrusted strings into shell commands.
8. AI-generated tool arguments and shell commands are untrusted — validate before execution.

## 7. Workflow Rules

1. **Preserve existing work**: Do not overwrite `.env` files, databases, Docker volumes, or uncommitted changes without explicit approval.
2. **No destructive commands**: Never run `git reset --hard`, `docker system prune`, `DROP DATABASE`, or equivalent without explicit user approval.
3. **Incremental commits**: Commit after each coherent unit of work. Each commit should leave the project in a runnable (or at minimum, non-broken) state.
4. **Test before claiming done**: Run the relevant test suite. Record actual commands and results in `docs/TEST_STATUS.md`.
5. **Update docs after milestones**: After completing a milestone, update `PROJECT_STATE.md`, `TEST_STATUS.md`, and `HANDOFF.md`.
6. **Handoff on exit**: Before ending any session, update `docs/HANDOFF.md` with:
   - Exact next task
   - Relevant files and modules
   - Unresolved decisions
   - Outstanding test failures
   - Verification status

## 8. Module Boundaries

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full architecture diagram.

High-level boundaries:

```
frontend/          — Next.js application (pages, components, API client)
backend/
  api/             — FastAPI routers and request/response schemas
  core/            — Domain logic, services, models
  indexing/        — Repository parsing, symbol extraction, graph building
  ai/              — Provider abstraction, Nebius adapter, prompt templates
  sandbox/         — Isolated test execution environment
  db/              — SQLAlchemy models, Alembic migrations
docs/              — Project documentation (this continuity system)
tests/             — Test fixtures, sample repos, integration tests
```

## 9. Acceptance Criteria (Summary)

A developer must be able to:
1. Start the app from documented instructions.
2. Import a repository (local folder, ZIP, or public Git URL).
3. See real indexing progress and extracted symbols.
4. Search for a function and navigate to its source.
5. Inspect a dependency graph based on parsed relationships.
6. Ask a question and receive a repository-grounded AI answer (via Nebius/NVIDIA).
7. Review a proposed code patch with unified diff.
8. Execute tests in an isolated sandbox (or see why execution is disabled).
9. Inspect genuine logs and test outcomes.
10. Reproduce the demo using documented setup.

See [`docs/PRD.md`](docs/PRD.md) for full requirements.

## 10. Getting Started

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # fill in your credentials
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env.local  # fill in your credentials
npm run dev
```

See [`docs/HANDOFF.md`](docs/HANDOFF.md) for the current implementation state and next steps.
