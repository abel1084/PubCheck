"""
Text processing utilities for PDF extraction.
Handles font name normalization and text block extraction.
"""
import pymupdf

from app.models.extraction import TextBlock


def normalize_font_name(font_name: str) -> str:
    """
    Strip subset prefix from font name.

    PDF font subsetting adds a 6-character prefix followed by '+' to identify
    embedded subsets. For example: BAAAAA+Arial -> Arial

    Args:
        font_name: Raw font name from PDF

    Returns:
        Normalized font name without subset prefix
    """
    if "+" in font_name:
        prefix, name = font_name.split("+", 1)
        # Subset prefixes are exactly 6 uppercase letters
        if len(prefix) == 6 and prefix.isupper() and prefix.isalpha():
            return name
    return font_name


def decode_font_flags(flags: int) -> dict[str, bool]:
    """
    Decode font property flags from PDF span.

    Font flags are bit flags where:
    - 1 = superscript
    - 2 = italic
    - 4 = serif
    - 8 = monospace
    - 16 = bold

    Args:
        flags: Integer font flags from PDF span

    Returns:
        Dictionary with decoded flag values
    """
    return {
        "superscript": bool(flags & 1),
        "italic": bool(flags & 2),
        "serif": bool(flags & 4),
        "monospace": bool(flags & 8),
        "bold": bool(flags & 16),
    }


def is_bold_from_name(font_name: str) -> bool:
    """
    Check if font name indicates bold weight.

    Some PDFs don't set the bold flag correctly, so we also check
    the font name for common bold indicators.

    Args:
        font_name: Normalized font name

    Returns:
        True if font name suggests bold weight
    """
    bold_indicators = [
        "Bold", "Black", "Heavy", "ExtraBold", "SemiBold",
        "bold", "black", "heavy", "extrabold", "semibold",
        "-Bold", "-Black", "-Heavy",
    ]
    return any(indicator in font_name for indicator in bold_indicators)


def is_italic_from_name(font_name: str) -> bool:
    """
    Check if font name indicates italic style.

    Args:
        font_name: Normalized font name

    Returns:
        True if font name suggests italic style
    """
    italic_indicators = [
        "Italic", "Oblique", "Slanted",
        "italic", "oblique", "slanted",
        "-Italic", "-Oblique", "-It",
    ]
    return any(indicator in font_name for indicator in italic_indicators)


def extract_text_blocks(page: pymupdf.Page, page_num: int) -> list[TextBlock]:
    """
    Extract text blocks with full font info and coordinates from a PDF page.

    Uses get_text("dict", sort=True) for reading order, processes all spans
    in blocks/lines hierarchy.

    Args:
        page: PyMuPDF page object
        page_num: Page number (0-indexed)

    Returns:
        List of TextBlock objects with text, font, size, style, color, and bbox
    """
    text_blocks: list[TextBlock] = []

    # Get text with full formatting info, sorted for reading order
    data = page.get_text("dict", sort=True)

    for block in data.get("blocks", []):
        # Skip image blocks (type 1)
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")

                # Skip empty spans
                if not text.strip():
                    continue

                raw_font = span.get("font", "")
                font = normalize_font_name(raw_font)
                size = span.get("size", 0.0)
                flags = span.get("flags", 0)
                color = span.get("color", 0)
                bbox = span.get("bbox", (0.0, 0.0, 0.0, 0.0))

                # Decode font flags
                decoded = decode_font_flags(flags)

                # Check both flags and font name for bold/italic
                bold = decoded["bold"] or is_bold_from_name(font)
                italic = decoded["italic"] or is_italic_from_name(font)

                text_blocks.append(TextBlock(
                    text=text,
                    font=font,
                    size=round(size, 2),
                    bold=bold,
                    italic=italic,
                    color=color,
                    bbox=(
                        round(bbox[0], 2),
                        round(bbox[1], 2),
                        round(bbox[2], 2),
                        round(bbox[3], 2),
                    ),
                    page=page_num,
                ))

    return text_blocks
