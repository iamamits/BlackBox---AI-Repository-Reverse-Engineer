"""BlackBox — Local Filesystem Storage Service."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.storage.base import StorageService


class LocalStorageService(StorageService):
    """Local disk storage implementation for development environments."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, key: str) -> Path:
        """Resolve path and prevent directory traversal outside root."""
        if ".." in key or key.startswith("/") or key.startswith("\\"):
            # Check if attempting traversal
            clean_test = (self.root_dir / key.lstrip("/\\")).resolve()
            if not str(clean_test).startswith(str(self.root_dir)):
                raise ValueError(f"Path traversal detected for key: {key}")

        clean_key = key.lstrip("/\\")
        target = (self.root_dir / clean_key).resolve()
        if not str(target).startswith(str(self.root_dir)):
            raise ValueError(f"Path traversal detected for key: {key}")
        return target

    async def store_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        target = self._safe_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"local://{key}"

    async def retrieve_file(self, key: str) -> bytes:
        target = self._safe_path(key)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"Artifact not found: {key}")
        return target.read_bytes()

    async def delete_file(self, key: str) -> bool:
        target = self._safe_path(key)
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False

    async def file_exists(self, key: str) -> bool:
        target = self._safe_path(key)
        return target.exists() and target.is_file()

    def generate_presigned_download_url(
        self,
        key: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        # In local development, returns an API route relative path
        return f"/api/v1/storage/download/{key}"
