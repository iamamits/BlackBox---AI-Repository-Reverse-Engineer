"""BlackBox Backend — Application Settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    allowed_origins: Union[str, list[str]] = ["http://localhost:3000"]

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database (PostgreSQL with asyncpg for Neon, or SQLite for local dev)
    database_url: str = "sqlite+aiosqlite:///./blackbox.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Workspace / Storage
    blackbox_workspace_root: Path = Path("./workspace_data")
    storage_backend: Literal["local", "r2", "s3"] = "local"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_endpoint_url: str = ""

    # S3 alias fields for Cloudflare R2 / S3 compatibility
    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    @field_validator("storage_backend", mode="before")
    @classmethod
    def normalize_storage_backend(cls, v: Any) -> str:
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("s3", "r2", "cloudflare"):
                return "r2"
            return v_clean
        return v

    @model_validator(mode="after")
    def resolve_storage_credentials(self) -> Settings:
        """Alias S3_* credentials into r2_* variables if provided."""
        if not self.r2_endpoint_url and self.s3_endpoint_url:
            self.r2_endpoint_url = self.s3_endpoint_url
        if not self.r2_bucket_name and self.s3_bucket:
            self.r2_bucket_name = self.s3_bucket
        if not self.r2_access_key_id and self.s3_access_key_id:
            self.r2_access_key_id = self.s3_access_key_id
        if not self.r2_secret_access_key and self.s3_secret_access_key:
            self.r2_secret_access_key = self.s3_secret_access_key
        return self

    # Nebius / NVIDIA Inference
    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.studio.nebius.ai/v1"
    nebius_model: str = "nvidia/Nemotron-3-Ultra-550b-a55b"
    nebius_max_retries: int = 3
    nebius_timeout_seconds: float = 60.0

    # Upstash Redis
    redis_url: str = ""
    redis_queue_name: str = "blackbox_jobs"

    @property
    def is_postgres(self) -> bool:
        """True if the configured database is PostgreSQL."""
        return "postgres" in self.database_url.lower()

    @property
    def r2_enabled(self) -> bool:
        """True when Cloudflare R2 credentials are configured."""
        return bool(
            self.r2_access_key_id
            and self.r2_secret_access_key
            and self.r2_bucket_name
            and (self.r2_endpoint_url or self.r2_account_id)
        )

    @property
    def redis_enabled(self) -> bool:
        """True when Upstash Redis is configured."""
        return bool(self.redis_url and self.redis_url.startswith(("redis://", "rediss://")))

    @property
    def ai_enabled(self) -> bool:
        """True when a real Nebius API key is configured."""
        return bool(self.nebius_api_key and self.nebius_api_key != "your-nebius-api-key-here")

    @property
    def workspace_root(self) -> Path:
        """Resolved, absolute workspace root path."""
        p = self.blackbox_workspace_root.resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
