"""
PDF page to base64 image renderer using PyMuPDF.
Uses webptools for reliable WebP compression (bundles its own binaries).
"""
import base64
import io
import logging
import os
import tempfile

import pymupdf
from PIL import Image
from webptools import cwebp


logger = logging.getLogger(__name__)

# Gemini API limit is 1MB per part. Base64 adds ~33% overhead.
# So raw bytes must be under ~750KB to stay under 1MB after encoding.
MAX_IMAGE_BYTES = 700 * 1024  # 700KB raw = ~930KB base64


def _compress_to_webp(img: Image.Image, quality: int) -> bytes:
    """Compress PIL Image to WebP using webptools (has bundled binaries)."""
    # Create temp file paths (don't keep files open - Windows locking issue)
    import uuid
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex[:8]
    tmp_png_path = os.path.join(temp_dir, f"pubcheck_{unique_id}.png")
    tmp_webp_path = os.path.join(temp_dir, f"pubcheck_{unique_id}.webp")

    try:
        # Save as PNG
        img.save(tmp_png_path, 'PNG')

        # Convert to WebP using webptools
        result = cwebp(input_image=tmp_png_path, output_image=tmp_webp_path, option=f"-q {quality}")

        if result.get('exit_code', 1) != 0:
            raise RuntimeError(f"cwebp failed: {result}")

        # Read result
        with open(tmp_webp_path, 'rb') as f:
            webp_bytes = f.read()

        return webp_bytes
    finally:
        # Cleanup temp files
        if os.path.exists(tmp_png_path):
            os.unlink(tmp_png_path)
        if os.path.exists(tmp_webp_path):
            os.unlink(tmp_webp_path)


def _compress_to_jpeg(img: Image.Image, quality: int) -> bytes:
    """Compress PIL Image to JPEG."""
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def _try_compress(img: Image.Image) -> tuple[bytes, str]:
    """
    Try to compress image under MAX_IMAGE_BYTES.
    Uses WebP (smaller files), falls back to JPEG if WebP fails.
    Returns (image_bytes, mime_type).
    """
    # Try WebP first (typically 30% smaller than JPEG)
    for quality in [80, 65, 50, 35, 20]:
        try:
            img_bytes = _compress_to_webp(img, quality)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"WebP compressed to {len(img_bytes)//1024}KB at q={quality}")
                return img_bytes, "image/webp"
        except Exception as e:
            logger.warning(f"WebP compression failed: {e}, trying JPEG")
            break

    # Fall back to JPEG
    for quality in [80, 65, 50, 35, 20]:
        img_bytes = _compress_to_jpeg(img, quality)
        if len(img_bytes) <= MAX_IMAGE_BYTES:
            logger.info(f"JPEG compressed to {len(img_bytes)//1024}KB at q={quality}")
            return img_bytes, "image/jpeg"

    # If still too large, resize the image
    for scale in [0.8, 0.65, 0.5, 0.4, 0.3]:
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)

        # Try WebP for resized
        try:
            img_bytes = _compress_to_webp(resized, 60)
            if len(img_bytes) <= MAX_IMAGE_BYTES:
                logger.info(f"WebP resized to {scale*100:.0f}% = {len(img_bytes)//1024}KB")
                return img_bytes, "image/webp"
        except:
            pass

        # Try JPEG for resized
        img_bytes = _compress_to_jpeg(resized, 60)
        if len(img_bytes) <= MAX_IMAGE_BYTES:
            logger.info(f"JPEG resized to {scale*100:.0f}% = {len(img_bytes)//1024}KB")
            return img_bytes, "image/jpeg"

    # Last resort: very small image
    new_size = (int(img.width * 0.25), int(img.height * 0.25))
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    img_bytes = _compress_to_jpeg(resized, 50)
    logger.warning(f"Last resort: 25% size = {len(img_bytes)//1024}KB")
    return img_bytes, "image/jpeg"


def render_page_to_base64(pdf_path: str, page_num: int, dpi: int = 72) -> tuple[str, str]:
    """
    Render a PDF page to base64-encoded image.

    Uses WebP for smallest size (via webptools), falls back to JPEG.
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

        # Compress with WebP/JPEG
        img_bytes, mime_type = _try_compress(img)

        return base64.standard_b64encode(img_bytes).decode("utf-8"), mime_type

    finally:
        if doc:
            doc.close()
