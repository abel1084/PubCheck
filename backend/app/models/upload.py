"""
PubCheck - Upload Models
Pydantic models for upload endpoint responses
"""
from typing import Literal

from pydantic import BaseModel

from app.models.extraction import ExtractionResult
from app.services.document_type_detector import DocumentType, Confidence


class UploadResponse(BaseModel):
    """Successful upload response with extraction results."""
    success: Literal[True] = True
    filename: str
    document_type: DocumentType
    confidence: Confidence
    extraction: ExtractionResult


class RejectionResponse(BaseModel):
    """
    Response when a PDF is rejected (e.g., rasterized/scanned).

    Includes helpful information about why the PDF was rejected
    and where to find accessibility guidance.
    """
    success: Literal[False] = False
    error: str
    message: str
    details: str
    accessibility_info: str = "https://www.w3.org/WAI/WCAG21/Techniques/pdf/"
