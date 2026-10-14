"""BlackBox — AI Structured Response Schemas."""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class FindingItem(BaseModel):
    """A specific finding discovered during code investigation."""

    title: str = Field(description="Brief title of finding")
    description: str = Field(description="Detailed explanation")
    severity: Literal["low", "medium", "high", "critical"] = "low"
    file: Optional[str] = None
    line: Optional[int] = None


class EvidenceItem(BaseModel):
    """Grounded code snippet serving as concrete evidence."""

    file: str = Field(description="Relative path of file")
    lines: str = Field(description="Line range, e.g. '12-25'")
    snippet: str = Field(description="Source code excerpt")


class InvestigationStructuredOutput(BaseModel):
    """Structured response from Nebius/NVIDIA open model."""

    summary: str = Field(description="Executive summary of the investigation")
    classification: str = Field(
        default="architecture_query",
        description="Category: bug, performance, architecture_query, security, refactor",
    )
    confidence: Literal["high", "medium", "low"] = "high"
    findings: List[FindingItem] = Field(default_factory=list)
    evidence_refs: List[EvidenceItem] = Field(default_factory=list)
    proposed_patch_diff: Optional[str] = Field(
        default=None, description="Optional unified diff resolving the issue"
    )
    proposed_patch_explanation: Optional[str] = Field(
        default=None, description="Explanation of what the patch changes"
    )
