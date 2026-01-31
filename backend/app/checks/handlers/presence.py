"""
Presence check handler for element existence validation.

Handles requirements:
- REQD-06: SDG icons count
- COVR-02: Title presence
- COVR-03: Subtitle presence
- IMAG-02: Color space validation (allowed_values check)

Also supports checking if specific elements exist in the document.
"""
from typing import List, Set

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import points_to_mm


def check_presence(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute presence check against extraction data.

    Supports:
    - required: bool (element must/must not exist)
    - count: min/max count for element
    - allowed_values: list of allowed values (for color space checks)

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (required, count, allowed_values)

    Returns:
        List of issues found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    required = exp.get("required", False)
    count_spec = exp.get("count")
    allowed_values = exp.get("allowed_values")

    # Handle color space validation (allowed_values check)
    if allowed_values:
        issues.extend(_check_color_space(extraction, rule, allowed_values))
        return issues

    # Handle SDG icon counting
    if "sdg" in rule.name.lower() or "icon" in rule.name.lower():
        issues.extend(_check_sdg_icons(extraction, rule, count_spec))
        return issues

    # Handle general presence check (page numbers, etc.)
    if required:
        issues.extend(_check_element_required(extraction, rule))

    return issues


def _check_color_space(
    extraction: ExtractionResult,
    rule: Rule,
    allowed_values: List[str]
) -> List[CheckIssue]:
    """
    Check if image color spaces are in allowed list.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        allowed_values: List of allowed color space values

    Returns:
        List of issues for images with invalid color space
    """
    issues: List[CheckIssue] = []
    failing_pages: Set[int] = set()
    invalid_colorspaces: Set[str] = set()

    # Normalize allowed values for comparison
    allowed_normalized = [v.lower() for v in allowed_values]

    for image in extraction.images:
        colorspace = image.colorspace
        page_num = image.page + 1  # 1-indexed

        # Normalize for comparison
        if colorspace.lower() not in allowed_normalized:
            failing_pages.add(page_num)
            invalid_colorspaces.add(colorspace)

    if failing_pages:
        colorspaces_str = ", ".join(sorted(invalid_colorspaces))
        allowed_str = ", ".join(allowed_values)

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Invalid color space found: {colorspaces_str}",
            expected=f"One of: {allowed_str}",
            actual=colorspaces_str,
            pages=sorted(failing_pages),
            how_to_fix="Convert images to RGB or CMYK color space",
        ))

    return issues


def _check_sdg_icons(
    extraction: ExtractionResult,
    rule: Rule,
    count_spec: dict
) -> List[CheckIssue]:
    """
    Check SDG icon count on last page.

    SDG icons are typically small square images on the back cover.
    This is a heuristic check - full SDG detection requires Phase 4 AI.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        count_spec: Count specification (min, max)

    Returns:
        List of issues for incorrect SDG icon count
    """
    issues: List[CheckIssue] = []

    if not count_spec:
        return issues

    min_count = count_spec.get("min", 1)
    max_count = count_spec.get("max", 17)  # There are 17 SDGs

    # Find last page
    if not extraction.margins:
        return issues

    last_page = max(m.page for m in extraction.margins)

    # Count likely SDG icon candidates on last page
    # SDG icons are typically small (15-25mm) square images
    sdg_candidates = 0

    for image in extraction.images:
        if image.page != last_page:
            continue

        # Calculate dimensions in mm
        width_pt = image.bbox[2] - image.bbox[0]
        height_pt = image.bbox[3] - image.bbox[1]
        width_mm = points_to_mm(width_pt)
        height_mm = points_to_mm(height_pt)

        # Check if roughly square (aspect ratio 0.8-1.2)
        if width_mm > 0 and height_mm > 0:
            aspect = width_mm / height_mm
            if 0.8 <= aspect <= 1.2:
                # Check if in typical SDG icon size range
                if 10 <= width_mm <= 30 and 10 <= height_mm <= 30:
                    sdg_candidates += 1

    if sdg_candidates < min_count:
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Insufficient SDG icon candidates on back cover",
            expected=f"{min_count}-{max_count} icons",
            actual=f"{sdg_candidates} candidates found",
            pages=[last_page + 1],
            how_to_fix="Add SDG icons to back cover",
        ))
    elif sdg_candidates > max_count:
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Too many SDG icon candidates on back cover",
            expected=f"{min_count}-{max_count} icons",
            actual=f"{sdg_candidates} candidates found",
            pages=[last_page + 1],
            how_to_fix="Reduce number of SDG icons to allowed range",
        ))

    return issues


def _check_element_required(
    extraction: ExtractionResult,
    rule: Rule
) -> List[CheckIssue]:
    """
    Check if a required element exists.

    For page numbers, checks if any text blocks appear to be page numbers.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration

    Returns:
        List of issues for missing required elements
    """
    issues: List[CheckIssue] = []

    rule_name_lower = rule.name.lower()

    if "page" in rule_name_lower and "number" in rule_name_lower:
        # Check for page numbers
        # Page numbers are typically small numbers at top or bottom of pages
        has_page_numbers = _detect_page_numbers(extraction)

        if not has_page_numbers:
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message="Page numbers not detected",
                expected="Page numbers on pages",
                actual="No page numbers found",
                pages=[],
                how_to_fix="Add page numbers to document",
            ))

    return issues


def _detect_page_numbers(extraction: ExtractionResult) -> bool:
    """
    Detect if document has page numbers.

    Heuristic: Look for small text blocks at top or bottom of pages
    that contain numbers matching page sequence.

    Args:
        extraction: The extracted PDF data

    Returns:
        True if page numbers appear to exist
    """
    # Group text blocks by page
    pages_with_numbers = set()

    for block in extraction.text_blocks:
        text = block.text.strip()

        # Page numbers are typically 1-3 digits
        if text.isdigit() and len(text) <= 3:
            # Check if at top or bottom of page (using bbox y coordinate)
            # Typical page number positions: y < 50pt (top) or y > 750pt (bottom for A4)
            y = block.bbox[1]  # top of text block
            if y < 60 or y > 700:
                pages_with_numbers.add(block.page)

    # If at least half the pages have detected page numbers, consider it present
    total_pages = len(extraction.margins) if extraction.margins else 1
    if len(pages_with_numbers) >= total_pages / 2:
        return True

    return False
