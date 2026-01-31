"""
PDF page to base64 image renderer using PyMuPDF.
Uses JPEG compression to stay under Gemini's 1MB limit.
"""
import base64
import io
import logging

import pymupdf
from PIL import Image


logger = logging.getLogger(__name__)

# Gemini API limit is 1MB per part. Base64 adds ~33% overhead.
MAX_IMAGE_BYTES = 700 * 1024  # 700KB raw = ~930KB base64


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> tuple[str, str]:
    """
    Render a PDF page to base64-encoded JPEG.

    Args:
        pdf_path: Path to the PDF file
        page_num: 0-indexed page number
        dpi: Resolution for rendering (default 72)

    Returns:
        Tuple of (base64_image_data, mime_type)
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]

        # Calculate zoom factor for desired DPI
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)

        # Render page to pixmap
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        logger.info(f"Page {page_num}: rendered {pix.width}x{pix.height}")

        # Convert to PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Try progressively lower quality until under size limit
        for quality in [75, 60, 45, 30, 15]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            jpeg_bytes = buffer.getvalue()

            if len(jpeg_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"Page {page_num}: JPEG {len(jpeg_bytes)//1024}KB at q={quality}")
                return base64.standard_b64encode(jpeg_bytes).decode("utf-8"), "image/jpeg"

        # Resize if still too large
        for scale in [0.75, 0.5, 0.35, 0.25]:
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=50)
            jpeg_bytes = buffer.getvalue()

            if len(jpeg_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"Page {page_num}: JPEG resized {scale*100:.0f}% = {len(jpeg_bytes)//1024}KB")
                return base64.standard_b64encode(jpeg_bytes).decode("utf-8"), "image/jpeg"

        # Last resort
        new_size = (int(img.width * 0.2), int(img.height * 0.2))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=40)
        jpeg_bytes = buffer.getvalue()
        logger.warning(f"Page {page_num}: last resort {len(jpeg_bytes)//1024}KB")
        return base64.standard_b64encode(jpeg_bytes).decode("utf-8"), "image/jpeg"

    finally:
        if doc:
            doc.close()
