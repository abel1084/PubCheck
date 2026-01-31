"""
API router for ignored rules management.
Provides CRUD endpoints for learning/ignored rules.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from .models import IgnoredRule
from .service import IgnoredRulesService


# Singleton service instance
_service = IgnoredRulesService()

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/ignored-rules",
    tags=["learning"]
)


class AddIgnoredRuleRequest(BaseModel):
    """Request body for adding an ignored rule."""
    rule_id: str
    document_type: str
    reason: Optional[str] = None


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    success: bool


@router.get("/", response_model=List[IgnoredRule])
async def get_all_ignored_rules() -> List[IgnoredRule]:
    """
    Get all ignored rules.

    Returns:
        List of all ignored rules across all document types
    """
    return _service.get_all()


@router.get("/{document_type}", response_model=List[str])
async def get_ignored_rules_for_doc_type(document_type: str) -> List[str]:
    """
    Get rule IDs that are ignored for a specific document type.

    Args:
        document_type: The document type to filter by (e.g., "factsheet")

    Returns:
        List of rule_id strings to filter out during compliance checks
    """
    return _service.get_ignored_for_doc_type(document_type)


@router.post("/", response_model=IgnoredRule, status_code=status.HTTP_201_CREATED)
async def add_ignored_rule(request: AddIgnoredRuleRequest) -> IgnoredRule:
    """
    Add a rule to the ignored list.

    If the rule already exists for this document type, it will be updated.

    Args:
        request: Contains rule_id, document_type, and optional reason

    Returns:
        The created/updated IgnoredRule
    """
    return _service.add_rule(
        rule_id=request.rule_id,
        document_type=request.document_type,
        reason=request.reason
    )


@router.delete("/{rule_id}/{document_type}", response_model=DeleteResponse)
async def delete_ignored_rule(rule_id: str, document_type: str) -> DeleteResponse:
    """
    Remove a rule from the ignored list.

    Args:
        rule_id: The rule ID to remove
        document_type: The document type context

    Returns:
        Success status (true if removed, false if not found)

    Raises:
        404: If the rule was not found
    """
    success = _service.remove_rule(rule_id, document_type)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ignored rule not found: {rule_id} for {document_type}"
        )

    return DeleteResponse(success=True)
