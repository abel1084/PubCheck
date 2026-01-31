"""
Pydantic models for AI analysis responses.
Compatible with Pydantic v1 (using class Config pattern).
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AIFinding(BaseModel):
    """Single finding from AI analysis."""

    check_name: str = Field(description="Name of the check (e.g., 'UNEP Logo Position')")
    passed: bool = Field(description="Whether the check passed")
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the finding"
    )
    message: str = Field(description="Brief description of finding")
    reasoning: Optional[str] = Field(
        None, description="Explanation for non-obvious findings"
    )
    location: Optional[str] = Field(
        None, description="Descriptive location (e.g., 'top-right corner')"
    )
    suggestion: Optional[str] = Field(
        None, description="Fix suggestion for failures"
    )

    class Config:
        extra = "forbid"


class PageAnalysisResult(BaseModel):
    """Analysis result for a single page."""

    page_number: int = Field(description="1-indexed page number")
    findings: List[AIFinding] = Field(default_factory=list)
    error: Optional[str] = Field(
        None, description="Error message if analysis failed"
    )

    class Config:
        extra = "forbid"


class DocumentAnalysisResult(BaseModel):
    """Complete document analysis result."""

    page_results: List[PageAnalysisResult] = Field(default_factory=list)
    document_summary: Optional[str] = Field(
        None, description="Cross-page consistency notes"
    )
    total_findings: int = Field(default=0)
    analysis_duration_ms: int = Field(default=0)

    class Config:
        extra = "forbid"
