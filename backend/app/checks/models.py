"""
Pydantic models for compliance check results.
Compatible with Pydantic v1 (using class Config pattern).
"""
from typing import List, Literal, Optional

from pydantic import BaseModel


class CheckIssue(BaseModel):
    """A single compliance issue found during checking."""
    rule_id: str
    rule_name: str
    severity: Literal["error", "warning"]
    message: str  # Human-readable description
    expected: Optional[str] = None  # Formatted for display
    actual: Optional[str] = None  # Formatted for display
    pages: List[int]  # 1-indexed page numbers
    how_to_fix: Optional[str] = None  # Hint for obvious fixes

    class Config:
        arbitrary_types_allowed = True


class CategoryResult(BaseModel):
    """Results for a single category of checks."""
    category_id: str
    category_name: str
    issues: List[CheckIssue]
    error_count: int
    warning_count: int

    class Config:
        arbitrary_types_allowed = True


class CheckResult(BaseModel):
    """Complete compliance check result."""
    document_type: str
    categories: List[CategoryResult]
    total_errors: int
    total_warnings: int
    status: Literal["pass", "fail", "warning"]  # pass=no errors, fail=has errors, warning=warnings only
    check_duration_ms: int

    class Config:
        arbitrary_types_allowed = True
