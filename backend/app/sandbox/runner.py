"""BlackBox — Sandboxed Subprocess Test Execution Runner."""
from __future__ import annotations

import asyncio
import os
import shlex
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import structlog

from app.core.models import SandboxStatus

log = structlog.get_logger(__name__)

# Strict command allowlist for test execution (prevents arbitrary command execution)
ALLOWED_PREFIXES = (
    "pytest",
    "python -m pytest",
    sys.executable + " -m pytest",
    "npm test",
    "npm run test",
    "cargo test",
    "go test",
    "vitest",
)


@dataclass
class TestRunResult:
    """Outcome of a sandboxed test command execution."""

    status: SandboxStatus
    exit_code: Optional[int]
    stdout: str
    stderr: str
    duration_seconds: float
    error_message: Optional[str] = None


def is_command_allowed(cmd: str) -> bool:
    """Validate that command strictly matches the security allowlist."""
    cmd_clean = cmd.strip()
    # Reject shell metacharacters that allow command chaining / redirection
    for dangerous_char in (";", "&&", "||", "|", "`", "$(", ">", "<", "&"):
        if dangerous_char in cmd_clean:
            return False

    return any(cmd_clean.startswith(prefix) for prefix in ALLOWED_PREFIXES)


async def execute_sandboxed_test(
    command: str,
    cwd: Path,
    timeout: float = 30.0,
    extra_env: Optional[dict[str, str]] = None,
) -> TestRunResult:
    """
    Execute a sandboxed test command inside an isolated environment.
    Scrubs sensitive credentials from environment variables.
    """
    if not is_command_allowed(command):
        return TestRunResult(
            status=SandboxStatus.ERROR,
            exit_code=-1,
            stdout="",
            stderr=f"Command '{command}' rejected: Not in security allowlist ({ALLOWED_PREFIXES})",
            duration_seconds=0.0,
            error_message="Command rejected by security sandbox policy",
        )

    # Clean environment — explicitly redact API keys & tokens
    safe_env = {k: v for k, v in os.environ.items() if not k.startswith("NEBIUS_") and "KEY" not in k and "SECRET" not in k and "TOKEN" not in k}
    if extra_env:
        safe_env.update(extra_env)

    start_time = time.monotonic()

    try:
        # Split args safely
        args = shlex.split(command, posix=(os.name != "nt"))

        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(cwd.resolve()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=safe_env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            duration = time.monotonic() - start_time
            exit_code = proc.returncode

            status = SandboxStatus.PASSED if exit_code == 0 else SandboxStatus.FAILED
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            return TestRunResult(
                status=status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=round(duration, 3),
            )

        except asyncio.TimeoutError:
            try:
                proc.kill()
            except OSError:
                pass
            duration = time.monotonic() - start_time
            return TestRunResult(
                status=SandboxStatus.TIMEOUT,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                duration_seconds=round(duration, 3),
                error_message="Test execution timed out",
            )

    except Exception as e:
        duration = time.monotonic() - start_time
        return TestRunResult(
            status=SandboxStatus.ERROR,
            exit_code=-1,
            stdout="",
            stderr=str(e),
            duration_seconds=round(duration, 3),
            error_message=str(e),
        )
