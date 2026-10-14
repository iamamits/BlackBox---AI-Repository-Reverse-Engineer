# Product Requirements Document — BlackBox

> AI Repository Reverse Engineering & Autonomous Debugging Platform

## 1. Product Vision

BlackBox is a developer tool that enables a user to import an unfamiliar codebase and ask questions about its architecture, trace bugs to root causes, receive evidence-grounded AI answers, and verify proposed fixes through isolated test execution.

It is **not** a generic chatbot, a static dashboard, or a superficial AI wrapper. Every answer must be grounded in actual repository evidence: file paths, line ranges, symbols, dependency relationships, test results, and explicit confidence levels.

## 2. Target User

An individual developer (or small team) who:
- Inherits, audits, or on-boards onto an unfamiliar codebase.
- Needs to understand internal architecture quickly.
- Wants AI assistance that cites real source evidence, not hallucinated code.
- Requires safe, isolated test execution for proposed patches.

## 3. Core Modules and Requirements

### A. Repository Import

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| RI-01 | Import from local folder via explicit picker                           | P0       |
| RI-02 | Import from ZIP upload with safe extraction                            | P0       |
| RI-03 | Import from public Git URL                                             | P0       |
| RI-04 | Show indexing status, progress, errors, and support cancellation       | P0       |
| RI-05 | Display repository metadata (languages, file counts, ignored paths)    | P1       |
| RI-06 | Ignore generated dirs, deps, build artifacts, binaries per config      | P0       |
| RI-07 | Prevent path traversal, ZIP bombs, oversized uploads, symlink escape   | P0       |
| RI-08 | Never execute repository code during import                            | P0       |

### B. Repository Intelligence Engine (Indexing)

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| IX-01 | Discover eligible source files                                         | P0       |
| IX-02 | Detect languages and frameworks                                        | P0       |
| IX-03 | Parse with Tree-sitter (TS/JS, Python, Java initially)                 | P0       |
| IX-04 | Extract symbols: definitions, imports, exports, calls, relationships   | P0       |
| IX-05 | Construct typed dependency graph (NetworkX)                            | P0       |
| IX-06 | Build searchable symbol and code index (SQLite FTS5)                   | P0       |
| IX-07 | Persist index metadata; support incremental re-indexing                | P1       |
| IX-08 | Track unsupported syntax and parser errors explicitly                  | P1       |
| IX-09 | Distinguish verified relationships from heuristic inferences           | P1       |

### C. Architecture Explorer

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| AE-01 | Interactive graph: files, modules, symbols, dependencies               | P0       |
| AE-02 | Search, filter, expand/collapse nodes                                  | P0       |
| AE-03 | Click node → inspect source (Monaco Editor)                            | P0       |
| AE-04 | Highlight inbound/outbound dependencies                                | P0       |
| AE-05 | Show relationship evidence and navigate to source locations             | P1       |
| AE-06 | Never invent graph edges                                               | P0       |

### D. Evidence-Grounded AI Investigator

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| AI-01 | Classify developer question                                            | P0       |
| AI-02 | Search indexed symbols and source                                      | P0       |
| AI-03 | Retrieve snippets with file paths and line ranges                      | P0       |
| AI-04 | Follow dependency relationships                                        | P1       |
| AI-05 | Use configured NVIDIA model via Nebius                                  | P0       |
| AI-06 | Structured answer: summary, findings, evidence, confidence, next steps | P0       |
| AI-07 | Cite retrieved evidence; admit insufficiency rather than fabricate      | P0       |
| AI-08 | Treat repo contents as untrusted; never let them override system rules | P0       |
| AI-09 | Deterministic (non-LLM) analysis when AI credentials absent            | P1       |

### E. Bug Investigation & Patch Proposals

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| BP-01 | Accept bug description + optional logs/repro scenario                  | P0       |
| BP-02 | Identify relevant files and symbols                                    | P0       |
| BP-03 | Rank root-cause hypotheses by evidence                                 | P0       |
| BP-04 | Generate minimal proposed patch as unified diff                        | P0       |
| BP-05 | User accept/reject workflow                                            | P0       |
| BP-06 | Record patch and verification status                                   | P1       |
| BP-07 | Never silently modify original repo; reversible workflow               | P0       |

### F. Safe Test Verification

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| TV-01 | Disposable, unprivileged Docker container                              | P1       |
| TV-02 | No host filesystem access beyond approved workspace                    | P0       |
| TV-03 | No network, resource/process/memory/time limits                        | P1       |
| TV-04 | Explicit approval before executing untrusted code                      | P0       |
| TV-05 | Baseline tests before patch, relevant tests after; compare results     | P1       |
| TV-06 | Show commands, exit codes, test summaries, logs                        | P0       |
| TV-07 | Never label patch "verified" unless tests actually passed              | P0       |
| TV-08 | If sandbox unavailable, support static analysis; disable execution     | P0       |

### G. Change Impact Analysis

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| CI-01 | Find direct dependents of a file/symbol/diff                          | P0       |
| CI-02 | Traverse dependency relationships                                      | P0       |
| CI-03 | Identify affected APIs, modules, tests                                 | P0       |
| CI-04 | Visual impact graph                                                    | P1       |
| CI-05 | Explain why each component is affected                                 | P1       |
| CI-06 | Distinguish confirmed from estimated dependencies                      | P1       |
| CI-07 | Produce regression-testing checklist                                   | P1       |

### H. Investigation History

| ID    | Requirement                                                            | Priority |
|-------|------------------------------------------------------------------------|----------|
| IH-01 | Persist repo version, question, evidence, findings, patches, outcomes  | P0       |
| IH-02 | Searchable history                                                     | P1       |
| IH-03 | Reproducible reports                                                   | P2       |

## 4. Non-Functional Requirements

| Area          | Requirement                                                              |
|---------------|--------------------------------------------------------------------------|
| Security      | See `docs/ARCHITECTURE.md` security section and threat model             |
| Performance   | Indexing < 60s for 10k-file repo; search < 500ms; graph render < 2s     |
| Reliability   | Graceful degradation when AI unavailable; never crash on parser errors   |
| Observability | Structured logging; health endpoint; error tracking                      |
| Portability   | Local dev on macOS/Linux/Windows; Docker Compose for full stack          |

## 5. Hackathon-Specific Requirements

- **Nebius Token Factory** adapter for authentication.
- **NVIDIA open model** inference through Nebius.
- Model name and provider configurable via environment variables.
- Health/status view showing configured provider.
- Must attribute model + provider in every AI response.
- Deterministic features must work without AI credentials.
- Document exactly how NVIDIA model + Nebius satisfy hackathon rules.

## 6. Acceptance Criteria (MVP)

1. Start the app from documented instructions.
2. Import a sample repository.
3. See real indexing progress and extracted symbols.
4. Search for a function → navigate to source.
5. Inspect a dependency graph from parsed relationships.
6. Ask a question → receive repository-grounded AI answer (Nebius/NVIDIA).
7. Review a proposed code patch (unified diff).
8. Execute tests in isolated sandbox or see clear explanation of why disabled.
9. Inspect genuine logs and test outcomes.
10. Reproduce demo using documented setup.

## 7. Out of Scope (MVP)

- Multi-user authentication and RBAC
- Real-time collaborative editing
- Kubernetes deployment
- Microservices decomposition
- Support for >10 programming languages
- CI/CD pipeline integration
- Production PostgreSQL migration (clean path documented, not required for MVP)
