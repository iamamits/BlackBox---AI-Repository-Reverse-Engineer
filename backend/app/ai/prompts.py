"""BlackBox — AI Prompt Templates and Grounded Context Builder."""
from __future__ import annotations

import json
from typing import Any, List

SYSTEM_PROMPT = """You are BlackBox — an advanced AI Repository Reverse Engineer and Autonomous Debugger.
You operate on code repositories using parsed AST symbols, architecture dependency graphs, and static code evidence.
Your inference is powered by NVIDIA open models hosted on Nebius Token Factory.

Your task is to answer questions, diagnose root causes, identify architectural hotspots, and propose verifiable patches.

CRITICAL INSTRUCTIONS:
1. Always ground your analysis in the provided repository context (files, classes, functions, and call edges).
2. Never invent non-existent file paths or symbols.
3. You MUST respond with a single, valid JSON object matching this exact structure:
{
  "summary": "Executive summary of findings",
  "classification": "architecture_query" | "bug" | "security" | "performance" | "refactor",
  "confidence": "high" | "medium" | "low",
  "findings": [
    {
      "title": "Title of finding",
      "description": "In-depth description",
      "severity": "low" | "medium" | "high" | "critical",
      "file": "path/to/file.py",
      "line": 42
    }
  ],
  "evidence_refs": [
    {
      "file": "path/to/file.py",
      "lines": "40-45",
      "snippet": "actual code excerpt"
    }
  ],
  "proposed_patch_diff": null or "--- a/file.py\\n+++ b/file.py\\n...",
  "proposed_patch_explanation": null or "Why this patch fixes the issue"
}
Do not wrap your output in markdown unless standard JSON. Ensure valid JSON parsing.
"""


def build_investigation_prompt(
    repo_name: str,
    question: str,
    files_summary: List[dict[str, Any]],
    symbols_summary: List[dict[str, Any]],
    dependency_edges: List[str] = None,
) -> str:
    """Format repository context into a concise grounded user prompt."""
    prompt_parts = [
        f"REPOSITORY: {repo_name}",
        f"USER INVESTIGATION QUESTION: {question}",
        "\n--- INDEXED SOURCE FILES (TOP SAMPLES) ---",
    ]

    for f in files_summary[:25]:
        prompt_parts.append(f"- {f.get('path')} ({f.get('language') or 'text'}, {f.get('line_count', 0)} lines)")

    prompt_parts.append("\n--- EXTRACTED AST SYMBOLS ---")
    for s in symbols_summary[:40]:
        sig = f": {s.get('signature')}" if s.get("signature") else ""
        prompt_parts.append(f"- [{s.get('kind')}] {s.get('name')} in {s.get('file')}{sig}")

    if dependency_edges:
        prompt_parts.append("\n--- ARCHITECTURE DEPENDENCY EDGES ---")
        for edge in dependency_edges[:20]:
            prompt_parts.append(f"- {edge}")

    prompt_parts.append(
        "\nProvide your detailed investigation analysis and concrete evidence in the requested JSON format."
    )
    return "\n".join(prompt_parts)
