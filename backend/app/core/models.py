"""BlackBox — SQLAlchemy ORM models."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── Enumerations ──────────────────────────────────────────────────────────


class RepoStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class SourceType(str, enum.Enum):
    LOCAL = "local"
    ZIP = "zip"
    GIT = "git"


class ParseStatus(str, enum.Enum):
    OK = "ok"
    PARTIAL = "partial"
    ERROR = "error"
    UNSUPPORTED = "unsupported"


class SymbolKind(str, enum.Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    EXPORT = "export"
    MODULE = "module"
    UNKNOWN = "unknown"


class DependencyType(str, enum.Enum):
    IMPORT = "import"
    CALL = "call"
    INHERITANCE = "inheritance"
    REFERENCE = "reference"


class ConfidenceLevel(str, enum.Enum):
    VERIFIED = "verified"
    HEURISTIC = "heuristic"


class InvestigationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class PatchStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SandboxStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


# ── Models ────────────────────────────────────────────────────────────────


class User(Base):
    """A registered user for workspace data isolation and session history."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="user", cascade="all, delete-orphan"
    )


class Repository(Base):
    """An imported repository being analysed."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    workspace_path: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[RepoStatus] = mapped_column(
        Enum(RepoStatus), nullable=False, default=RepoStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    primary_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    symbol_count: Mapped[int] = mapped_column(Integer, default=0)
    index_progress: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="repositories")
    files: Mapped[list["IndexedFile"]] = relationship(
        "IndexedFile", back_populates="repository", cascade="all, delete-orphan"
    )
    dependencies: Mapped[list["Dependency"]] = relationship(
        "Dependency", back_populates="repository", cascade="all, delete-orphan"
    )
    investigations: Mapped[list["Investigation"]] = relationship(
        "Investigation", back_populates="repository", cascade="all, delete-orphan"
    )
    memories: Mapped[list["ProjectMemory"]] = relationship(
        "ProjectMemory", back_populates="repository", cascade="all, delete-orphan"
    )


class IndexedFile(Base):
    """A source file that has been indexed within a repository."""

    __tablename__ = "indexed_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)  # relative to workspace root
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    parse_status: Mapped[ParseStatus] = mapped_column(
        Enum(ParseStatus), default=ParseStatus.UNSUPPORTED
    )
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    line_count: Mapped[int] = mapped_column(Integer, default=0)

    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    repository: Mapped[Repository] = relationship("Repository", back_populates="files")
    symbols: Mapped[list["Symbol"]] = relationship(
        "Symbol", back_populates="file", cascade="all, delete-orphan"
    )


class Symbol(Base):
    """A symbol (function, class, variable, etc.) extracted from a file."""

    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indexed_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qualified_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kind: Mapped[SymbolKind] = mapped_column(Enum(SymbolKind), nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("symbols.id", ondelete="SET NULL"), nullable=True
    )
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    file: Mapped[IndexedFile] = relationship("IndexedFile", back_populates="symbols")
    children: Mapped[list["Symbol"]] = relationship("Symbol", back_populates="parent")
    parent: Mapped[Optional["Symbol"]] = relationship(
        "Symbol", back_populates="children", remote_side="Symbol.id"
    )


class Dependency(Base):
    """A dependency edge between two files in a repository."""

    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indexed_files.id", ondelete="CASCADE"), nullable=False
    )
    target_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("indexed_files.id", ondelete="CASCADE"), nullable=False
    )
    dep_type: Mapped[DependencyType] = mapped_column(Enum(DependencyType), nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel), default=ConfidenceLevel.VERIFIED
    )
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    repository: Mapped[Repository] = relationship("Repository", back_populates="dependencies")


class Investigation(Base):
    """An AI-powered investigation session on a repository."""

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(InvestigationStatus), default=InvestigationStatus.PENDING
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    evidence_refs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    confidence: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    repository: Mapped[Repository] = relationship("Repository", back_populates="investigations")
    patches: Mapped[list["Patch"]] = relationship(
        "Patch", back_populates="investigation", cascade="all, delete-orphan"
    )


class Patch(Base):
    """A proposed code patch from an investigation."""

    __tablename__ = "patches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    investigation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[PatchStatus] = mapped_column(
        Enum(PatchStatus), default=PatchStatus.PROPOSED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation", back_populates="patches"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="patch", cascade="all, delete-orphan"
    )


class TestRun(Base):
    """A sandboxed test execution result."""

    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("patches.id", ondelete="CASCADE"), nullable=True
    )
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    command: Mapped[str] = mapped_column(Text, nullable=False)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sandbox_container_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[SandboxStatus] = mapped_column(
        Enum(SandboxStatus), default=SandboxStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    patch: Mapped[Optional[Patch]] = relationship("Patch", back_populates="test_runs")


# ── Neural Link & Project Memory ──────────────────────────────────────────


class ProjectMemory(Base):
    """Neural Link — Persistent, versioned project context memory."""

    __tablename__ = "project_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    commit_hash: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    # Structured Context Sections
    project_identity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    architecture_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conventions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decisions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_continuity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="memories")
    context_packs: Mapped[list["ContextPack"]] = relationship(
        "ContextPack", back_populates="memory", cascade="all, delete-orphan"
    )


class ContextPack(Base):
    """A token-budgeted, compiled context pack for coding agents."""

    __tablename__ = "context_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    memory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project_memories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="markdown")
    target_agent: Mapped[str] = mapped_column(String(50), default="generic")
    token_budget: Mapped[int] = mapped_column(Integer, default=8000)
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    memory: Mapped[ProjectMemory] = relationship("ProjectMemory", back_populates="context_packs")

