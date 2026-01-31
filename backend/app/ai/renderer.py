"""
PDF page to base64 image renderer using PyMuPDF.
Uses WebP compression via webptools for smallest file size.
"""
import base64
import io
import logging
import os
import tempfile
import uuid

import pymupdf
from PIL import Image
from webptools import cwebp


logger = logging.getLogger(__name__)

# Gemini API limit is 1MB per part. Base64 adds ~33% overhead.
MAX_IMAGE_BYTES = 700 * 1024  # 700KB raw = ~930KB base64


def _compress_to_webp(img: Image.Image, quality: int) -> bytes:
    """Compress PIL Image to WebP using webptools (bundled binaries)."""
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex[:8]
    tmp_png_path = os.path.join(temp_dir, f"pubcheck_{unique_id}.png")
    tmp_webp_path = os.path.join(temp_dir, f"pubcheck_{unique_id}.webp")

    try:
        # Save as PNG first
        img.save(tmp_png_path, 'PNG')

        # Convert to WebP
        result = cwebp(input_image=tmp_png_path, output_image=tmp_webp_path, option=f"-q {quality}")

        if result.get('exit_code', 1) != 0:
            raise RuntimeError(f"cwebp failed: {result}")

        with open(tmp_webp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(tmp_png_path):
            os.unlink(tmp_png_path)
        if os.path.exists(tmp_webp_path):
            os.unlink(tmp_webp_path)


def _compress_to_jpeg(img: Image.Image, quality: int) -> bytes:
    """Compress PIL Image to JPEG (fallback)."""
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> tuple[str, str]:
    """
    Render a PDF page to base64-encoded WebP image.

    Uses WebP for smallest size (~30% smaller than JPEG).
    Falls back to JPEG if WebP fails.

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

        # Render page to pixmap
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        logger.info(f"Page {page_num}: rendered {pix.width}x{pix.height}")

        # Try WebP first (smaller files)
        for quality in [80, 65, 50, 35, 20]:
            try:
                img_bytes = _compress_to_webp(img, quality)
                if len(img_bytes) <= MAX_IMAGE_BYTES:
                    logger.info(f"Page {page_num}: WebP {len(img_bytes)//1024}KB at q={quality}")
                    return base64.standard_b64encode(img_bytes).decode("utf-8"), "image/webp"
            except Exception as e:
                logger.warning(f"WebP failed: {e}, falling back to JPEG")
                break

        # Fall back to JPEG
        for quality in [75, 60, 45, 30, 15]:
            img_bytes = _compress_to_jpeg(img, quality)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"Page {page_num}: JPEG {len(img_bytes)//1024}KB at q={quality}")
                return base64.standard_b64encode(img_bytes).decode("utf-8"), "image/jpeg"

        # Resize if still too large
        for scale in [0.75, 0.5, 0.35, 0.25]:
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)

            # Try WebP for resized
            try:
                img_bytes = _compress_to_webp(resized, 60)
                if len(img_bytes) <= MAX_IMAGE_BYTES:
                    logger.info(f"Page {page_num}: WebP resized {scale*100:.0f}% = {len(img_bytes)//1024}KB")
                    return base64.standard_b64encode(img_bytes).decode("utf-8"), "image/webp"
            except:
                pass

            # Try JPEG for resized
            img_bytes = _compress_to_jpeg(resized, 50)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"Page {page_num}: JPEG resized {scale*100:.0f}% = {len(img_bytes)//1024}KB")
                return base64.standard_b64encode(img_bytes).decode("utf-8"), "image/jpeg"

        # Last resort
        new_size = (int(img.width * 0.2), int(img.height * 0.2))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        img_bytes = _compress_to_jpeg(resized, 40)
        logger.warning(f"Page {page_num}: last resort {len(img_bytes)//1024}KB")
        return base64.standard_b64encode(img_bytes).decode("utf-8"), "image/jpeg"

    finally:
        if doc:
            doc.close()
