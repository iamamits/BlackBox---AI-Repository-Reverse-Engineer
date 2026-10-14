"""BlackBox — Directory Scanner and File Discovery."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".next",
    ".turbo",
    "dist",
    "build",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "workspace_data",
}

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".rs": "rust",
    ".go": "go",
    ".md": "markdown",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".sh": "bash",
    ".bat": "batch",
    ".ps1": "powershell",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".zip", ".tar", ".gz", ".7z",
    ".db", ".sqlite", ".sqlite3",
    ".pyc", ".pyo", ".pyd",
    ".pdf", ".mp4", ".mp3",
}


@dataclass
class ScannedFile:
    """Represents a discovered file in a repository."""

    path: str  # forward-slash normalized relative path
    abs_path: Path
    language: Optional[str]
    size_bytes: int
    content_hash: str
    line_count: int
    is_text: bool


def detect_language(path: Path) -> Optional[str]:
    """Detect language from file suffix or name."""
    suffix = path.suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(suffix)


def scan_directory(root_dir: Path, max_file_size: int = 2 * 1024 * 1024) -> list[ScannedFile]:
    """
    Safely scan a directory, filtering out ignored folders and large/binary files.
    Returns normalized ScannedFile items.
    """
    results: list[ScannedFile] = []
    root = root_dir.resolve()

    if not root.exists() or not root.is_dir():
        return results

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

        for fname in filenames:
            file_path = Path(dirpath) / fname
            suffix = file_path.suffix.lower()

            if suffix in BINARY_EXTENSIONS:
                continue

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                if size_bytes > max_file_size:
                    continue  # skip files larger than max_file_size (e.g. minified bundles)

                # Compute SHA-256 and count lines
                hasher = hashlib.sha256()
                line_count = 0
                is_text = True

                try:
                    with open(file_path, "rb") as f:
                        raw = f.read()
                        hasher.update(raw)
                        # Check for null bytes to detect binary
                        if b"\x00" in raw:
                            is_text = False
                        else:
                            line_count = raw.count(b"\n") + (1 if raw and not raw.endswith(b"\n") else 0)
                except Exception:
                    is_text = False

                if not is_text:
                    continue

                rel_path = file_path.relative_to(root).as_posix()
                lang = detect_language(file_path)

                results.append(
                    ScannedFile(
                        path=rel_path,
                        abs_path=file_path,
                        language=lang,
                        size_bytes=size_bytes,
                        content_hash=hasher.hexdigest(),
                        line_count=line_count,
                        is_text=True,
                    )
                )
            except (OSError, PermissionError):
                continue

    return results
