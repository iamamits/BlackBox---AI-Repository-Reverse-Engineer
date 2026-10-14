"""BlackBox — Job Definitions and Queue Dispatcher for Upstash Redis."""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
import structlog

from app.config import get_settings
from app.queue.client import get_redis_client

log = structlog.get_logger(__name__)


class JobPayload(BaseModel):
    """Normalized payload representing a background task."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str  # "index_repository" | "run_investigation"
    payload: dict[str, Any]
    retries: int = 0
    max_retries: int = 3
    created_at: float = Field(default_factory=time.time)


async def enqueue_job(
    job_type: str,
    payload: dict[str, Any],
    max_retries: int = 3,
) -> str:
    """
    Enqueue a background task to Upstash Redis.
    If Redis is not configured, logs fallback for in-process execution.
    """
    settings = get_settings()
    client = get_redis_client()

    job = JobPayload(
        job_type=job_type,
        payload=payload,
        max_retries=max_retries,
    )

    if client is not None:
        queue_key = settings.redis_queue_name
        data = job.model_dump_json()
        await client.lpush(queue_key, data)
        log.info("Enqueued job to Upstash Redis", job_id=job.job_id, job_type=job_type, queue=queue_key)
        return job.job_id
    else:
        log.info("Redis not configured; task dispatched for in-process execution", job_id=job.job_id, job_type=job_type)
        return job.job_id
