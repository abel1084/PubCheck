"""
PDF page to base64 image renderer using PyMuPDF.
Compresses images to stay under Gemini's 1MB limit.
"""
import base64
import io
import logging

import pymupdf
from PIL import Image


logger = logging.getLogger(__name__)

# Gemini API limit is 1MB per part. Base64 adds ~33% overhead.
# So raw bytes must be under ~750KB to stay under 1MB after encoding.
MAX_IMAGE_BYTES = 700 * 1024  # 700KB raw = ~930KB base64


def _save_image(img: Image.Image, format: str, quality: int) -> bytes:
    """Save image to bytes with given format and quality."""
    buffer = io.BytesIO()
    if format == "WEBP":
        img.save(buffer, format="WEBP", quality=quality, method=4)
    else:
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def _try_compress(img: Image.Image, use_webp: bool) -> tuple[bytes, str]:
    """
    Try to compress image under MAX_IMAGE_BYTES.
    Returns (image_bytes, mime_type).
    """
    fmt = "WEBP" if use_webp else "JPEG"
    mime = "image/webp" if use_webp else "image/jpeg"

    # Try progressively lower quality
    for quality in [80, 65, 50, 35, 20]:
        try:
            img_bytes = _save_image(img, fmt, quality)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.debug(f"Compressed to {len(img_bytes)//1024}KB at quality={quality}")
                return img_bytes, mime
        except Exception as e:
            if use_webp:
                # WebP failed, fall back to JPEG
                logger.warning(f"WebP failed: {e}, falling back to JPEG")
                return _try_compress(img, use_webp=False)
            raise

    # If still too large, resize the image
    for scale in [0.8, 0.65, 0.5, 0.4, 0.3]:
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)

        try:
            img_bytes = _save_image(resized, fmt, 50)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.debug(f"Resized to {scale*100:.0f}% = {len(img_bytes)//1024}KB")
                return img_bytes, mime
        except Exception as e:
            if use_webp:
                logger.warning(f"WebP resize failed: {e}, falling back to JPEG")
                return _try_compress(img, use_webp=False)
            raise

    # Last resort: very small image
    new_size = (int(img.width * 0.25), int(img.height * 0.25))
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    img_bytes = _save_image(resized, fmt, 40)
    logger.warning(f"Last resort: 25% size = {len(img_bytes)//1024}KB")
    return img_bytes, mime


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> tuple[str, str]:
    """
    Render a PDF page to base64-encoded image.

    Uses WebP if available, falls back to JPEG.
    Automatically compresses/resizes to stay under API size limits.

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

        # Render page to pixmap (no alpha for smaller size)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        logger.debug(f"Rendered page {page_num} at {pix.width}x{pix.height}")

        # Convert to PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Try WebP first (smaller), fall back to JPEG
        img_bytes, mime_type = _try_compress(img, use_webp=True)

        return base64.standard_b64encode(img_bytes).decode("utf-8"), mime_type

    finally:
        if doc:
            doc.close()
