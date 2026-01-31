"""
Range check handler for margin and DPI checks.

Handles check types:
- MRGN-01, MRGN-02, MRGN-03, MRGN-04: Margin checks (mm)
- IMAG-01: DPI checks

Uses minimum-only logic for margins (flag when content too close to edge).
Uses 2.5% tolerance for DPI checks.
"""
from typing import List

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import points_to_mm, check_margin_minimum, check_dpi_minimum


def check_range(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute range check against extraction data.

    For unit="mm": Check margins (minimum only)
    For unit="dpi": Check image DPI (with 2.5% tolerance)
    For unit="pt": Return empty (font sizes handled by font handler)

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (min, max, unit)

    Returns:
        List of issues found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    unit = exp.get("unit", "")
    min_val = exp.get("min")
    max_val = exp.get("max")

    if unit == "mm":
        # Margin check - minimum only per CONTEXT.md
        issues.extend(_check_margins(extraction, rule, min_val))
    elif unit == "dpi":
        # DPI check with 2.5% tolerance
        issues.extend(_check_dpi(extraction, rule, min_val))
    elif unit == "pt":
        # Font size checks are handled by font handler
        # This allows range checks to be used for font sizes in YAML
        # but delegated appropriately
        pass

    return issues


def _check_margins(
    extraction: ExtractionResult,
    rule: Rule,
    min_mm: float
) -> List[CheckIssue]:
    """
    Check page margins against minimum requirement.

    Determines which margin to check based on rule name keywords:
    - "left" or "right" -> check left/right (outside/inside)
    - "top" -> check top
    - "bottom" -> check bottom
    - "left/right" -> check both left and right

    Per CONTEXT.md: Check minimum only - flag when content too close to edge.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        min_mm: Minimum margin in mm

    Returns:
        List of issues for pages with insufficient margins
    """
    issues: List[CheckIssue] = []
    failing_pages: List[int] = []
    min_actual_mm = float('inf')

    # Determine which margins to check based on rule name
    rule_name_lower = rule.name.lower()

    for page_margin in extraction.margins:
        page_num = page_margin.page + 1  # 1-indexed for display

        margins_to_check = []

        if "left" in rule_name_lower and "right" in rule_name_lower:
            # Check both left and right
            margins_to_check = [
                ("left", page_margin.left),
                ("right", page_margin.right),
            ]
        elif "top" in rule_name_lower and "bottom" in rule_name_lower:
            # Check both top and bottom
            margins_to_check = [
                ("top", page_margin.top),
                ("bottom", page_margin.bottom),
            ]
        elif "left" in rule_name_lower:
            margins_to_check = [("left", page_margin.left)]
        elif "right" in rule_name_lower:
            margins_to_check = [("right", page_margin.right)]
        elif "top" in rule_name_lower:
            margins_to_check = [("top", page_margin.top)]
        elif "bottom" in rule_name_lower:
            margins_to_check = [("bottom", page_margin.bottom)]
        elif "inside" in rule_name_lower:
            margins_to_check = [("inside", page_margin.inside)]
        elif "outside" in rule_name_lower:
            margins_to_check = [("outside", page_margin.outside)]
        else:
            # Default: check all outer margins
            margins_to_check = [
                ("top", page_margin.top),
                ("bottom", page_margin.bottom),
                ("left", page_margin.left),
                ("right", page_margin.right),
            ]

        for margin_name, margin_pt in margins_to_check:
            actual_mm = points_to_mm(margin_pt)

            if not check_margin_minimum(actual_mm, min_mm):
                if page_num not in failing_pages:
                    failing_pages.append(page_num)
                if actual_mm < min_actual_mm:
                    min_actual_mm = actual_mm

    if failing_pages:
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Margin too small on {len(failing_pages)} page(s)",
            expected=f"{min_mm:.1f}mm minimum",
            actual=f"{min_actual_mm:.1f}mm",
            pages=sorted(failing_pages),
            how_to_fix="Adjust page layout to increase margin",
        ))

    return issues


def _check_dpi(
    extraction: ExtractionResult,
    rule: Rule,
    min_dpi: float
) -> List[CheckIssue]:
    """
    Check image DPI against minimum requirement.

    Per CONTEXT.md: 2.5% tolerance below minimum (293 DPI passes for 300 min).

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        min_dpi: Minimum required DPI

    Returns:
        List of issues for low-DPI images
    """
    issues: List[CheckIssue] = []
    failing_pages: List[int] = []
    lowest_dpi = float('inf')

    for image in extraction.images:
        # Use the lower of x and y DPI
        actual_dpi = min(image.dpi_x, image.dpi_y)
        page_num = image.page + 1  # 1-indexed for display

        if not check_dpi_minimum(actual_dpi, min_dpi):
            if page_num not in failing_pages:
                failing_pages.append(page_num)
            if actual_dpi < lowest_dpi:
                lowest_dpi = actual_dpi

    if failing_pages:
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Low resolution image(s) on {len(failing_pages)} page(s)",
            expected=f"{min_dpi:.0f} DPI minimum",
            actual=f"{lowest_dpi:.0f} DPI",
            pages=sorted(failing_pages),
            how_to_fix="Replace with higher resolution image",
        ))

    return issues
