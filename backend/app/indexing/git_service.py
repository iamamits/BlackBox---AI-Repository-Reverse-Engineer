"""BlackBox — Robust Git Repository Ingestion Service.

Clones public Git repositories via 'git clone --depth 1' with an automatic
HTTP ZIP archive fallback for GitHub repositories.
Includes SSRF validation, timeout guards, and path traversal protection.
"""
from __future__ import annotations

import asyncio
import io
from pathlib import Path
import shutil
import urllib.parse
import zipfile
import httpx
import structlog

log = structlog.get_logger(__name__)

# SSRF Blocked Hosts / Subnets
DISALLOWED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # AWS/GCP metadata
    "metadata.google.internal",
}


def validate_git_url(url: str) -> tuple[bool, str]:
    """Validate that the Git URL is public and not targeting local/metadata endpoints."""
    cleaned = url.strip()
    if not (cleaned.startswith("https://") or cleaned.startswith("http://")):
        return False, "Only http:// and https:// Git URLs are supported."

    try:
        parsed = urllib.parse.urlparse(cleaned)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False, "Invalid repository URL hostname."

        if hostname in DISALLOWED_HOSTS or hostname.startswith("127.") or hostname.startswith("10.") or hostname.startswith("192.168."):
            return False, "SSRF Protection: Access to local or private network ranges is blocked."

        return True, "OK"
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def extract_repo_name(url: str, default: str = "imported-repo") -> str:
    """Extract a clean repository name from a Git URL."""
    try:
        cleaned = url.strip().rstrip("/").removesuffix(".git")
        parts = cleaned.split("/")
        if parts:
            name = parts[-1].strip()
            if name:
                # Sanitize characters
                safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))
                return safe[:80] if safe else default
    except Exception:
        pass
    return default


async def clone_git_repo(url: str, dest_dir: Path, timeout_seconds: float = 90.0) -> tuple[bool, str]:
    """
    Safely clone or download a Git repository into dest_dir:
    1. Try 'git clone --depth 1'.
    2. Fallback to GitHub ZIP archive download if Git CLI fails or URL is on github.com.
    """
    valid, reason = validate_git_url(url)
    if not valid:
        return False, reason

    # Clean existing destination if present
    try:
        if dest_dir.exists():
            shutil.rmtree(dest_dir, ignore_errors=True)
        dest_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        log.warning("Primary dest_dir not writable, falling back to tempdir", error=str(e), dest=str(dest_dir))
        import tempfile
        dest_dir = Path(tempfile.gettempdir()) / "blackbox_workspace" / dest_dir.name
        dest_dir.mkdir(parents=True, exist_ok=True)

    # ── Strategy 1: Fast Shallow Git Clone ──────────────────────────────────
    log.info("Attempting shallow git clone", url=url, dest=str(dest_dir))
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
            url,
            str(dest_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
            if proc.returncode == 0 and any(dest_dir.iterdir()):
                log.info("Git shallow clone succeeded", url=url, dest=str(dest_dir))
                return True, "Successfully cloned via Git"
            else:
                err_msg = stderr.decode("utf-8", errors="replace").strip()
                log.warning("Git clone exited with non-zero code, attempting fallback", code=proc.returncode, stderr=err_msg[:200])
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            log.warning("Git clone timed out, attempting ZIP archive fallback", timeout=timeout_seconds)
    except FileNotFoundError:
        log.warning("Git executable not found in PATH, falling back to HTTP archive download")
    except Exception as e:
        log.warning("Git clone error, attempting HTTP fallback", error=str(e))

    # ── Strategy 2: GitHub Archive ZIP Fallback ──────────────────────────────
    cleaned_url = url.strip().rstrip("/").removesuffix(".git")
    parsed = urllib.parse.urlparse(cleaned_url)
    if "github.com" in (parsed.hostname or ""):
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            owner, repo_slug = parts[0], parts[1]
            log.info("Attempting GitHub ZIP archive download fallback", owner=owner, repo=repo_slug)

            for branch in ["main", "master"]:
                zip_url = f"https://github.com/{owner}/{repo_slug}/archive/refs/heads/{branch}.zip"
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_seconds) as client:
                        resp = await client.get(zip_url)
                        if resp.status_code == 200 and len(resp.content) > 0:
                            # Extract with zip bomb protection (max 250MB, max 10,000 files)
                            total_bytes = 0
                            file_count = 0
                            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                                for member in zf.infolist():
                                    file_count += 1
                                    total_bytes += member.file_size
                                    if file_count > 10000 or total_bytes > 250 * 1024 * 1024:
                                        return False, "Repository exceeds safe archive limits (max 250MB or 10,000 files)."

                                    # Path traversal protection
                                    target_path = (dest_dir / member.filename).resolve()
                                    if not str(target_path).startswith(str(dest_dir.resolve())):
                                        return False, "Malicious path traversal detected inside archive."

                                zf.extractall(dest_dir)

                            # Flatten single root folder if zip extracted into a subfolder e.g. repo-main/
                            subdirs = [d for d in dest_dir.iterdir() if d.is_dir()]
                            if len(subdirs) == 1 and subdirs[0].name.startswith(f"{repo_slug}-"):
                                inner = subdirs[0]
                                for item in inner.iterdir():
                                    target = dest_dir / item.name
                                    if target.exists():
                                        if target.is_dir():
                                            shutil.rmtree(target, ignore_errors=True)
                                        else:
                                            target.unlink(missing_ok=True)
                                    shutil.move(str(item), str(dest_dir))
                                shutil.rmtree(inner, ignore_errors=True)

                            log.info("GitHub ZIP archive download succeeded", files=len(list(dest_dir.iterdir())))
                            return True, f"Successfully imported via GitHub {branch} archive"
                except Exception as ex:
                    log.warning("Branch zip download attempt failed", branch=branch, error=str(ex))

    # Check if files arrived regardless
    if dest_dir.exists() and any(dest_dir.iterdir()):
        return True, "Repository files present"

    return False, "Failed to clone repository via Git and HTTP archive fallback."
