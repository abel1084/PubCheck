"""
Compliance checking module for PDF design validation.

This module provides:
- CheckIssue, CategoryResult, CheckResult: Models for check results
- CheckExecutor: Handler registry and execution engine
- Tolerance utilities: Centralized comparison functions
"""
from .models import CategoryResult, CheckIssue, CheckResult
from .executor import CheckExecutor, create_executor

__all__ = [
    "CheckIssue",
    "CategoryResult",
    "CheckResult",
    "CheckExecutor",
    "create_executor",
]
