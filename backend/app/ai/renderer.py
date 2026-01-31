"""
PDF page to base64 image renderer using PyMuPDF.
Uses JPEG compression to stay under Gemini's 1MB limit.
"""
import base64
import io

import pymupdf
from PIL import Image


# Gemini API limit is 1MB per part. Base64 adds ~33% overhead.
# So raw bytes must be under ~750KB to stay under 1MB after encoding.
MAX_IMAGE_BYTES = 700 * 1024  # 700KB raw = ~930KB base64


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> str:
    """
    Render a PDF page to base64-encoded JPEG.

    Uses JPEG compression to stay under API size limits.
    Falls back to lower quality/resolution if needed.

    Args:
        pdf_path: Path to the PDF file
        page_num: 0-indexed page number
        dpi: Resolution for rendering (default 72 for screen)

    Returns:
        Base64-encoded JPEG image data
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

        # Convert to PIL Image for JPEG compression
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Try progressively lower quality until under size limit
        for quality in [85, 70, 55, 40, 25]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            jpeg_bytes = buffer.getvalue()

            if len(jpeg_bytes) <= MAX_IMAGE_BYTES:
                return base64.standard_b64encode(jpeg_bytes).decode("utf-8")

        # If still too large, resize the image
        for scale in [0.75, 0.6, 0.5, 0.4, 0.3]:
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=50, optimize=True)
            jpeg_bytes = buffer.getvalue()

            if len(jpeg_bytes) <= MAX_IMAGE_BYTES:
                return base64.standard_b64encode(jpeg_bytes).decode("utf-8")

        # Last resort: very small image
        new_size = (int(img.width * 0.25), int(img.height * 0.25))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=40, optimize=True)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    finally:
        if doc:
            doc.close()
