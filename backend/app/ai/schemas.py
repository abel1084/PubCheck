"""
Schemas for AI-powered document review.
Simplified for single-call document review with streaming response.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    """Request for AI document review."""
    document_type: str = Field(..., description="Type of document being reviewed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Document type detection confidence")


class ReviewMetadata(BaseModel):
    """Metadata about the review process."""
    document_type: str
    page_count: int
    model_used: str
    estimated_tokens: Optional[int] = None
