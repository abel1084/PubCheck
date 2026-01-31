"""
PubCheck - Rasterized PDF Detection
Detects if a PDF is rasterized/flattened (image-only, no text layer)
"""
import pymupdf


def is_rasterized_pdf(doc: pymupdf.Document, threshold: float = 0.95) -> tuple[bool, str]:
    """
    Detect if PDF is rasterized/flattened (image-only, no text layer).

    A page is considered rasterized if:
    - Has very little extractable text (< 10 chars)
    - AND has image(s) covering > threshold (95%) of page area

    PDF is considered rasterized if > 50% of pages are rasterized.

    Args:
        doc: PyMuPDF document object
        threshold: Minimum image coverage ratio to consider a page rasterized (default 0.95)

    Returns:
        Tuple of (is_rasterized, reason)
        - is_rasterized: True if PDF appears to be rasterized/scanned
        - reason: Human-readable explanation (empty if not rasterized)
    """
    total_pages = doc.page_count
    rasterized_pages = 0

    for page_num in range(total_pages):
        page = doc[page_num]
        page_rect = page.rect
        page_area = abs(page_rect)

        if page_area <= 0:
            # Skip empty page area (shouldn't happen but safety check)
            continue

        # Check 1: Try to extract text
        text = page.get_text("text").strip()
        has_text = len(text) > 10  # Minimal text threshold

        if has_text:
            # If page has meaningful text, it's not rasterized
            continue

        # Check 2: Check image coverage
        images = page.get_images(full=True)

        if not images:
            # No text and no images - empty page, not rasterized
            continue

        total_image_coverage = 0.0

        for img_info in images:
            xref = img_info[0]
            try:
                for rect in page.get_image_rects(xref):
                    # Calculate intersection with page rect
                    intersection = rect & page_rect
                    if intersection.is_empty:
                        continue
                    total_image_coverage += abs(intersection)
            except Exception:
                # Skip images with issues getting rects
                continue

        coverage_ratio = total_image_coverage / page_area

        # Page is rasterized if: little/no text AND high image coverage
        if coverage_ratio >= threshold:
            rasterized_pages += 1

    # Consider PDF rasterized if majority of pages are
    is_rasterized = rasterized_pages > total_pages * 0.5

    if is_rasterized:
        reason = f"{rasterized_pages}/{total_pages} pages appear to be scanned images without text layers"
    else:
        reason = ""

    return is_rasterized, reason
