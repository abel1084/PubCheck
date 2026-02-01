"""
Pydantic models for PDF extraction data.
These models define the structure of extracted PDF content.
Compatible with Pydantic v1 and v2.
"""
from typing import List, Optional, Tuple

from pydantic import BaseModel


class TextBlock(BaseModel):
    """A block of text extracted from a PDF page."""
    text: str
    font: str  # Normalized (subset prefix stripped)
    size: float
    bold: bool
    italic: bool
    color: int  # RGB as integer
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page: int

    class Config:
        # Pydantic v1 config for compatibility
        arbitrary_types_allowed = True


class ImageInfo(BaseModel):
    """Information about an image extracted from a PDF."""
    xref: int
    width: int
    height: int
    colorspace: str
    dpi_x: float
    dpi_y: float
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page: int
    has_mask: bool
    width_mm: Optional[float] = None  # Rendered width in millimeters
    height_mm: Optional[float] = None  # Rendered height in millimeters

    class Config:
        arbitrary_types_allowed = True


class PageMargins(BaseModel):
    """Calculated margins for a PDF page (in points, 72 points = 1 inch)."""
    page: int
    top: float
    bottom: float
    left: float
    right: float
    # Inside/outside derived from odd/even page (assuming right-hand binding)
    inside: float
    outside: float


class DocumentMetadata(BaseModel):
    """Document-level metadata extracted from the PDF."""
    filename: str
    page_count: int
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    producer: Optional[str] = None
    isbn: Optional[str] = None
    doi: Optional[str] = None
    job_number: Optional[str] = None


class FontSummary(BaseModel):
    """Summary of a font used in the document."""
    name: str
    count: int
    pages: List[int]


class ExtractionResult(BaseModel):
    """Complete extraction result from a PDF document."""
    metadata: DocumentMetadata
    text_blocks: List[TextBlock]
    images: List[ImageInfo]
    margins: List[PageMargins]
    fonts: List[FontSummary]
