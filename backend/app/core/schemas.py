"""BlackBox — Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.models import (
    ConfidenceLevel,
    DependencyType,
    InvestigationStatus,
    PatchStatus,
    ParseStatus,
    RepoStatus,
    SandboxStatus,
    SourceType,
    SymbolKind,
)


# ── Shared ────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


# ── Repository ────────────────────────────────────────────────────────────


class RepoBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType


class RepoImportLocal(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., description="Absolute path to local repository folder")


class RepoImportGit(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., description="Public Git repository URL")


class RepoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: SourceType
    source_path: str
    status: RepoStatus
    error_message: str | None
    primary_language: str | None
    file_count: int
    symbol_count: int
    index_progress: float
    created_at: datetime
    updated_at: datetime


class RepoSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: RepoStatus
    primary_language: str | None
    file_count: int
    symbol_count: int
    index_progress: float
    created_at: datetime


class RepoList(BaseModel):
    items: list[RepoSummary]
    total: int


# ── Indexing ──────────────────────────────────────────────────────────────


class IndexingStatus(BaseModel):
    repository_id: int
    status: RepoStatus
    progress: float
    files_processed: int
    files_total: int
    symbols_extracted: int
    current_file: str | None
    error_message: str | None


# ── Files & Symbols ───────────────────────────────────────────────────────


class SymbolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    qualified_name: str | None
    kind: SymbolKind
    line_start: int
    line_end: int
    docstring: str | None
    signature: str | None
    file_id: int


class IndexedFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    path: str
    language: str | None
    size_bytes: int
    parse_status: ParseStatus
    parse_error: str | None
    line_count: int
    symbol_count: int = 0
    indexed_at: datetime


# ── Search ────────────────────────────────────────────────────────────────


class SearchQuery(BaseModel):
    q: str = Field(..., min_length=1, max_length=500)
    repository_id: int
    kinds: list[SymbolKind] | None = None
    languages: list[str] | None = None
    page: int = 1
    page_size: int = 20


class SearchHit(BaseModel):
    symbol_id: int | None
    file_id: int
    file_path: str
    symbol_name: str | None
    symbol_kind: SymbolKind | None
    line_start: int
    line_end: int
    snippet: str
    language: str | None
    score: float


class SearchResponse(BaseModel):
    query: str
    repository_id: int
    total: int
    hits: list[SearchHit]


# ── Graph ─────────────────────────────────────────────────────────────────


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str  # file | class | function | module
    language: str | None
    path: str | None
    line_start: int | None
    symbol_count: int


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    dep_type: DependencyType
    confidence: ConfidenceLevel
    evidence: str | None


class GraphResponse(BaseModel):
    repository_id: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    truncated: bool = False
    node_count: int
    edge_count: int


# ── Investigation ─────────────────────────────────────────────────────────


class EvidenceRef(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    snippet: str
    relevance: str


class InvestigationCreate(BaseModel):
    repository_id: int
    question: str = Field(..., min_length=5, max_length=4000)
    model: str | None = Field(None, description="Optional LLM model override")


class InvestigationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    question: str
    classification: str | None
    status: InvestigationStatus
    summary: str | None
    findings: str | None
    evidence_refs: str | None
    confidence: str | None
    model_used: str | None
    provider_used: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


# ── Patch ─────────────────────────────────────────────────────────────────


class PatchCreate(BaseModel):
    investigation_id: int
    diff: str
    explanation: str | None = None


class PatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investigation_id: int
    diff: str
    explanation: str | None
    status: PatchStatus
    created_at: datetime


class PatchDecision(BaseModel):
    decision: str  # "accept" | "reject"


# ── Test Runs ─────────────────────────────────────────────────────────────


class TestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patch_id: int | None
    repository_id: int
    command: str
    exit_code: int | None
    stdout: str | None
    stderr: str | None
    duration_seconds: float | None
    status: SandboxStatus
    created_at: datetime


# ── Health ────────────────────────────────────────────────────────────────


class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    model: str | None
    base_url: str | None
    status: str  # "ok" | "unreachable" | "unconfigured"
    error: str | None = None


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    version: str
    database: str
    ai_provider: ProviderStatus
    sandbox: str
    storage: str = "local"
    queue: str = "in_process"


# ── User & Auth ───────────────────────────────────────────────────────────


class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str | None = None


class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime


class UserProfileStats(BaseModel):
    user: UserRead
    repository_count: int
    investigation_count: int
    patch_count: int


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ── Reports ───────────────────────────────────────────────────────────────


class MetricCard(BaseModel):
    label: str
    value: str
    change: str | None = None
    status: str = "normal"  # normal | good | warning | critical


class AuditFinding(BaseModel):
    title: str
    severity: str  # critical | high | medium | low | info
    category: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    remediation: str | None = None


class RepoAuditReport(BaseModel):
    repository_id: int
    repository_name: str
    primary_language: str | None = None
    source_type: str
    health_score: int  # 0 to 100
    security_grade: str  # A+, A, B, C, D
    generated_at: str
    metrics: list[MetricCard]
    summary: str
    component_breakdown: list[dict[str, Any]]
    symbol_statistics: dict[str, int]
    security_findings: list[AuditFinding]
    investigation_history: list[dict[str, Any]]
    patches_summary: list[dict[str, Any]]

