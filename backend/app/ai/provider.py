"""BlackBox — Nebius / NVIDIA Open Models Inference Adapter."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, List, Optional
import httpx
import structlog

from app.ai.prompts import SYSTEM_PROMPT, build_investigation_prompt
from app.ai.schemas import InvestigationStructuredOutput
from app.config import get_settings

log = structlog.get_logger(__name__)

# Concurrency semaphore to bound simultaneous requests to Nebius API
_NEBIUS_SEMAPHORE = asyncio.Semaphore(5)


class NebiusAIProvider:
    """Inference client targeting Nebius Token Factory with NVIDIA open models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.nebius_api_key
        self.base_url = (base_url or settings.nebius_base_url).rstrip("/")
        self.model = model or settings.nebius_model
        self.max_retries = max_retries or settings.nebius_max_retries
        self.timeout_seconds = timeout_seconds or settings.nebius_timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your-nebius-api-key-here")

    def _clean_json_content(self, text: str) -> str:
        """Strip markdown fences if model outputs ```json ... ```."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    async def test_connection(self, model: Optional[str] = None) -> dict[str, Any]:
        """Test inference connectivity with a light ping prompt and measure latency."""
        import time

        if not self.is_configured:
            return {
                "status": "unconfigured",
                "configured": False,
                "latency_ms": None,
                "model": model or self.model,
                "message": "Nebius API key is not configured. Set NEBIUS_API_KEY in backend/.env.",
            }

        selected_model = model or self.model
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "user", "content": "Respond with the word 'OK' if you can read this."}
            ],
            "max_tokens": 10,
            "temperature": 0.0,
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return {
                        "status": "connected",
                        "configured": True,
                        "latency_ms": elapsed_ms,
                        "model": selected_model,
                        "message": f"Verified in {elapsed_ms}ms ({selected_model})",
                        "reply": reply[:50],
                    }
                elif resp.status_code == 401:
                    return {
                        "status": "error",
                        "configured": True,
                        "latency_ms": elapsed_ms,
                        "model": selected_model,
                        "message": "Authentication failed (HTTP 401). Please verify your NEBIUS_API_KEY in backend/.env.",
                    }
                elif resp.status_code == 429:
                    return {
                        "status": "rate_limited",
                        "configured": True,
                        "latency_ms": elapsed_ms,
                        "model": selected_model,
                        "message": "Rate limit exceeded (HTTP 429). Please wait before testing again.",
                    }
                else:
                    return {
                        "status": "error",
                        "configured": True,
                        "latency_ms": elapsed_ms,
                        "model": selected_model,
                        "message": f"Nebius API returned HTTP {resp.status_code}: {resp.text[:100]}",
                    }
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "configured": True,
                "latency_ms": None,
                "model": selected_model,
                "message": "Connection timed out after 10.0s. Please check network connectivity.",
            }
        except Exception as e:
            return {
                "status": "error",
                "configured": True,
                "latency_ms": None,
                "model": selected_model,
                "message": f"Connection error: {str(e)}",
            }

    async def investigate(
        self,
        repo_name: str,
        question: str,
        files_summary: List[dict[str, Any]],
        symbols_summary: List[dict[str, Any]],
        dependency_edges: Optional[List[str]] = None,
    ) -> InvestigationStructuredOutput:
        """Execute grounded AI investigation session via Nebius with bounded retries."""
        if not self.is_configured:
            raise ValueError(
                "Nebius API key is not configured. Set NEBIUS_API_KEY in your environment or .env file."
            )

        prompt = build_investigation_prompt(
            repo_name=repo_name,
            question=question,
            files_summary=files_summary,
            symbols_summary=symbols_summary,
            dependency_edges=dependency_edges,
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        async with _NEBIUS_SEMAPHORE:
            last_exception: Optional[Exception] = None

            for attempt in range(1, self.max_retries + 1):
                try:
                    log.info(
                        "Dispatching request to Nebius Token Factory",
                        model=self.model,
                        endpoint=endpoint,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )

                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        resp = await client.post(endpoint, headers=headers, json=payload)

                        # Handle rate limiting or server errors with backoff
                        if resp.status_code in (429, 502, 503, 504):
                            wait_s = 2 ** attempt
                            log.warning(
                                "Nebius transient error, retrying",
                                status_code=resp.status_code,
                                wait_seconds=wait_s,
                            )
                            await asyncio.sleep(wait_s)
                            continue

                        if resp.status_code != 200:
                            log.error("Nebius API error", status_code=resp.status_code, body=resp.text)
                            raise RuntimeError(
                                f"Nebius Token Factory inference failed (HTTP {resp.status_code}): {resp.text}"
                            )

                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        cleaned = self._clean_json_content(raw_content)

                        try:
                            parsed_dict = json.loads(cleaned)
                            return InvestigationStructuredOutput.model_validate(parsed_dict)
                        except Exception as e:
                            log.warning("JSON parsing error, constructing fallback schema", error=str(e))
                            return InvestigationStructuredOutput(
                                summary=raw_content[:500],
                                classification="architecture_query",
                                confidence="medium",
                            )

                except httpx.TimeoutException as e:
                    last_exception = RuntimeError(
                        f"Nebius request timed out after {self.timeout_seconds}s (attempt {attempt}/{self.max_retries})"
                    )
                    log.warning("Nebius request timeout", attempt=attempt)
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)

                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise e

            if last_exception:
                raise last_exception
            raise RuntimeError("Nebius inference failed after maximum retry attempts")
