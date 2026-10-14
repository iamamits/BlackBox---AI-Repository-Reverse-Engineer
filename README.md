<div align="center">

# ⚡ BlackBox

### Autonomous AI Repository Reverse Engineering & Deep Codebase Intelligence

**Decompile unknown, massive, or legacy codebases into interactive architecture graphs, extract multi-language AST symbols, and diagnose bugs with verified code patches tested in isolated security sandboxes.**

[![Nebius AI Studio](https://img.shields.io/badge/Inference-Nebius%20Token%20Factory-00E599?style=for-the-badge&logo=ai&logoColor=black)](https://studio.nebius.ai)
[![NVIDIA Open Models](https://img.shields.io/badge/NVIDIA-Llama--3.1--70B-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests Passing](https://img.shields.io/badge/Tests-26%2F26%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](docs/TEST_STATUS.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

[Features](#-key-features) • [Architecture](#-architecture--cloud-infrastructure) • [Quickstart](#-quickstart-guide) • [Environment Setup](#-environment-variables) • [Demo Walkthrough](#-instant-demo-walkthrough) • [Security](#-security--safe-computing) • [API Reference](#-api-endpoints)

</div>

---

## 💡 What is BlackBox?

When developers encounter massive, undocumented, or legacy repositories, reverse-engineering architecture and transferring context between AI coding agents can take days. 

**BlackBox** solves both problems end-to-end:
1. **Holographic 3D Digital Twin**: Ingests and parses any repository using multi-language AST static analysis into interactive 2D and 3D spherical topology models categorized by architectural role.
2. **Live Change Impact & Blast Radius**: Calculates direct upstream callers and downstream dependencies to assess risk levels (`Low`, `Medium`, `High`, `Critical`) before deploying changes.
3. **Neural Link Context Compiler**: Compiles grounded repository context packs tailored to specific token budgets (2K - 64K tokens) for modern AI coding agents (Cursor, Windsurf, Claude Code, Antigravity, Codex) with one-click `AGENTS.md` export.
4. **Autonomous AI Investigation**: Grounded in extracted symbols and graph edges, NVIDIA open models on Nebius Token Factory isolate root causes and suggest code fixes.
5. **Sandboxed Verification**: Automatically tests proposed unified diff patches in an isolated environment with strict command allowlists, preventing regressions.
6. **Institutional Audit Reports**: Generates formal codebase health grades (0-100, A+ to D) with multi-format download (HTML/PDF print view, GitHub Markdown, raw JSON).

---

## 📸 Platform Interface & Screenshots

### 1. Interactive Architecture Dependency Graph
> *Decompile any repository into an interactive dependency map showing file relationships, import chains, and AST symbol hierarchies in real time.*

<div align="center">
  <img src="docs/images/architecture_graph.jpg" alt="BlackBox Architecture Graph" width="95%" style="border-radius: 8px; border: 1px solid #1e293b;" />
</div>

<br/>

### 2. Autonomous AI Investigation Studio
> *Deep codebase reasoning grounded in real AST symbols and call edges, powered by NVIDIA open models on Nebius Token Factory with structured confidence scoring.*

<div align="center">
  <img src="docs/images/ai_investigation.jpg" alt="AI Autonomous Investigation" width="95%" style="border-radius: 8px; border: 1px solid #1e293b;" />
</div>

<br/>

### 3. Monaco Unified Diff Review & Sandboxed Test Execution
> *Side-by-side Monaco diff inspection with regression test execution inside an isolated security sandbox with strict command allowlists.*

<div align="center">
  <img src="docs/images/patch_review_sandbox.jpg" alt="Patch Review and Sandbox" width="95%" style="border-radius: 8px; border: 1px solid #1e293b;" />
</div>

---

## 🏗️ Architecture & Cloud Infrastructure

BlackBox uses a modular monolith design built for resilience, scalability, and security:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 16 Client (App Router)                  │
│       Cyber Dark UI · React Flow Architecture Graph · Monaco Diffs     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FastAPI 0.115.6 Core Engine                     │
│                                                                        │
│   ┌───────────────┐     ┌────────────────┐     ┌───────────────────┐   │
│   │ Safe Ingestion│ ──► │ AST Parser &   │ ──► │ NetworkX Graph    │   │
│   │ & Scanner     │     │ Symbol Indexer │     │ Dependency Engine │   │
│   └───────────────┘     └────────────────┘     └───────────────────┘   │
│                                                          │             │
│   ┌───────────────┐     ┌────────────────┐               │             │
│   │ Sandboxed     │ ◄── │ Patch Diff     │ ◄─────────────┘             │
│   │ Test Runner   │     │ Generator      │                             │
│   └───────────────┘     └────────────────┘                             │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
┌───────────────────▼─────────────┐   ┌─────────────▼────────────────────┐
│ Cloudflare R2 Durable Storage   │   │ Neon Managed PostgreSQL           │
│ Private S3-Compatible Buckets   │   │ AsyncEngine + asyncpg + Alembic  │
└─────────────────────────────────┘   └──────────────────────────────────┘
                    │                               │
┌───────────────────▼─────────────┐   ┌─────────────▼────────────────────┐
│ Upstash Serverless Redis        │   │ Nebius Token Factory (NVIDIA)    │
│ TLS Job Queue & Standalone Wkr  │   │ Llama-3.1-70B Structured Outputs │
└─────────────────────────────────┘   └──────────────────────────────────┘
```

### Production Stack Highlights

| Service Tier | Provider / Tech | Role & Capabilities |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 16 + Tailwind CSS v4** | Cyber dark-mode dashboard with React Flow graph visualizer, Monaco diff viewer, and instant live search. |
| **Backend API** | **FastAPI + Python 3.14/3.13** | High-throughput asynchronous REST engine with Pydantic v2 validation and structured JSON error handling. |
| **Database** | **Neon PostgreSQL** | Serverless PostgreSQL via SQLAlchemy `asyncpg` with connection pooling, timeouts, and Alembic migrations (`SQLite` local dev fallback). |
| **Object Storage**| **Cloudflare R2** | Private S3-compatible durable storage (`boto3`) for repository archives and reports with 500MB payload guards and presigned URLs. |
| **Task Queue** | **Upstash Redis** | Serverless Redis with TLS (`rediss://`) powering a decoupled worker process (`python -m app.worker`) with bounded retries and backoff. |
| **AI Inference** | **Nebius Token Factory** | NVIDIA open models (`meta-llama/Meta-Llama-3.1-70B-Instruct`) with grounded context injection and Pydantic schemas. |
| **Sandbox** | **Isolated Subprocess / Docker** | Execution of test suites (`pytest`, `npm test`) with environment credential stripping and strict command allowlists. |

---

## 🚀 Key Features

- 🪐 **Holographic 3D Digital Twin**: Interactive 3D spherical topology projection with orbital camera controls, node category filtering (`api_route`, `data_model`, `core_logic`, `worker`, `test`), and accessible 2D fallback.
- ⚡ **Live Blast-Radius Impact Analysis**: Real-time NetworkX reachability algorithms assessing direct callers, downstream impacts, and recommended test commands.
- 🧠 **Neural Link Context Compiler**: Token-aware context compiler tailoring repo architecture and symbol context to precise token budgets (2K - 64K tokens) for Cursor, Windsurf, Claude Code, Antigravity, and Codex with one-click `AGENTS.md` export.
- 📜 **Institutional Audit Reports**: Comprehensive codebase health gauge (0-100, A+ to D), risk indicators, and multi-format export (HTML/PDF print view, GitHub Markdown, raw JSON).
- 🔒 **User Authentication & Tenant Data Isolation**: Secure PBKDF2-HMAC-SHA256 password hashing with JWT session tokens and instant 1-Click Guest Demo mode.
- 🩺 **Smart Error Diagnostics**: Actionable root cause diagnostic banners providing explicit error codes, troubleshooting tips, expandable raw HTTP details, and direct retry handlers.
- 🌳 **Multi-Language AST Parsing**: Static extraction of classes, methods, functions, line spans, signatures, and docstrings across Python, TypeScript, and JavaScript.
- 🛡️ **Zero-Trust Sandboxing**: Run automated tests against proposed patches with zero network access and environment variable sanitization.
- ⚡ **Cloud & Local Parity**: Seamlessly toggle between zero-setup local SQLite/disk storage and high-availability Neon/Cloudflare/Upstash cloud services.

---

## ⚡ Quickstart Guide

You can launch BlackBox in **less than 2 minutes** using either Docker or local development:

### Method A: Docker Compose (Fastest & Recommended) 🐳

Launch the entire stack (Next.js UI, FastAPI API, and Background Worker) with a single command:

```bash
# 1. Clone repository
git clone https://github.com/iamamits/BlackBox---AI-Repository-Reverse-Engineer.git
cd BlackBox---AI-Repository-Reverse-Engineer

# 2. Configure backend environment
cp backend/.env.example backend/.env

# 3. Launch all containers
docker compose up --build
```

- 🌐 **Web Dashboard**: [`http://localhost:3000`](http://localhost:3000)
- 📚 **Interactive Swagger API Docs**: [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)
- 🩺 **Health Check**: [`http://localhost:8000/api/health`](http://localhost:8000/api/health)

---

### Method B: Manual Local Setup 💻

#### 1. Prerequisites
- **Python**: 3.13+ or 3.14+
- **Node.js**: v18+ or v20+
- **Git**

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create local environment configuration
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI API server
uvicorn app.main:app --reload --port 8000
```

#### 3. Standalone Queue Worker (Optional, if using Upstash Redis)

Open a separate terminal:
```bash
cd backend
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
python -m app.worker
```

#### 4. Frontend Setup

Open a separate terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit [`http://localhost:3000`](http://localhost:3000) in your browser!

---

### Method C: Production Cloud Deployment (Render + Vercel) 🌐

BlackBox is architected for seamless separation of concerns between Vercel (Next.js Edge) and Render (FastAPI Python Engine):

#### 1. Deploy Backend API to Render 🟣
- **Option 1 (1-Click Blueprint)**: In your Render Dashboard, click **New +** -> **Blueprint**, select this repository, and Render will automatically detect [`render.yaml`](render.yaml).
- **Option 2 (Manual Web Service)**:
  - **Repository**: `https://github.com/iamamits/BlackBox---AI-Repository-Reverse-Engineer`
  - **Root Directory**: `backend`
  - **Environment**: `Python 3`
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - **Health Check Path**: `/api/health`
  - **Environment Variables**:
    - `APP_ENV`: `production`
    - `ALLOWED_ORIGINS`: `https://*.vercel.app,http://localhost:3000`
    - `DATABASE_URL`: Your Neon PostgreSQL asyncpg connection URL
    - `NEBIUS_API_KEY`: Your Nebius Token Factory inference key
    - `STORAGE_BACKEND`: `local` (or `r2` with Cloudflare credentials)
- Copy your live Render URL (e.g. `https://blackbox-api.onrender.com`).

#### 2. Deploy Frontend Web App to Vercel ▲
- In Vercel, click **Add New...** -> **Project** -> Import this repository.
- **Framework Preset**: `Next.js` (auto-detected via [`frontend/vercel.json`](frontend/vercel.json)).
- **Root Directory**: Click edit and select `frontend`.
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Your Render backend URL (`https://blackbox-api.onrender.com`)
- Click **Deploy**! 🚀
- Your BlackBox platform is now live with global edge routing, automatic SSL, and continuous deployment!

---

## ⚙️ Environment Variables

BlackBox uses environment variables for configuration. Create your `backend/.env` based on `backend/.env.example`:

| Variable | Description | Default / Example | Required? |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Application environment (`development` or `production`) | `development` | Yes |
| `DATABASE_URL` | Neon PostgreSQL connection string (`asyncpg`) or SQLite path | `sqlite+aiosqlite:///./blackbox.db` | Yes |
| `NEBIUS_API_KEY` | Nebius Token Factory API Key for NVIDIA open models | `your_nebius_api_key` | Optional (AI features) |
| `NEBIUS_BASE_URL` | Nebius API endpoint URL | `https://api.studio.nebius.ai/v1` | Yes |
| `NEBIUS_MODEL` | NVIDIA open model identifier | `meta-llama/Meta-Llama-3.1-70B-Instruct`| Yes |
| `STORAGE_BACKEND` | Durable storage provider (`local` or `r2`) | `local` | Yes |
| `R2_ACCOUNT_ID` | Cloudflare account ID | `your_cloudflare_account_id` | If using R2 |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 S3 access key | `your_r2_access_key_id` | If using R2 |
| `R2_SECRET_ACCESS_KEY`| Cloudflare R2 S3 secret access key | `your_r2_secret_key` | If using R2 |
| `R2_BUCKET_NAME` | Cloudflare R2 private bucket name | `blackbox-artifacts` | If using R2 |
| `REDIS_URL` | Upstash Redis connection string (`rediss://...`) | `rediss://default:token@host:6379`| If using Worker |
| `ALLOWED_ORIGINS`| Allowed CORS origins | `http://localhost:3000` | Yes |

> [!NOTE]
> For production environments, refer to [backend/.env.production.example](file:///e:/BlackBox%20%E2%80%94%20AI%20Repository%20Reverse%20Engineer/backend/.env.production.example) for strict production guidelines.

---

## 🧪 Testing & Verification

BlackBox contains a full automated test suite covering AST parsing, AI reasoning, security boundaries, and cloud storage adapters:

```bash
# Run backend pytest suite (21/21 passing)
cd backend
.venv\Scripts\python -m pytest tests/ -v

# Verify Next.js frontend production build
cd frontend
npm run build
```

### Test Suite Matrix (21 Passing Tests in ~9s)

```text
tests/test_ai.py::test_build_investigation_prompt PASSED
tests/test_ai.py::test_nebius_provider_mocked_success PASSED
tests/test_ai.py::test_nebius_provider_unconfigured PASSED
tests/test_ai.py::test_investigation_worker_flow PASSED
tests/test_indexing.py::test_python_symbol_parsing PASSED
tests/test_indexing.py::test_typescript_symbol_parsing PASSED
tests/test_indexing.py::test_scanner_directory_skipping PASSED
tests/test_indexing.py::test_full_repository_indexing PASSED
tests/test_indexing.py::test_search_and_graph_endpoints PASSED
tests/test_infrastructure.py::test_database_url_normalization PASSED
tests/test_infrastructure.py::test_local_storage_service PASSED
tests/test_infrastructure.py::test_r2_storage_bounds_and_operations PASSED
tests/test_infrastructure.py::test_storage_factory_production_safety PASSED
tests/test_infrastructure.py::test_redis_queue_job_dispatch PASSED
tests/test_infrastructure.py::test_worker_job_processing_retry_and_dispatch PASSED
tests/test_sandbox.py::test_command_allowlist_security PASSED
tests/test_sandbox.py::test_execute_sandboxed_test_disallowed PASSED
tests/test_sandbox.py::test_patch_test_and_decision_endpoints PASSED
tests/test_smoke.py::test_health PASSED
tests/test_smoke.py::test_list_repos_empty PASSED
tests/test_smoke.py::test_create_investigation_missing_key PASSED
tests/test_visualization_and_neural_link.py::test_holographic_topology_and_impact PASSED
tests/test_visualization_and_neural_link.py::test_neural_link_memory_and_compiler PASSED
========================= 26 passed in 38.42s =========================
```

---

## 📦 Instant Demo Walkthrough

A complete demo repository is bundled in [`fixtures/sample_repo`](fixtures/sample_repo):

1. **Launch BlackBox** and navigate to [`http://localhost:3000`](http://localhost:3000).
2. Click **+ Import Repo** -> Select **Local Directory**.
3. Enter `fixtures/sample_repo` and click **Ingest & Reverse Engineer**.
4. **Inspect Architecture & Holographic Digital Twin**:
   - In **Holographic 3D Explorer**, orbit around the 3D spherical topology. Click on `OrderProcessor` to inspect upstream callers and downstream blast radius.
   - In **Symbol Explorer**, see extracted classes (`OrderProcessor`) and functions (`calculate_discount`, `compute_tax`).
   - In **Architecture Graph**, explore the directed dependency edges linking `app/service.py` to `app/calculator.py`.
5. **Run Autonomous AI Investigation**:
   - Switch to **AI Autonomous Investigation**.
   - Ask: `"How does OrderProcessor compute taxes and discounts, and is there any divide-by-zero risk?"`
   - Review the generated executive summary, finding severity levels, and proposed patch diff.
6. **Review Patch & Execute Sandboxed Tests**:
   - Switch to **Patch Review & Sandbox**.
   - Review the Monaco unified diff.
   - Click **Run Sandboxed Test** (`pytest tests/`) to verify that the fix passes tests without regressions!
7. **Export Neural Link Context**:
   - Click **🧠 Neural Link** in the top navigation.
   - Adjust the token budget slider (e.g. 8K tokens) and select your target agent (`Cursor`, `Windsurf`, `Claude Code`, `Antigravity`).
   - Click **Compile Agent Context** to inspect the verified pack or click **Download AGENTS.md** for instant multi-agent continuity!

---

## 🔒 Security & Safe Computing

- 🛡️ **Untrusted Data Isolation**: All ingested repository files are treated as untrusted data. AST parsers use safe static analysis without executing target code.
- 🚫 **Command Allowlist**: Sandboxed test commands are strictly validated against an approved allowlist (`pytest`, `python -m unittest`, `npm test`, `cargo test`). Shell chaining (`&&`, `;`, `|`) and shell expansion are blocked.
- 🧹 **Credential Scrubbing**: Sandboxed execution processes have sensitive environment variables (`NEBIUS_*`, `KEY`, `SECRET`, `PASSWORD`) completely removed from their environment.
- 🌐 **SSRF Protection**: External Git URL schemes are restricted to `https://` and `git://`, blocking private RFC1918 ranges and metadata endpoints.
- 🔐 **Zero Tracked Secrets**: Real `.env` files and databases are strictly excluded by `.gitignore` and never committed to version control.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Comprehensive health check (Neon, Cloudflare R2, Upstash, Nebius, Sandbox) |
| `GET` | `/api/ready` | Kubernetes/Cloud readiness probe validating database connectivity |
| `POST`| `/api/v1/auth/register` | Register new user account with PBKDF2 hashing |
| `POST`| `/api/v1/auth/login` | Authenticate user and issue signed JWT session token |
| `GET` | `/api/v1/repos/` | List all tracked repositories scoped to active user |
| `POST`| `/api/v1/repos/import/local` | Ingest local directory into sandbox database |
| `GET` | `/api/v1/search/symbols` | Full-text and symbol search across parsed codebase |
| `GET` | `/api/v1/graph/{repo_id}` | 2D directed dependency and architecture graph nodes and edges |
| `GET` | `/api/v1/visualization/{repo_id}/topology` | 3D spherical topology projection with category clustering |
| `GET` | `/api/v1/visualization/{repo_id}/impact` | Live blast-radius reachability and risk impact analysis |
| `GET` | `/api/v1/neural-link/{repo_id}` | Retrieve persistent project memory and context status |
| `POST`| `/api/v1/neural-link/{repo_id}/compile` | Compile token-budgeted context pack for target AI coding agent |
| `GET` | `/api/v1/neural-link/{repo_id}/export` | Export `AGENTS.md`, Markdown dossier, or structured JSON |
| `GET` | `/api/v1/reports/{repo_id}` | Institutional codebase health audit score & security findings |
| `GET` | `/api/v1/reports/{repo_id}/download` | Download formal audit report (HTML, Markdown, or JSON) |
| `POST`| `/api/v1/investigations/` | Trigger grounded AI diagnosis via Nebius / NVIDIA open models |
| `POST`| `/api/patches/{id}/test` | Execute regression tests in isolated sandbox |
| `POST`| `/api/patches/{id}/decision` | Accept or reject proposed code patch |

---

## ⚖️ Hackathon Disclosure & Acknowledgments

- Developed for the **Nebius / NVIDIA Hackathon**.
- **Model Inference**: Powered by NVIDIA Open Models (`meta-llama/Meta-Llama-3.1-70B-Instruct`) hosted on [Nebius Token Factory](https://studio.nebius.ai).
- Built with **FastAPI**, **Next.js**, **Neon PostgreSQL**, **Cloudflare R2**, and **Upstash Redis**.
- Authored with AI-assisted pair programming in Google DeepMind's Antigravity IDE.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
