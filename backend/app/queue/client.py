"""BlackBox — Upstash Redis Client with TLS and SSL support."""
from __future__ import annotations

from typing import Optional
import redis.asyncio as aioredis
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> Optional[aioredis.Redis]:
    """
    Return shared async Redis client compatible with Upstash Redis.
    Supports TLS (rediss://), auto-reconnect, and socket timeouts.
    """
    global _redis_client
    settings = get_settings()

    if not settings.redis_enabled:
        return None

    if _redis_client is None:
        log.info("Connecting to Upstash Redis", url_scheme=settings.redis_url.split("://")[0])
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )

    return _redis_client


async def close_redis_client() -> None:
    """Gracefully close Redis connections."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
