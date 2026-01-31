"""
Margin calculation utilities for PDF extraction.
Calculates page margins from content bounding boxes.
"""
import pymupdf

from app.models.extraction import PageMargins


def calculate_margins(page: pymupdf.Page, page_num: int) -> PageMargins:
    """
    Calculate margins from content bounding boxes.

    Finds the bounding box of all content (text and images) and calculates
    margins as the distance from content to page edges.

    Inside/outside margins are derived assuming standard book binding:
    - Odd pages (1, 3, 5...): inside = left, outside = right (right-hand pages)
    - Even pages (2, 4, 6...): inside = right, outside = left (left-hand pages)

    Args:
        page: PyMuPDF page object
        page_num: Page number (1-indexed for display)

    Returns:
        PageMargins with top, bottom, left, right, inside, outside values in points
    """
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    # Initialize with page bounds (will track min/max of content)
    min_x = page_width
    min_y = page_height
    max_x = 0.0
    max_y = 0.0

    has_content = False

    # Process text blocks
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        bbox = block.get("bbox")
        if bbox:
            has_content = True
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

    # Process images
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            for rect in page.get_image_rects(xref):
                has_content = True
                if hasattr(rect, 'x0'):
                    min_x = min(min_x, rect.x0)
                    min_y = min(min_y, rect.y0)
                    max_x = max(max_x, rect.x1)
                    max_y = max(max_y, rect.y1)
                else:
                    # Handle tuple-like rect
                    min_x = min(min_x, rect[0])
                    min_y = min(min_y, rect[1])
                    max_x = max(max_x, rect[2])
                    max_y = max(max_y, rect[3])
        except Exception:
            # Skip images with issues getting rects
            continue

    # If no content found, return zero margins
    if not has_content:
        return PageMargins(
            page=page_num,
            top=0.0,
            bottom=0.0,
            left=0.0,
            right=0.0,
            inside=0.0,
            outside=0.0,
        )

    # Calculate margins (in points, 72 points = 1 inch)
    left_margin = max(0.0, min_x)
    top_margin = max(0.0, min_y)
    right_margin = max(0.0, page_width - max_x)
    bottom_margin = max(0.0, page_height - max_y)

    # Determine inside/outside based on page position
    # For odd pages (1, 3, 5): inside = left (gutter side), right-hand page
    # For even pages (2, 4, 6): inside = right (gutter side), left-hand page
    is_odd_book_page = (page_num % 2) == 1  # 1-indexed, so 1, 3, 5 are odd book pages

    if is_odd_book_page:
        inside_margin = left_margin
        outside_margin = right_margin
    else:
        inside_margin = right_margin
        outside_margin = left_margin

    return PageMargins(
        page=page_num,
        top=round(top_margin, 2),
        bottom=round(bottom_margin, 2),
        left=round(left_margin, 2),
        right=round(right_margin, 2),
        inside=round(inside_margin, 2),
        outside=round(outside_margin, 2),
    )
