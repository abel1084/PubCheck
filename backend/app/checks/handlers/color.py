"""
Color check handler for color matching validation.

Handles requirements:
- TYPO-*: Heading color checks
- Any rule requiring color matching with tolerance

Checks text colors against expected values with per-channel tolerance.
"""
from typing import List, Set

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import check_color_match


def check_color(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute color check against extraction data.

    Checks text colors against expected hex value with per-channel tolerance.
    Targets specific text types based on rule name (headings, body, etc.).

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (hex, tolerance)

    Returns:
        List of issues found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    expected_hex = exp.get("hex", "")
    tolerance = exp.get("tolerance", 5)

    if not expected_hex:
        return issues

    # Determine which text to check based on rule name
    rule_name_lower = rule.name.lower()

    if "heading" in rule_name_lower or "title" in rule_name_lower:
        issues.extend(_check_heading_colors(extraction, rule, expected_hex, tolerance))
    elif "body" in rule_name_lower:
        issues.extend(_check_body_colors(extraction, rule, expected_hex, tolerance))
    else:
        # Check all text
        issues.extend(_check_all_colors(extraction, rule, expected_hex, tolerance))

    return issues


def _check_heading_colors(
    extraction: ExtractionResult,
    rule: Rule,
    expected_hex: str,
    tolerance: int
) -> List[CheckIssue]:
    """
    Check heading text colors.

    Headings are identified by larger font sizes (>14pt typically).

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected_hex: Expected color as hex string
        tolerance: Per-channel tolerance

    Returns:
        List of issues for incorrect heading colors
    """
    issues: List[CheckIssue] = []
    failing_pages: Set[int] = set()
    wrong_colors: Set[str] = set()

    for block in extraction.text_blocks:
        # Headings are typically larger text (> 14pt)
        if block.size < 14:
            continue

        page_num = block.page + 1  # 1-indexed

        if not check_color_match(block.color, expected_hex, tolerance):
            failing_pages.add(page_num)
            wrong_colors.add(_int_to_hex(block.color))

    if failing_pages:
        colors_str = ", ".join(sorted(wrong_colors)[:3])
        if len(wrong_colors) > 3:
            colors_str += f" (+{len(wrong_colors) - 3} more)"

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Heading color mismatch on {len(failing_pages)} page(s)",
            expected=expected_hex,
            actual=colors_str,
            pages=sorted(failing_pages),
            how_to_fix=f"Update heading colors to {expected_hex}",
        ))

    return issues


def _check_body_colors(
    extraction: ExtractionResult,
    rule: Rule,
    expected_hex: str,
    tolerance: int
) -> List[CheckIssue]:
    """
    Check body text colors.

    Body text is identified by smaller font sizes (<= 14pt).

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected_hex: Expected color as hex string
        tolerance: Per-channel tolerance

    Returns:
        List of issues for incorrect body text colors
    """
    issues: List[CheckIssue] = []
    failing_pages: Set[int] = set()
    wrong_colors: Set[str] = set()

    for block in extraction.text_blocks:
        # Body text is typically smaller (<=14pt)
        if block.size > 14:
            continue

        page_num = block.page + 1  # 1-indexed

        if not check_color_match(block.color, expected_hex, tolerance):
            failing_pages.add(page_num)
            wrong_colors.add(_int_to_hex(block.color))

    if failing_pages:
        colors_str = ", ".join(sorted(wrong_colors)[:3])
        if len(wrong_colors) > 3:
            colors_str += f" (+{len(wrong_colors) - 3} more)"

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Body text color mismatch on {len(failing_pages)} page(s)",
            expected=expected_hex,
            actual=colors_str,
            pages=sorted(failing_pages),
            how_to_fix=f"Update body text colors to {expected_hex}",
        ))

    return issues


def _check_all_colors(
    extraction: ExtractionResult,
    rule: Rule,
    expected_hex: str,
    tolerance: int
) -> List[CheckIssue]:
    """
    Check all text colors.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected_hex: Expected color as hex string
        tolerance: Per-channel tolerance

    Returns:
        List of issues for incorrect colors
    """
    issues: List[CheckIssue] = []
    failing_pages: Set[int] = set()
    wrong_colors: Set[str] = set()

    for block in extraction.text_blocks:
        page_num = block.page + 1  # 1-indexed

        if not check_color_match(block.color, expected_hex, tolerance):
            failing_pages.add(page_num)
            wrong_colors.add(_int_to_hex(block.color))

    if failing_pages:
        colors_str = ", ".join(sorted(wrong_colors)[:3])
        if len(wrong_colors) > 3:
            colors_str += f" (+{len(wrong_colors) - 3} more)"

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Text color mismatch on {len(failing_pages)} page(s)",
            expected=expected_hex,
            actual=colors_str,
            pages=sorted(failing_pages),
            how_to_fix=f"Update text colors to {expected_hex}",
        ))

    return issues


def _int_to_hex(color_int: int) -> str:
    """
    Convert RGB integer to hex string.

    Args:
        color_int: Color as integer (0xRRGGBB)

    Returns:
        Hex color string (e.g., "#00AEEF")
    """
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"
