"""
Image processing utilities for PDF extraction.
Handles image extraction with DPI calculation.
"""
import pymupdf

from app.models.extraction import ImageInfo


def extract_images(doc: pymupdf.Document, page: pymupdf.Page, page_num: int) -> list[ImageInfo]:
    """
    Extract images with DPI and colorspace from a PDF page.

    DPI is calculated from the rendered size on page, not embedded metadata,
    as embedded DPI values are often incorrect.

    Formula: DPI = (image_pixels / display_points) * 72

    Args:
        doc: PyMuPDF document object (needed for extract_image)
        page: PyMuPDF page object
        page_num: Page number (0-indexed)

    Returns:
        List of ImageInfo objects with dimensions, DPI, colorspace, and bbox
    """
    images: list[ImageInfo] = []

    # Get all images on page with full info
    # Returns: (xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, referencer)
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        smask = img_info[1]  # Transparency mask xref (0 if none)

        # Extract image data for dimensions and colorspace
        try:
            img_data = doc.extract_image(xref)
        except Exception:
            # Skip images that can't be extracted
            continue

        if not img_data:
            continue

        img_width = img_data.get("width", 0)
        img_height = img_data.get("height", 0)
        # Colorspace can be int (component count) or string - normalize to string
        cs = img_data.get("colorspace", "unknown")
        if isinstance(cs, int):
            # Map component count to colorspace name
            colorspace = {1: "Gray", 3: "RGB", 4: "CMYK"}.get(cs, f"Unknown({cs})")
        else:
            colorspace = cs or "unknown"

        # Get image bounding boxes on page for DPI calculation
        # An image can appear multiple times on a page at different sizes
        try:
            img_rects = page.get_image_rects(xref)
        except Exception:
            img_rects = []

        for rect in img_rects:
            # Calculate rendered DPI from bbox
            # DPI = (image_pixels / display_points) * 72
            bbox_width = rect.width if hasattr(rect, 'width') else (rect.x1 - rect.x0)
            bbox_height = rect.height if hasattr(rect, 'height') else (rect.y1 - rect.y0)

            dpi_x = (img_width / bbox_width) * 72 if bbox_width > 0 else 0
            dpi_y = (img_height / bbox_height) * 72 if bbox_height > 0 else 0

            # Get bbox coordinates
            if hasattr(rect, 'x0'):
                bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
            else:
                bbox = tuple(rect)

            # Calculate dimensions in mm from rendered size (points / 72 * 25.4)
            width_mm = bbox_width / 72 * 25.4
            height_mm = bbox_height / 72 * 25.4

            images.append(ImageInfo(
                xref=xref,
                width=img_width,
                height=img_height,
                colorspace=colorspace,
                dpi_x=round(dpi_x, 1),
                dpi_y=round(dpi_y, 1),
                bbox=(
                    round(bbox[0], 2),
                    round(bbox[1], 2),
                    round(bbox[2], 2),
                    round(bbox[3], 2),
                ),
                page=page_num,
                has_mask=smask != 0,
                width_mm=round(width_mm, 1),
                height_mm=round(height_mm, 1),
            ))

    return images
