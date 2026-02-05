"""
Document chunking utilities for large PDF review.

Splits large documents into reviewable chunks with context overlap
to handle Gemini's token limits for documents >40 pages.
"""
from io import BytesIO
from typing import List, Tuple

import fitz  # PyMuPDF

from app.models.extraction import (
    DocumentMetadata,
    ExtractionResult,
    FontSummary,
    ImageInfo,
    PageMargins,
    TextBlock,
)


class DocumentChunker:
    """
    Manages chunking configuration and calculations for large document review.

    Constants are tuned for Gemini's 1M token context window with
    conservative margins for extraction JSON overhead.
    """

    # Pages per chunk - conservative for 1M token limit
    PAGES_PER_CHUNK = 35

    # Overlap pages between chunks for context continuity
    OVERLAP_PAGES = 2

    # Page count threshold to trigger chunking
    PAGE_THRESHOLD = 40

    # Maximum concurrent chunk reviews
    MAX_CONCURRENT = 2

    def needs_chunking(self, page_count: int) -> bool:
        """
        Determine if a document needs to be chunked.

        Args:
            page_count: Total number of pages in the document

        Returns:
            True if document exceeds PAGE_THRESHOLD
        """
        return page_count > self.PAGE_THRESHOLD

    def calculate_chunks(self, page_count: int) -> List[Tuple[int, int]]:
        """
        Calculate chunk ranges for a document.

        Args:
            page_count: Total number of pages in the document

        Returns:
            List of (start_page, end_page) tuples (0-indexed, end exclusive)
            Each chunk overlaps with the previous by OVERLAP_PAGES

        Example:
            105 pages -> [(0, 35), (33, 68), (66, 101), (99, 105)]
        """
        if page_count <= 0:
            return []

        chunks = []
        start = 0

        while start < page_count:
            end = min(start + self.PAGES_PER_CHUNK, page_count)
            chunks.append((start, end))

            # If this chunk reaches the end of the document, we're done
            if end >= page_count:
                break

            # Move start forward by chunk size minus overlap
            # This creates the overlap with the previous chunk
            next_start = end - self.OVERLAP_PAGES

            # Prevent infinite loop: ensure we always make progress
            if next_start <= start:
                break

            start = next_start

        return chunks


def extract_page_range(pdf_bytes: bytes, start: int, end: int) -> bytes:
    """
    Extract a subset of pages from a PDF document.

    Uses PyMuPDF's select() method to create a new PDF containing
    only the specified page range.

    Args:
        pdf_bytes: Original PDF as bytes
        start: Start page (0-indexed, inclusive)
        end: End page (0-indexed, exclusive)

    Returns:
        New PDF bytes containing only pages [start, end)
    """
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Validate range
        start = max(0, start)
        end = min(end, doc.page_count)

        if start >= end:
            raise ValueError(f"Invalid page range: start={start}, end={end}")

        # Select only the specified pages
        # select() expects a list of page indices to keep
        pages_to_keep = list(range(start, end))
        doc.select(pages_to_keep)

        # Write to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.read()

    finally:
        if doc:
            doc.close()


def filter_extraction_for_chunk(
    extraction: ExtractionResult,
    start_page: int,
    end_page: int,
) -> ExtractionResult:
    """
    Filter extraction data to only include items for a specific page range.

    Preserves ACTUAL page numbers in the filtered data (doesn't renumber
    to chunk-relative). This is important for AI prompts to reference
    correct page numbers in their findings.

    Args:
        extraction: Full document extraction result
        start_page: Start page (0-indexed, inclusive)
        end_page: End page (0-indexed, exclusive)

    Returns:
        New ExtractionResult with only data for pages [start_page, end_page)

    Note:
        Extraction data uses 1-indexed page numbers internally,
        so we filter for pages in range [start_page+1, end_page] inclusive.
    """
    # Convert 0-indexed range to 1-indexed for filtering
    page_min = start_page + 1
    page_max = end_page  # end_page is exclusive 0-indexed = inclusive 1-indexed

    def is_page_in_range(page: int) -> bool:
        """Check if 1-indexed page number is in the chunk range."""
        return page_min <= page <= page_max

    # Filter text blocks
    filtered_text_blocks = [
        tb for tb in extraction.text_blocks
        if is_page_in_range(tb.page)
    ]

    # Filter images
    filtered_images = [
        img for img in extraction.images
        if is_page_in_range(img.page)
    ]

    # Filter margins
    filtered_margins = [
        m for m in extraction.margins
        if is_page_in_range(m.page)
    ]

    # Keep fonts summary as-is (document-wide information)
    # This helps AI understand the full font palette even in chunks

    # Create new metadata with updated page count
    chunk_metadata = DocumentMetadata(
        filename=extraction.metadata.filename,
        page_count=end_page - start_page,  # Chunk size
        title=extraction.metadata.title,
        author=extraction.metadata.author,
        creation_date=extraction.metadata.creation_date,
        producer=extraction.metadata.producer,
        isbn=extraction.metadata.isbn,
        doi=extraction.metadata.doi,
        job_number=extraction.metadata.job_number,
    )

    return ExtractionResult(
        metadata=chunk_metadata,
        text_blocks=filtered_text_blocks,
        images=filtered_images,
        margins=filtered_margins,
        fonts=extraction.fonts,  # Keep full font summary
    )
