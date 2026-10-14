"""BlackBox — Infrastructure Tests for Neon Postgres, Cloudflare R2, Upstash Redis & Nebius."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.config import Settings
from app.db.session import normalize_database_url
from app.queue.jobs import JobPayload, enqueue_job
from app.storage.base import StorageService
from app.storage.factory import get_storage_service
from app.storage.local import LocalStorageService
from app.storage.r2 import MAX_ARTIFACT_SIZE_BYTES, R2StorageService
from app.worker import process_job


def test_database_url_normalization():
    # Neon / standard PostgreSQL urls must be normalized to postgresql+asyncpg
    neon_url = "postgres://user:pass@ep-cool-123.neon.tech/neondb?ssl=require"
    assert normalize_database_url(neon_url) == "postgresql+asyncpg://user:pass@ep-cool-123.neon.tech/neondb?ssl=require"

    pg_url = "postgresql://user:pass@localhost:5432/blackbox"
    assert normalize_database_url(pg_url) == "postgresql+asyncpg://user:pass@localhost:5432/blackbox"

    # SQLite URLs should remain untouched
    sqlite_url = "sqlite+aiosqlite:///./test.db"
    assert normalize_database_url(sqlite_url) == sqlite_url


@pytest.mark.asyncio
async def test_local_storage_service():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalStorageService(root_dir=Path(tmp_dir))

        # Store
        uri = await storage.store_file("reports/test.txt", b"Hello BlackBox", "text/plain")
        assert uri == "local://reports/test.txt"

        # Exists
        assert await storage.file_exists("reports/test.txt")
        assert not await storage.file_exists("reports/missing.txt")

        # Retrieve
        data = await storage.retrieve_file("reports/test.txt")
        assert data == b"Hello BlackBox"

        # Delete
        assert await storage.delete_file("reports/test.txt")
        assert not await storage.file_exists("reports/test.txt")

        # Path traversal prevention
        with pytest.raises(ValueError, match="Path traversal detected"):
            await storage.store_file("../../escaped.txt", b"bad")


@pytest.mark.asyncio
async def test_r2_storage_bounds_and_operations():
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        r2 = R2StorageService(
            account_id="acc-123",
            access_key_id="key-123",
            secret_access_key="secret-123",
            bucket_name="blackbox-test",
        )

        # File size limit enforcement
        huge_data = b"X" * (MAX_ARTIFACT_SIZE_BYTES + 1)
        with pytest.raises(ValueError, match="exceeds maximum allowable limit"):
            await r2.store_file("big.bin", huge_data)

        # Normal store
        uri = await r2.store_file("reports/summary.json", b'{"ok": true}', "application/json")
        assert uri == "r2://blackbox-test/reports/summary.json"
        mock_s3.put_object.assert_called_once()

        # Presigned URL generation
        mock_s3.generate_presigned_url.return_value = "https://r2.test/download?sig=xyz"
        url = r2.generate_presigned_download_url("reports/summary.json", expires_in_seconds=3600)
        assert url == "https://r2.test/download?sig=xyz"


def test_storage_factory_production_safety():
    # Production without R2 must fail explicitly (no silent local fallback)
    with patch("app.storage.factory.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            app_env="production",
            storage_backend="local",
        )
        get_storage_service.cache_clear()
        with pytest.raises(ValueError, match="Local filesystem storage is not permitted"):
            get_storage_service()

        # R2 backend with missing credentials must fail explicitly
        mock_settings.return_value = Settings(
            app_env="production",
            storage_backend="r2",
            r2_access_key_id="",
        )
        get_storage_service.cache_clear()
        with pytest.raises(ValueError, match="Refusing to silently fall back"):
            get_storage_service()


@pytest.mark.asyncio
async def test_redis_queue_job_dispatch():
    # Enqueue when Redis is disabled falls back to in-process log safely
    with patch("app.queue.jobs.get_redis_client", return_value=None):
        job_id = await enqueue_job("index_repository", {"repo_id": 999})
        assert isinstance(job_id, str) and len(job_id) > 10


@pytest.mark.asyncio
async def test_worker_job_processing_retry_and_dispatch():
    job = JobPayload(
        job_type="index_repository",
        payload={"repo_id": 999999},  # Non-existent repo to trigger failure handling
        max_retries=1,
    )

    # Process job handles failure cleanly without crash
    success = await process_job(job)
    assert not success  # Handled cleanly
