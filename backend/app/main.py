"""BlackBox — FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.session import Base, engine
from app.api import repos, indexing, search, graph, investigate, patches, ai, auth, reports

# ── Logging ───────────────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    log.info("BlackBox starting", env=settings.app_env, ai_enabled=settings.ai_enabled)

    # Create tables (Alembic will handle this in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Self-healing migration for existing databases: ensure user_id column exists on repositories
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE repositories ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
        except Exception:
            pass  # Already exists or handled by create_all
    log.info("Database tables initialised")

    yield

    log.info("BlackBox shutting down")
    await engine.dispose()


# ── Application ───────────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="BlackBox API",
    description="AI Repository Reverse Engineering & Autonomous Debugging Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error handlers ────────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled exception", exc=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An internal error occurred"}},
    )


# ── Health ────────────────────────────────────────────────────────────────


@app.get("/api/health", tags=["health"], summary="Service health and AI provider status")
async def health() -> dict[str, Any]:
    from app.core.schemas import HealthResponse, ProviderStatus

    settings = get_settings()

    # Test DB
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_type = "Neon PostgreSQL" if settings.is_postgres else "SQLite"
        db_status = f"{db_type} (connected)"
    except Exception as e:
        db_status = f"error: {e}"

    # AI provider status
    if settings.ai_enabled:
        ai_status = ProviderStatus(
            name="nebius",
            enabled=True,
            model=settings.nebius_model,
            base_url=settings.nebius_base_url,
            status="configured",
        )
    else:
        ai_status = ProviderStatus(
            name="nebius",
            enabled=False,
            model=None,
            base_url=None,
            status="unconfigured",
            error="Set NEBIUS_API_KEY in .env to enable AI features",
        )

    # Sandbox status
    sandbox_status = "unknown"
    try:
        import subprocess
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
        sandbox_status = "available" if result.returncode == 0 else "unavailable"
    except Exception:
        sandbox_status = "unavailable"

    storage_status = "Cloudflare R2" if settings.r2_enabled else "Local Disk"
    queue_status = "Upstash Redis" if settings.redis_enabled else "Local In-Process"

    overall = "ok" if "error" not in db_status else "degraded"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        database=db_status,
        ai_provider=ai_status,
        sandbox=sandbox_status,
        storage=storage_status,
        queue=queue_status,
    ).model_dump()


@app.get("/api/ready", tags=["health"], summary="Readiness probe")
async def ready() -> dict[str, Any]:
    """Readiness probe verifying database and core dependencies."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


# ── Routers ───────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(repos.router, prefix=API_PREFIX)
app.include_router(indexing.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(graph.router, prefix=API_PREFIX)
app.include_router(investigate.router, prefix=API_PREFIX)
app.include_router(patches.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
