"""BlackBox — Repository Indexing Orchestrator Service."""
from __future__ import annotations

import collections
from pathlib import Path
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    ConfidenceLevel,
    Dependency,
    DependencyType,
    IndexedFile,
    ParseStatus,
    Repository,
    RepoStatus,
    SourceType,
    Symbol,
)
from app.db.session import AsyncSessionLocal
from app.indexing.parser import parse_file
from app.indexing.scanner import scan_directory

log = structlog.get_logger(__name__)


async def index_repository(repo_id: int) -> None:
    """
    Background worker that indexes an imported repository:
    1. Scans workspace directory for source files.
    2. Ingests IndexedFile records.
    3. Parses symbols (functions, classes) and builds dependency links.
    4. Updates index progress and status.
    """
    log.info("Starting repository indexing", repo_id=repo_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if not repo:
            log.error("Repository not found for indexing", repo_id=repo_id)
            raise ValueError(f"Repository {repo_id} not found for indexing")

        from app.indexing.git_service import clone_git_repo
        from app.config import get_settings
        import zipfile

        settings = get_settings()

        # Handle GIT cloning
        if repo.source_type == SourceType.GIT:
            if not repo.workspace_path:
                repo.workspace_path = str(settings.workspace_root / f"repo_git_{repo.id}")
            target_dir = Path(repo.workspace_path)
            if not target_dir.exists() or not any(target_dir.iterdir()):
                repo.status = RepoStatus.INDEXING
                repo.index_progress = 0.1
                await db.commit()
                log.info("Cloning Git repository into workspace", repo_id=repo.id, url=repo.source_path, dest=str(target_dir))
                success, clone_msg = await clone_git_repo(repo.source_path, target_dir)
                if not success:
                    repo.status = RepoStatus.ERROR
                    repo.error_message = f"Git clone failed: {clone_msg}"
                    await db.commit()
                    log.error("Git clone failed", repo_id=repo.id, error=clone_msg)
                    return
        elif repo.source_type == SourceType.ZIP:
            target_dir = Path(repo.workspace_path or settings.workspace_root / f"zip_{repo.id}")
            repo.workspace_path = str(target_dir)
            zip_file = Path(repo.source_path)
            if zip_file.exists() and zip_file.is_file() and zip_file.suffix.lower() == ".zip":
                target_dir.mkdir(parents=True, exist_ok=True)
                try:
                    with zipfile.ZipFile(zip_file, "r") as zf:
                        zf.extractall(target_dir)
                except Exception as ex:
                    log.warning("ZIP extraction failed", error=str(ex))
        else:
            target_dir = Path(repo.workspace_path or repo.source_path)

        if not target_dir.exists():
            repo.status = RepoStatus.ERROR
            repo.error_message = f"Repository path not found: {target_dir}"
            await db.commit()
            return

        repo.status = RepoStatus.INDEXING
        repo.index_progress = 0.25
        await db.commit()

        # Step 1: Discover files
        scanned_files = scan_directory(target_dir)
        total_files = len(scanned_files)
        log.info("Scanned files discovered", repo_id=repo_id, count=total_files)

        if total_files == 0:
            repo.status = RepoStatus.READY
            repo.file_count = 0
            repo.symbol_count = 0
            repo.index_progress = 1.0
            await db.commit()
            return

        lang_counter: collections.Counter[str] = collections.Counter()
        total_symbols = 0
        file_record_map: dict[str, IndexedFile] = {}
        pending_deps: list[tuple[IndexedFile, list]] = []

        # Step 2: Ingest files and parse symbols
        for i, sf in enumerate(scanned_files, start=1):
            if sf.language:
                lang_counter[sf.language] += 1

            parse_res = parse_file(sf.abs_path, sf.language, sf.path)

            status_map = {
                "ok": ParseStatus.OK,
                "partial": ParseStatus.PARTIAL,
                "error": ParseStatus.ERROR,
                "unsupported": ParseStatus.UNSUPPORTED,
            }
            parsed_status = status_map.get(parse_res.parse_status, ParseStatus.UNSUPPORTED)

            indexed_file = IndexedFile(
                repository_id=repo.id,
                path=sf.path,
                language=sf.language,
                size_bytes=sf.size_bytes,
                content_hash=sf.content_hash,
                parse_status=parsed_status,
                parse_error=parse_res.parse_error,
                line_count=sf.line_count,
            )
            db.add(indexed_file)
            await db.flush()  # get indexed_file.id
            file_record_map[sf.path] = indexed_file

            if parse_res.dependencies:
                pending_deps.append((indexed_file, parse_res.dependencies))

            # Add extracted symbols
            for sym in parse_res.symbols:
                s_rec = Symbol(
                    file_id=indexed_file.id,
                    repository_id=repo.id,
                    name=sym.name,
                    qualified_name=sym.qualified_name,
                    kind=sym.kind,
                    line_start=sym.line_start,
                    line_end=sym.line_end,
                    signature=sym.signature,
                    docstring=sym.docstring,
                )
                db.add(s_rec)
                total_symbols += 1

            # Update progress periodically
            if i % 10 == 0 or i == total_files:
                repo.index_progress = min(0.1 + (i / total_files) * 0.7, 0.85)
                await db.commit()

        # Step 2.5: Resolve inter-file dependency edges
        module_lookup: dict[str, IndexedFile] = {}
        for path_str, file_obj in file_record_map.items():
            path_no_ext = path_str.rsplit(".", 1)[0]
            module_lookup[path_str] = file_obj
            module_lookup[path_no_ext] = file_obj
            module_lookup[path_no_ext.replace("/", ".")] = file_obj

        for src_file, dep_list in pending_deps:
            for dep in dep_list:
                target_obj = module_lookup.get(dep.target_name)
                if not target_obj:
                    # Try relative prefix match
                    for mod_key, f_obj in module_lookup.items():
                        if mod_key.endswith(dep.target_name) or dep.target_name.endswith(mod_key):
                            target_obj = f_obj
                            break

                if target_obj and target_obj.id != src_file.id:
                    edge = Dependency(
                        repository_id=repo.id,
                        source_file_id=src_file.id,
                        target_file_id=target_obj.id,
                        dep_type=dep.dep_type,
                        confidence=ConfidenceLevel.VERIFIED,
                        evidence=dep.evidence,
                    )
                    db.add(edge)

        await db.flush()

        # Step 3: Determine primary language and finalize
        primary_lang = lang_counter.most_common(1)[0][0] if lang_counter else None

        repo.file_count = total_files
        repo.symbol_count = total_symbols
        repo.primary_language = primary_lang
        repo.index_progress = 1.0
        repo.status = RepoStatus.READY
        await db.commit()

        log.info(
            "Repository indexing complete",
            repo_id=repo_id,
            files=total_files,
            symbols=total_symbols,
            primary_language=primary_lang,
        )
