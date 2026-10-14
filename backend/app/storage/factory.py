"""BlackBox — Storage Service Factory."""
from __future__ import annotations

from functools import lru_cache
import structlog

from app.config import get_settings
from app.storage.base import StorageService
from app.storage.local import LocalStorageService
from app.storage.r2 import R2StorageService

log = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    """
    Instantiate and cache the appropriate storage service.
    Guarantees that production never silently falls back to local ephemeral storage.
    """
    settings = get_settings()

    if settings.storage_backend == "r2" or settings.r2_enabled:
        if not settings.r2_enabled:
            raise ValueError(
                "Storage backend is configured as 'r2', but Cloudflare R2 credentials "
                "(R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME) are missing. "
                "Production safety policy: Refusing to silently fall back to local storage."
            )
        log.info("Initializing Cloudflare R2 storage service", bucket=settings.r2_bucket_name)
        return R2StorageService(
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
            endpoint_url=settings.r2_endpoint_url,
        )

    # Local development storage
    if settings.app_env == "production":
        raise ValueError(
            "Local filesystem storage is not permitted when APP_ENV=production. "
            "Please configure Cloudflare R2 (STORAGE_BACKEND=r2) with valid credentials."
        )

    log.info("Initializing local filesystem storage service for development")
    return LocalStorageService(root_dir=settings.workspace_root / "artifacts")
