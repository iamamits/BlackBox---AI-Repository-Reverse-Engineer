# Architectural Decisions — BlackBox

> Accepted decisions and their rationale. New decisions are appended; superseded decisions are marked.

---

## ADR-001: Modular Monolith Architecture

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: BlackBox is a hackathon MVP that must be built quickly, run locally, and demonstrate a complete vertical slice. Microservices add deployment complexity without proportional benefit at this stage.  
**Decision**: Use a modular monolith with clear module boundaries (API, Indexing, AI, Sandbox, Core). Modules communicate through service interfaces, not HTTP.  
**Consequences**: Simpler deployment and debugging. Modules can be extracted into services later if needed. Must enforce module boundaries through directory structure and import rules.

---

## ADR-002: Next.js Frontend + FastAPI Backend

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: The hackathon requires TypeScript frontend with React Flow and Monaco Editor, plus Python backend with Tree-sitter and NetworkX.  
**Decision**: Next.js App Router for frontend, FastAPI for backend, communicating over HTTP REST.  
**Consequences**: Two separate dev servers during development. Need CORS configuration. Clear separation of concerns. Both frameworks have strong typing support.

---

## ADR-003: SQLite for MVP, PostgreSQL Path Documented

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: MVP needs to run locally without infrastructure setup. Production would benefit from PostgreSQL.  
**Decision**: Use SQLite via SQLAlchemy for MVP. Use Alembic migrations from day one. Document the PostgreSQL switch as a `DATABASE_URL` change.  
**Consequences**: No external database dependency. FTS5 is SQLite-native, which simplifies search. Some SQLAlchemy patterns (e.g., array columns) need SQLite-compatible alternatives.

---

## ADR-004: Tree-sitter for Syntax-Aware Parsing

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: Accurate symbol extraction requires syntax-aware parsing, not regex. Tree-sitter provides incremental, error-tolerant parsing for many languages.  
**Decision**: Use Tree-sitter with language grammars for TypeScript/JavaScript, Python, and Java. Design a language adapter interface so additional languages can be added independently.  
**Consequences**: Dependency on Tree-sitter Python bindings and grammar packages. Parser errors are tracked, not fatal. Languages without grammars get file-level (not symbol-level) indexing.

---

## ADR-005: AI Provider Abstraction with Nebius Adapter

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: Hackathon requires Nebius Token Factory + NVIDIA open model. The app must also function (deterministic features) when AI is unavailable.  
**Decision**: Define an abstract `AIProvider` interface. Implement a `NebiusProvider` adapter. All application code depends on the interface.  
**Consequences**: Clean separation. Easy to add other providers later. Must handle graceful degradation when credentials are missing.

---

## ADR-006: Sandbox via Docker Containers

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: Test execution of untrusted repository code requires isolation. Docker provides disposable, resource-limited, network-isolated containers.  
**Decision**: Run tests in disposable Docker containers with no network, limited resources, and no access to host secrets. If Docker is unavailable, execution is disabled (static analysis only).  
**Consequences**: Docker must be installed for test execution features. The sandbox module must validate Docker availability and fail gracefully.

---

## ADR-007: Project Continuity System

**Status**: Accepted  
**Date**: 2026-10-14  
**Context**: Multiple coding agents (AI or human) may work on this project across sessions. Context is lost between sessions unless explicitly persisted.  
**Decision**: Maintain a set of canonical documentation files (`AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PROJECT_STATE.md`, `docs/HANDOFF.md`, `docs/TEST_STATUS.md`) that serve as the project's persistent memory. Every agent must read these before editing code and update them after milestones.  
**Consequences**: Small overhead per session for reading/updating docs. Greatly reduces context loss and redundant work. Documentation must be kept consistent with actual code state.

---

*Template for new decisions:*

```
## ADR-NNN: Title

**Status**: Proposed | Accepted | Superseded by ADR-XXX
**Date**: YYYY-MM-DD
**Context**: Why is this decision needed?
**Decision**: What was decided?
**Consequences**: What are the trade-offs?
```
