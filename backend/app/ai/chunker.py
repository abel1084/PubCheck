"""
Document chunking and compression utilities for large PDF review.

Provides two strategies for handling large documents:
1. Compression: Reduce image quality/DPI for AI review (preferred)
2. Chunking: Split into overlapping chunks (fallback)
"""
import gc
import logging
from io import BytesIO
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


# Compression settings for AI review (don't need print quality)
AI_REVIEW_DPI = 150  # 150 DPI is plenty for visual inspection
AI_REVIEW_JPEG_QUALITY = 70  # Good balance of quality vs size
TARGET_SIZE_MB = 18  # Target size under 20MB limit

from app.models.extraction import (
    DocumentMetadata,
    ExtractionResult,
    FontSummary,
    ImageInfo,
    PageMargins,
    TextBlock,
)


def compress_pdf_for_ai(
    pdf_bytes: bytes,
    target_size_mb: float = TARGET_SIZE_MB,
    min_dpi: int = 72,
    max_dpi: int = AI_REVIEW_DPI,
) -> Optional[bytes]:
    """
    Compress PDF by rendering pages as images at reduced DPI.

    For AI visual review, we don't need print-quality images.
    This renders each page at a lower DPI and creates a new image-based PDF.

    Args:
        pdf_bytes: Original PDF bytes
        target_size_mb: Target file size in MB
        min_dpi: Minimum DPI to try (won't go below this)
        max_dpi: Starting DPI to try

    Returns:
        Compressed PDF bytes, or None if compression failed/not needed
    """
    original_size = len(pdf_bytes)
    original_mb = original_size / 1024 / 1024
    target_bytes = target_size_mb * 1024 * 1024

    # Don't compress if already under target
    if original_size <= target_bytes:
        logger.info(f"PDF already under target ({original_mb:.1f}MB <= {target_size_mb}MB)")
        return None

    logger.info(f"Compressing PDF: {original_mb:.1f}MB -> target {target_size_mb}MB")

    src_doc = None
    try:
        src_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = src_doc.page_count

        # Binary search for optimal DPI
        dpi = max_dpi
        best_result = None

        while dpi >= min_dpi:
            logger.info(f"Trying DPI {dpi}...")
            new_doc = fitz.open()

            for page_num in range(page_count):
                page = src_doc[page_num]
                # Render page as pixmap at target DPI
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # Convert to JPEG bytes for smaller size
                img_bytes = pix.tobytes("jpeg", jpg_quality=AI_REVIEW_JPEG_QUALITY)
                pix = None  # Free pixmap immediately (~2-3MB each)

                # Create new page from image
                img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
                rect = img_doc[0].rect
                new_page = new_doc.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=img_bytes)
                img_doc.close()
                img_bytes = None  # Free JPEG bytes

            # Check size
            buffer = BytesIO()
            new_doc.save(buffer, deflate=True)
            compressed_size = buffer.tell()
            new_doc.close()

            logger.info(f"DPI {dpi}: {compressed_size/1024/1024:.1f}MB")

            if compressed_size <= target_bytes:
                buffer.seek(0)
                best_result = buffer.read()
                buffer.close()
                reduction = 100 * (1 - compressed_size / original_size)
                logger.info(
                    f"Compression successful: {original_mb:.1f}MB -> "
                    f"{compressed_size/1024/1024:.1f}MB ({reduction:.0f}% reduction) at {dpi} DPI"
                )
                return best_result

            # Didn't fit — close buffer and force GC before next DPI attempt
            buffer.close()
            gc.collect()

            # Try lower DPI
            dpi = dpi - 25 if dpi > 100 else dpi - 10

        logger.warning(f"Could not compress to target size even at {min_dpi} DPI")
        return None

    except Exception as e:
        logger.error(f"Compression failed: {e}")
        return None

    finally:
        if src_doc:
            src_doc.close()


def needs_compression(pdf_bytes: bytes, threshold_mb: float = 20.0) -> bool:
    """Check if PDF needs compression before AI review."""
    return len(pdf_bytes) > threshold_mb * 1024 * 1024


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

    Creates a NEW PDF document and copies only the specified pages,
    which ensures only the resources needed by those pages are included.

    Args:
        pdf_bytes: Original PDF as bytes
        start: Start page (0-indexed, inclusive)
        end: End page (0-indexed, exclusive)

    Returns:
        New PDF bytes containing only pages [start, end)
    """
    original_size = len(pdf_bytes)
    logger.info(
        f"extract_page_range called: pages {start}-{end}, "
        f"original size: {original_size/1024/1024:.1f}MB"
    )

    src_doc = None
    new_doc = None
    try:
        src_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        original_pages = src_doc.page_count
        logger.info(f"Opened PDF: {original_pages} pages")

        # Validate range
        start = max(0, start)
        end = min(end, src_doc.page_count)

        if start >= end:
            raise ValueError(f"Invalid page range: start={start}, end={end}")

        # Create NEW document and insert pages (copies only needed resources)
        new_doc = fitz.open()
        new_doc.insert_pdf(src_doc, from_page=start, to_page=end - 1)
        logger.info(f"Copied {new_doc.page_count} pages to new document")

        # Write with aggressive compression
        buffer = BytesIO()
        new_doc.save(buffer, garbage=4, deflate=True, clean=True)
        buffer.seek(0)
        chunk_bytes = buffer.read()
        buffer.close()

        reduction = 100 * (1 - len(chunk_bytes) / original_size)
        logger.info(
            f"Extracted pages {start}-{end}: "
            f"{len(chunk_bytes)/1024/1024:.1f}MB "
            f"(from {original_size/1024/1024:.1f}MB, {reduction:.0f}% reduction)"
        )
        return chunk_bytes

    finally:
        if src_doc:
            src_doc.close()
        if new_doc:
            new_doc.close()


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
