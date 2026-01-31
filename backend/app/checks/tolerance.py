"""
Centralized tolerance calculation utilities for compliance checking.
Follows CONTEXT.md decisions for all tolerance thresholds.
"""
import re
import unicodedata


def points_to_mm(points: float) -> float:
    """
    Convert points to millimeters.

    1 inch = 72 points = 25.4 mm
    Therefore: 1 point = 25.4/72 mm = ~0.3528 mm

    Args:
        points: Value in points

    Returns:
        Value in millimeters
    """
    return points * 25.4 / 72


def mm_to_points(mm: float) -> float:
    """
    Convert millimeters to points.

    1 mm = 72/25.4 points = ~2.8346 points

    Args:
        mm: Value in millimeters

    Returns:
        Value in points
    """
    return mm * 72 / 25.4


def check_margin_minimum(actual_mm: float, min_mm: float) -> bool:
    """
    Check if margin meets minimum requirement.

    Per CONTEXT.md: "Check minimum only - flag when content too close to edge,
    not when margins are larger"

    Args:
        actual_mm: Actual margin in mm
        min_mm: Minimum required margin in mm

    Returns:
        True if actual >= min (margin is acceptable)
    """
    return actual_mm >= min_mm


def check_font_size_range(
    actual_pt: float,
    min_pt: float,
    max_pt: float,
    tolerance: float = 0.5
) -> bool:
    """
    Check if font size falls within acceptable range.

    Per CONTEXT.md: "+/-0.5pt tolerance"

    Args:
        actual_pt: Actual font size in points
        min_pt: Minimum font size
        max_pt: Maximum font size
        tolerance: Tolerance in points (default 0.5)

    Returns:
        True if actual is within range (with tolerance)
    """
    return (min_pt - tolerance) <= actual_pt <= (max_pt + tolerance)


def check_dpi_minimum(
    actual_dpi: float,
    min_dpi: float,
    tolerance_pct: float = 2.5
) -> bool:
    """
    Check if image DPI meets minimum requirement.

    Per CONTEXT.md: "2.5% tolerance below minimum (293 DPI passes for 300 minimum)"

    Args:
        actual_dpi: Actual image DPI
        min_dpi: Minimum required DPI
        tolerance_pct: Tolerance percentage below minimum (default 2.5%)

    Returns:
        True if DPI is acceptable (at or above min with tolerance)
    """
    effective_min = min_dpi * (1 - tolerance_pct / 100)
    return actual_dpi >= effective_min


def check_logo_size(
    actual_mm: float,
    min_mm: float,
    tolerance: float = 1.0
) -> bool:
    """
    Check if logo size meets minimum requirement.

    Per CONTEXT.md: "+/-1mm tolerance around minimum"

    Args:
        actual_mm: Actual logo dimension in mm
        min_mm: Minimum required size in mm
        tolerance: Tolerance in mm (default 1.0)

    Returns:
        True if actual >= (min - tolerance)
    """
    return actual_mm >= (min_mm - tolerance)


def normalize_font_name(font_name: str) -> str:
    """
    Strip subset prefix from font name.

    PDF font subsetting adds a 6-character prefix followed by '+' to identify
    embedded subsets. For example: BAAAAA+Arial -> Arial

    Per CONTEXT.md: "Normalize subset prefixes ('ABCDEF+Roboto' matches 'Roboto')"

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


def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text for pattern matching.

    Per CONTEXT.md:
    - "Case-insensitive" -> use casefold()
    - "Normalize (multiple spaces/newlines treated as single space)"

    Also applies Unicode normalization (NFKC) to handle ligatures and
    other Unicode variations.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text (casefolded, whitespace collapsed, Unicode normalized)
    """
    # Unicode normalize (NFKC decomposes and recomposes for compatibility)
    normalized = unicodedata.normalize("NFKC", text)
    # Collapse all whitespace (spaces, tabs, newlines) to single space
    normalized = re.sub(r"\s+", " ", normalized)
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    # Casefold for case-insensitive comparison
    normalized = normalized.casefold()
    return normalized


def check_color_match(
    actual_rgb: int,
    expected_hex: str,
    tolerance: int = 5
) -> bool:
    """
    Check if a color matches expected value within tolerance.

    Per CONTEXT.md: "Allow near-matches (small delta per channel)"

    Args:
        actual_rgb: Actual color as RGB integer (0xRRGGBB)
        expected_hex: Expected color as hex string (e.g., "#00AEEF")
        tolerance: Maximum delta per channel (default 5)

    Returns:
        True if all channels are within tolerance
    """
    # Parse expected hex color
    hex_clean = expected_hex.lstrip("#")
    expected_r = int(hex_clean[0:2], 16)
    expected_g = int(hex_clean[2:4], 16)
    expected_b = int(hex_clean[4:6], 16)

    # Extract actual RGB components
    actual_r = (actual_rgb >> 16) & 0xFF
    actual_g = (actual_rgb >> 8) & 0xFF
    actual_b = actual_rgb & 0xFF

    # Check each channel within tolerance
    return (
        abs(actual_r - expected_r) <= tolerance and
        abs(actual_g - expected_g) <= tolerance and
        abs(actual_b - expected_b) <= tolerance
    )
