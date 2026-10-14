"""BlackBox — AST and Symbol Extraction Parser."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.core.models import DependencyType, SymbolKind


@dataclass
class ParsedSymbol:
    """A symbol extracted from source code."""

    name: str
    kind: SymbolKind
    line_start: int
    line_end: int
    qualified_name: Optional[str] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_name: Optional[str] = None


@dataclass
class ParsedDependency:
    """A dependency reference extracted from source code."""

    target_name: str
    dep_type: DependencyType
    evidence: Optional[str] = None


@dataclass
class ParseResult:
    """Aggregated symbols and dependencies extracted from a file."""

    symbols: list[ParsedSymbol] = field(default_factory=list)
    dependencies: list[ParsedDependency] = field(default_factory=list)
    parse_status: str = "ok"
    parse_error: Optional[str] = None


def parse_python_file(content: str, rel_path: str = "") -> ParseResult:
    """Extract Python symbols and imports using standard library AST parser."""
    symbols: list[ParsedSymbol] = []
    dependencies: list[ParsedDependency] = []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return ParseResult(symbols=[], dependencies=[], parse_status="partial", parse_error=str(e))
    except Exception as e:
        return ParseResult(symbols=[], dependencies=[], parse_status="error", parse_error=str(e))

    lines = content.splitlines()

    def get_signature_line(lineno: int) -> Optional[str]:
        if 1 <= lineno <= len(lines):
            return lines[lineno - 1].strip()
        return None

    for node in ast.walk(tree):
        # Functions and methods
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            docstring = ast.get_docstring(node)
            sig = get_signature_line(start)

            symbols.append(
                ParsedSymbol(
                    name=node.name,
                    kind=SymbolKind.FUNCTION,
                    line_start=start,
                    line_end=end,
                    qualified_name=f"{rel_path}:{node.name}" if rel_path else node.name,
                    signature=sig,
                    docstring=docstring,
                )
            )

        # Classes
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            docstring = ast.get_docstring(node)
            sig = get_signature_line(start)

            symbols.append(
                ParsedSymbol(
                    name=node.name,
                    kind=SymbolKind.CLASS,
                    line_start=start,
                    line_end=end,
                    qualified_name=f"{rel_path}:{node.name}" if rel_path else node.name,
                    signature=sig,
                    docstring=docstring,
                )
            )

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.append(
                    ParsedDependency(
                        target_name=alias.name,
                        dep_type=DependencyType.IMPORT,
                        evidence=f"import {alias.name}",
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                dependencies.append(
                    ParsedDependency(
                        target_name=node.module,
                        dep_type=DependencyType.IMPORT,
                        evidence=f"from {node.module} import ...",
                    )
                )

    return ParseResult(symbols=symbols, dependencies=dependencies, parse_status="ok")


# Regex patterns for JavaScript / TypeScript symbol extraction
TS_FUNCTION_PATTERN = re.compile(
    r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(", re.MULTILINE
)
TS_ARROW_FUNCTION_PATTERN = re.compile(
    r"^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", re.MULTILINE
)
TS_CLASS_PATTERN = re.compile(
    r"^(?:export\s+)?(?:abstract\s+)?class\s+([a-zA-Z0-9_$]+)", re.MULTILINE
)
TS_IMPORT_PATTERN = re.compile(
    r"^import\s+(?:(?:{[^}]+}|\*\s+as\s+[a-zA-Z0-9_$]+|[a-zA-Z0-9_$]+)\s+from\s+)?['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)


def parse_typescript_file(content: str, rel_path: str = "") -> ParseResult:
    """Extract TypeScript / JavaScript symbols and imports via pattern recognition."""
    symbols: list[ParsedSymbol] = []
    dependencies: list[ParsedDependency] = []
    lines = content.splitlines()

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Functions
        m_func = TS_FUNCTION_PATTERN.match(stripped)
        if m_func:
            name = m_func.group(1)
            symbols.append(
                ParsedSymbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    line_start=idx,
                    line_end=idx,
                    qualified_name=f"{rel_path}:{name}" if rel_path else name,
                    signature=stripped,
                )
            )
            continue

        # Arrow functions
        m_arrow = TS_ARROW_FUNCTION_PATTERN.match(stripped)
        if m_arrow:
            name = m_arrow.group(1)
            symbols.append(
                ParsedSymbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    line_start=idx,
                    line_end=idx,
                    qualified_name=f"{rel_path}:{name}" if rel_path else name,
                    signature=stripped,
                )
            )
            continue

        # Classes
        m_class = TS_CLASS_PATTERN.match(stripped)
        if m_class:
            name = m_class.group(1)
            symbols.append(
                ParsedSymbol(
                    name=name,
                    kind=SymbolKind.CLASS,
                    line_start=idx,
                    line_end=idx,
                    qualified_name=f"{rel_path}:{name}" if rel_path else name,
                    signature=stripped,
                )
            )
            continue

        # Imports
        m_import = TS_IMPORT_PATTERN.match(stripped)
        if m_import:
            target = m_import.group(1)
            dependencies.append(
                ParsedDependency(
                    target_name=target,
                    dep_type=DependencyType.IMPORT,
                    evidence=stripped,
                )
            )

    return ParseResult(symbols=symbols, dependencies=dependencies, parse_status="ok")


def parse_file(abs_path: Path, language: Optional[str], rel_path: str = "") -> ParseResult:
    """Dispatch file parsing to appropriate language parser."""
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ParseResult(parse_status="error", parse_error=str(e))

    if language == "python":
        return parse_python_file(content, rel_path)
    elif language in ("typescript", "javascript"):
        return parse_typescript_file(content, rel_path)

    return ParseResult(parse_status="unsupported")
