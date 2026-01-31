"""
PDF page to base64 image renderer using PyMuPDF.
Uses WebP compression to stay under Gemini's 1MB limit.
"""
import base64
import io

import pymupdf
from PIL import Image


# Gemini API limit is 1MB per part, leave margin for base64 overhead
MAX_IMAGE_BYTES = 900 * 1024  # 900KB to be safe


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> str:
    """
    Render a PDF page to base64-encoded WebP.

    Uses WebP compression for smallest file size while maintaining quality.
    Falls back to lower quality/resolution if needed.

    Args:
        pdf_path: Path to the PDF file
        page_num: 0-indexed page number
        dpi: Resolution for rendering (default 72 for screen)

    Returns:
        Base64-encoded WebP image data
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

        # Convert to PIL Image for WebP compression
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Try progressively lower quality until under size limit
        for quality in [85, 70, 55, 40]:
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=quality, method=6)
            webp_bytes = buffer.getvalue()

            if len(webp_bytes) <= MAX_IMAGE_BYTES:
                return base64.standard_b64encode(webp_bytes).decode("utf-8")

        # If still too large, resize the image
        scale = 0.7
        while scale > 0.3:
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            resized.save(buffer, format="WEBP", quality=60, method=6)
            webp_bytes = buffer.getvalue()

            if len(webp_bytes) <= MAX_IMAGE_BYTES:
                return base64.standard_b64encode(webp_bytes).decode("utf-8")

            scale -= 0.1

        # Last resort: very small image
        new_size = (int(img.width * 0.3), int(img.height * 0.3))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format="WEBP", quality=50, method=6)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    finally:
        if doc:
            doc.close()
