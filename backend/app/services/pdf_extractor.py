"""
PDF extraction orchestration service.
Coordinates all extraction operations and aggregates results.
"""
import re
from collections import defaultdict

import pymupdf

from app.models.extraction import (
    DocumentMetadata,
    ExtractionResult,
    FontSummary,
    TextBlock,
)
from app.services.text_processor import extract_text_blocks
from app.services.image_processor import extract_images
from app.services.margin_calculator import calculate_margins


class PDFExtractor:
    """
    Main PDF extraction orchestrator.

    Coordinates extraction of text, images, margins, and metadata from a PDF.
    """

    def __init__(self, file_bytes: bytes, filename: str):
        """
        Initialize extractor with PDF file data.

        Args:
            file_bytes: Raw PDF file bytes
            filename: Original filename for metadata
        """
        self.file_bytes = file_bytes
        self.filename = filename
        self._doc: pymupdf.Document | None = None

    def _open_document(self) -> pymupdf.Document:
        """Open the PDF document if not already open."""
        if self._doc is None:
            self._doc = pymupdf.open(stream=self.file_bytes, filetype="pdf")
        return self._doc

    def close(self) -> None:
        """Close the PDF document and release resources."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def extract(self) -> ExtractionResult:
        """
        Perform full extraction of PDF content.

        Extracts:
        - Document metadata (title, author, ISBN, DOI, job number)
        - Text blocks with font info and coordinates
        - Images with DPI and colorspace
        - Page margins
        - Font usage summary

        Returns:
            ExtractionResult containing all extracted data
        """
        doc = self._open_document()

        # Extract metadata
        metadata = self._extract_metadata(doc)

        # Extract content from each page
        all_text_blocks: list[TextBlock] = []
        all_images: list = []
        all_margins: list = []

        for page_idx in range(doc.page_count):
            page = doc[page_idx]
            # Use 1-indexed page numbers for display
            page_num = page_idx + 1

            # Extract text blocks
            text_blocks = extract_text_blocks(page, page_num)
            all_text_blocks.extend(text_blocks)

            # Extract images
            images = extract_images(doc, page, page_num)
            all_images.extend(images)

            # Calculate margins
            margins = calculate_margins(page, page_num)
            all_margins.append(margins)

        # Summarize fonts
        fonts = self._summarize_fonts(all_text_blocks)

        return ExtractionResult(
            metadata=metadata,
            text_blocks=all_text_blocks,
            images=all_images,
            margins=all_margins,
            fonts=fonts,
        )

    def _extract_metadata(self, doc: pymupdf.Document) -> DocumentMetadata:
        """
        Extract document metadata including ISBN, DOI, and job number.

        Searches first 3 pages for ISBN, DOI, and job number patterns.

        Args:
            doc: PyMuPDF document object

        Returns:
            DocumentMetadata with standard and extracted fields
        """
        meta = doc.metadata or {}

        # Standard metadata fields
        title = meta.get("title") or None
        author = meta.get("author") or None
        creation_date = meta.get("creationDate") or None
        producer = meta.get("producer") or None

        # Clean empty strings to None
        if title and not title.strip():
            title = None
        if author and not author.strip():
            author = None
        if creation_date and not creation_date.strip():
            creation_date = None
        if producer and not producer.strip():
            producer = None

        # Extract text from first 3 pages for ISBN/DOI/job number search
        full_text = ""
        pages_to_search = min(3, doc.page_count)
        for i in range(pages_to_search):
            full_text += doc[i].get_text("text")

        # ISBN pattern: ISBN followed by 10 or 13 digit number (with optional dashes)
        isbn_match = re.search(
            r'ISBN[:\s-]*([0-9][-0-9]{9,16}[0-9X])',
            full_text,
            re.IGNORECASE
        )
        isbn = isbn_match.group(1).replace("-", "") if isbn_match else None

        # DOI pattern: 10.XXXX/... (standard DOI format)
        doi_match = re.search(
            r'(10\.\d{4,}/[^\s]+)',
            full_text
        )
        doi = doi_match.group(1).rstrip('.,;:)') if doi_match else None

        # Job number pattern: Job followed by alphanumeric code
        # Customize this pattern for your organization
        job_match = re.search(
            r'Job[:\s#]*([A-Z0-9][-A-Z0-9]{3,})',
            full_text,
            re.IGNORECASE
        )
        job_number = job_match.group(1) if job_match else None

        return DocumentMetadata(
            filename=self.filename,
            page_count=doc.page_count,
            title=title,
            author=author,
            creation_date=creation_date,
            producer=producer,
            isbn=isbn,
            doi=doi,
            job_number=job_number,
        )

    def _summarize_fonts(self, text_blocks: list[TextBlock]) -> list[FontSummary]:
        """
        Create summary of fonts used in the document.

        Groups text blocks by font name and counts occurrences.

        Args:
            text_blocks: List of all extracted text blocks

        Returns:
            List of FontSummary objects sorted by count (descending)
        """
        font_data: dict[str, dict] = defaultdict(lambda: {"count": 0, "pages": set()})

        for block in text_blocks:
            font_data[block.font]["count"] += 1
            font_data[block.font]["pages"].add(block.page)

        summaries = [
            FontSummary(
                name=name,
                count=data["count"],
                pages=sorted(data["pages"]),
            )
            for name, data in font_data.items()
        ]

        # Sort by count descending
        summaries.sort(key=lambda x: x.count, reverse=True)

        return summaries


def extract_document(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Convenience function to extract content from a PDF.

    Creates an extractor, performs extraction, and closes the document.

    Args:
        file_bytes: Raw PDF file bytes
        filename: Original filename for metadata

    Returns:
        ExtractionResult containing all extracted data
    """
    extractor = PDFExtractor(file_bytes, filename)
    try:
        return extractor.extract()
    finally:
        extractor.close()
