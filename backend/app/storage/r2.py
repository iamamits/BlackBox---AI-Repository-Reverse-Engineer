"""BlackBox — Cloudflare R2 S3-Compatible Object Storage Service."""
from __future__ import annotations

import asyncio
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import structlog

from app.storage.base import StorageService

log = structlog.get_logger(__name__)

# Security & resource bounds
MAX_ARTIFACT_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB limit
DEFAULT_MAX_RETRIES = 3


class R2StorageService(StorageService):
    """Cloudflare R2 storage using the S3-compatible API."""

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
    ):
        if not access_key_id or not secret_access_key or not bucket_name:
            raise ValueError("Cloudflare R2 requires access_key_id, secret_access_key, and bucket_name.")

        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url or f"https://{account_id}.r2.cloudflarestorage.com"

        # R2 S3 Client configuration
        config = Config(
            region_name="auto",
            signature_version="s3v4",
            retries={"max_attempts": DEFAULT_MAX_RETRIES, "mode": "standard"},
        )

        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=config,
        )

    async def store_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload an artifact to private Cloudflare R2 bucket with size checks."""
        size = len(data)
        if size > MAX_ARTIFACT_SIZE_BYTES:
            raise ValueError(
                f"Artifact size ({size} bytes) exceeds maximum allowable limit of {MAX_ARTIFACT_SIZE_BYTES} bytes."
            )

        clean_key = key.lstrip("/\\")

        def _sync_put():
            self._client.put_object(
                Bucket=self.bucket_name,
                Key=clean_key,
                Body=data,
                ContentType=content_type,
            )

        await asyncio.to_thread(_sync_put)
        log.info("Stored artifact in Cloudflare R2", bucket=self.bucket_name, key=clean_key, bytes=size)
        return f"r2://{self.bucket_name}/{clean_key}"

    async def retrieve_file(self, key: str) -> bytes:
        """Download an artifact from Cloudflare R2."""
        clean_key = key.lstrip("/\\")

        def _sync_get():
            try:
                resp = self._client.get_object(Bucket=self.bucket_name, Key=clean_key)
                return resp["Body"].read()
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                    raise FileNotFoundError(f"Cloudflare R2 artifact not found: {clean_key}") from e
                raise

        return await asyncio.to_thread(_sync_get)

    async def delete_file(self, key: str) -> bool:
        """Delete an artifact from Cloudflare R2."""
        clean_key = key.lstrip("/\\")

        def _sync_delete():
            try:
                self._client.delete_object(Bucket=self.bucket_name, Key=clean_key)
                return True
            except ClientError:
                return False

        return await asyncio.to_thread(_sync_delete)

    async def file_exists(self, key: str) -> bool:
        """Check artifact existence via head_object."""
        clean_key = key.lstrip("/\\")

        def _sync_head():
            try:
                self._client.head_object(Bucket=self.bucket_name, Key=clean_key)
                return True
            except ClientError:
                return False

        return await asyncio.to_thread(_sync_head)

    def generate_presigned_download_url(
        self,
        key: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a short-lived presigned URL for secure authorized download."""
        clean_key = key.lstrip("/\\")
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": clean_key},
            ExpiresIn=min(expires_in_seconds, 86400),  # Max 24 hours
        )
