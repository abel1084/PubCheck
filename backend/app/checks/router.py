"""
Check API router.
Exposes POST /api/check/{document_type} endpoint for running compliance checks.
"""
import time
from typing import List

from fastapi import APIRouter, HTTPException

from app.config.service import DocumentTypeId, RuleService
from app.models.extraction import ExtractionResult
from .executor import create_executor
from .models import CategoryResult, CheckResult

router = APIRouter(prefix="/api/check", tags=["check"])

# Singleton instances
_executor = create_executor()
_rule_service = RuleService()

# Fixed category order per CONTEXT.md
CATEGORY_ORDER: List[str] = [
    "cover",
    "margins",
    "typography",
    "images",
    "required_elements",
]


@router.post("/{document_type}", response_model=CheckResult)
async def run_checks(
    document_type: DocumentTypeId,
    extraction: ExtractionResult,
) -> CheckResult:
    """
    Run compliance checks on extracted PDF data.

    Args:
        document_type: The document type to check against (e.g., factsheet, publication)
        extraction: Extracted PDF data from upload endpoint

    Returns:
        CheckResult with categorized issues and overall status
    """
    start_time = time.time()

    # Load merged rules for document type
    try:
        template = _rule_service.get_merged_rules(document_type)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown document type: {document_type}"
        )

    # Execute checks by category
    category_results: List[CategoryResult] = []
    total_errors = 0
    total_warnings = 0

    for cat_id in CATEGORY_ORDER:
        if cat_id not in template.categories:
            # Include empty category for completeness per CONTEXT.md
            category_results.append(CategoryResult(
                category_id=cat_id,
                category_name=cat_id.replace("_", " ").title(),
                issues=[],
                error_count=0,
                warning_count=0,
            ))
            continue

        category = template.categories[cat_id]
        category_issues = []

        for rule_id, rule in category.rules.items():
            issues = _executor.execute_rule(extraction, rule)
            # Add rule_id to each issue for reference
            for issue in issues:
                issue.rule_id = rule_id
            category_issues.extend(issues)

        error_count = sum(1 for i in category_issues if i.severity == "error")
        warning_count = sum(1 for i in category_issues if i.severity == "warning")

        category_results.append(CategoryResult(
            category_id=cat_id,
            category_name=category.name,
            issues=category_issues,
            error_count=error_count,
            warning_count=warning_count,
        ))

        total_errors += error_count
        total_warnings += warning_count

    # Determine overall status per CONTEXT.md
    if total_errors > 0:
        status = "fail"
    elif total_warnings > 0:
        status = "warning"
    else:
        status = "pass"

    duration_ms = int((time.time() - start_time) * 1000)

    return CheckResult(
        document_type=document_type,
        categories=category_results,
        total_errors=total_errors,
        total_warnings=total_warnings,
        status=status,
        check_duration_ms=duration_ms,
    )
