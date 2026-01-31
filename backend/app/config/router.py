"""
REST API endpoints for rule configuration.
Provides CRUD operations for managing rule settings per document type.
"""
from fastapi import APIRouter, HTTPException
from typing import Literal

from .models import UserOverrides
from .service import RuleService, DocumentTypeId

router = APIRouter(prefix="/api/rules", tags=["rules"])

# Singleton service instance
_rule_service = RuleService()


def get_rule_service() -> RuleService:
    """Get the rule service instance."""
    return _rule_service


# Valid document types for path validation
VALID_DOCUMENT_TYPES = {"factsheet", "policy-brief", "issue-note", "working-paper", "publication"}


def validate_document_type(document_type: str) -> DocumentTypeId:
    """
    Validate and return the document type.

    Raises:
        HTTPException: If document type is invalid
    """
    if document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid document type: {document_type}. "
                   f"Valid types: {', '.join(sorted(VALID_DOCUMENT_TYPES))}"
        )
    # Type narrowing for mypy
    return document_type  # type: ignore


@router.get("/{document_type}")
async def get_rules(document_type: str):
    """
    Get rules for a document type.

    Returns merged rules (base template + user overrides).

    Args:
        document_type: One of factsheet, policy-brief, issue-note, working-paper, publication

    Returns:
        Template with all rules and their current settings
    """
    doc_type = validate_document_type(document_type)
    service = get_rule_service()

    try:
        rules = service.get_merged_rules(doc_type)
        return rules.dict()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{document_type}")
async def save_rules(document_type: str, overrides: UserOverrides):
    """
    Save user rule overrides for a document type.

    Only saves fields that differ from defaults.

    Args:
        document_type: One of factsheet, policy-brief, issue-note, working-paper, publication
        overrides: UserOverrides containing changed settings

    Returns:
        {"status": "saved"} on success
    """
    doc_type = validate_document_type(document_type)
    service = get_rule_service()

    try:
        service.save_overrides(doc_type, overrides)
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save overrides: {str(e)}")


@router.post("/{document_type}/reset")
async def reset_rules(document_type: str):
    """
    Reset rules to defaults for a document type.

    Deletes user override file if it exists.

    Args:
        document_type: One of factsheet, policy-brief, issue-note, working-paper, publication

    Returns:
        {"status": "reset"} on success
    """
    doc_type = validate_document_type(document_type)
    service = get_rule_service()

    service.delete_overrides(doc_type)
    return {"status": "reset"}
