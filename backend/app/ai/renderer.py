"""
PDF page to base64 image renderer using PyMuPDF.
"""
import base64

import pymupdf


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> str:
    """
    Render a PDF page to base64-encoded PNG.

    Args:
        pdf_path: Path to the PDF file
        page_num: 0-indexed page number
        dpi: Resolution for rendering (default 72 for screen)

    Returns:
        Base64-encoded PNG image data
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]

        # Calculate zoom factor for desired DPI
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)

        # Render page to pixmap (no alpha for smaller size)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to PNG bytes
        png_bytes = pix.tobytes("png")

        # Encode to base64
        return base64.standard_b64encode(png_bytes).decode("utf-8")

    finally:
        if doc:
            doc.close()
