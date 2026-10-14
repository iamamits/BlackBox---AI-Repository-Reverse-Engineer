"""BlackBox — Abstract Storage Interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class StorageService(ABC):
    """Abstract interface for storing and retrieving durable repository artifacts."""

    @abstractmethod
    async def store_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Store binary file data and return its identifier or URI."""
        pass

    @abstractmethod
    async def retrieve_file(self, key: str) -> bytes:
        """Retrieve stored binary content by key."""
        pass

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete an artifact by key."""
        pass

    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """Check whether an artifact exists."""
        pass

    @abstractmethod
    def generate_presigned_download_url(
        self,
        key: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a short-lived download URL."""
        pass
