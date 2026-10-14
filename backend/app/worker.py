"""BlackBox — Separately Deployable Background Worker Process."""
from __future__ import annotations

import asyncio
import json
import signal
import sys
from typing import Optional
import structlog

from app.config import get_settings
from app.indexing.service import index_repository
from app.api.investigate import _run_investigation
from app.queue.client import close_redis_client, get_redis_client
from app.queue.jobs import JobPayload

log = structlog.get_logger(__name__)

_shutdown_event = asyncio.Event()


def _handle_shutdown_signal(*args):
    log.info("Shutdown signal received, draining active jobs...")
    _shutdown_event.set()


async def process_job(job: JobPayload) -> bool:
    """Execute a single job with bounded retries and error isolation."""
    log.info("Processing background job", job_id=job.job_id, job_type=job.job_type)

    try:
        if job.job_type == "index_repository":
            repo_id = job.payload.get("repo_id")
            if repo_id is not None:
                await index_repository(int(repo_id))
            else:
                raise ValueError("Missing 'repo_id' in index_repository job payload")

        elif job.job_type == "run_investigation":
            inv_id = job.payload.get("investigation_id")
            if inv_id is not None:
                await _run_investigation(int(inv_id))
            else:
                raise ValueError("Missing 'investigation_id' in run_investigation job payload")

        else:
            log.warning("Unknown job type received", job_type=job.job_type)

        log.info("Job completed successfully", job_id=job.job_id)
        return True

    except Exception as e:
        log.error("Job execution failed", job_id=job.job_id, error=str(e), retries=job.retries)

        if job.retries < job.max_retries:
            job.retries += 1
            client = get_redis_client()
            if client is not None:
                # Exponential backoff retry
                delay = 2 ** job.retries
                log.info("Re-queueing job after backoff", job_id=job.job_id, retry=job.retries, delay_s=delay)
                try:
                    await asyncio.sleep(delay)
                    await client.lpush(get_settings().redis_queue_name, job.model_dump_json())
                except Exception as requeue_err:
                    log.warning("Failed to requeue job to Redis", error=str(requeue_err))
        return False


async def run_worker():
    """Main worker event loop polling Upstash Redis."""
    settings = get_settings()
    client = get_redis_client()

    if client is None:
        log.info(
            "Worker is idling: REDIS_URL is not configured. Background jobs are handled in-process by the backend API. "
            "To enable the distributed queue worker, configure REDIS_URL in backend/.env."
        )
        try:
            await _shutdown_event.wait()
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        log.info("Worker gracefully stopped.")
        return

    queue_key = settings.redis_queue_name
    log.info("BlackBox Worker started", queue=queue_key, pid=sys.platform)

    while not _shutdown_event.is_set():
        try:
            # Pop with 2-second timeout to check shutdown event
            result = await client.brpop(queue_key, timeout=2)
            if result is not None:
                _, raw_data = result
                try:
                    job_data = json.loads(raw_data)
                    job = JobPayload.model_validate(job_data)
                    await process_job(job)
                except Exception as parse_err:
                    log.error("Failed to parse job payload from queue", err=str(parse_err))
        except (asyncio.CancelledError, KeyboardInterrupt):
            break
        except Exception as conn_err:
            log.warning("Redis poll exception, retrying in 3 seconds", error=str(conn_err))
            await asyncio.sleep(3)

    log.info("Worker gracefully stopped.")
    await close_redis_client()


if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_shutdown_signal)
        except (ValueError, AttributeError):
            pass

    asyncio.run(run_worker())
