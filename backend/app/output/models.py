"""
Pydantic models for PDF annotation output.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel


class IssueAnnotation(BaseModel):
    """A single issue to annotate on the PDF."""
    page: int  # 1-indexed page number
    x: Optional[float] = None  # x coordinate, None if no location
    y: Optional[float] = None  # y coordinate, None if no location
    message: str  # issue message to display
    severity: Literal["error", "warning"]
    reviewer_note: Optional[str] = None  # user's note if any

    class Config:
        arbitrary_types_allowed = True


class AnnotationRequest(BaseModel):
    """Request model for PDF annotation endpoint."""
    issues: List[IssueAnnotation]

    class Config:
        arbitrary_types_allowed = True
