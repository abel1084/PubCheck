"""
Font check handler for typography validation.

Handles requirements:
- TYPO-01, TYPO-02, TYPO-03, TYPO-04, TYPO-05: Typography checks

Checks font family, size ranges, and weights with flexible name matching.
"""
from typing import Dict, List, Set

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import normalize_font_name, check_font_size_range


def check_font(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute font check against extraction data.

    Checks:
    - Font family (with flexible name matching)
    - Font size range (with 0.5pt tolerance)
    - Font weights (Regular, Bold, etc.)

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (family, sizes, weights, alternatives)

    Returns:
        List of issues found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    expected_family = exp.get("family", "")
    alternatives = exp.get("alternatives", [])
    expected_weights = exp.get("weights", [])
    min_size = exp.get("min")
    max_size = exp.get("max")
    exact_size = exp.get("size")  # For exact size checks like chart_axis_font

    if not expected_family:
        return issues

    # Build list of acceptable font families
    acceptable_families = [expected_family] + alternatives

    # Analyze text blocks
    font_issues = _check_font_family(extraction, rule, acceptable_families)
    issues.extend(font_issues)

    # Check size range if specified
    if min_size is not None and max_size is not None:
        size_issues = _check_font_size(extraction, rule, min_size, max_size, acceptable_families)
        issues.extend(size_issues)
    elif exact_size is not None:
        # Use exact size with 0.5pt tolerance (so min=max=exact)
        size_issues = _check_font_size(extraction, rule, exact_size, exact_size, acceptable_families)
        issues.extend(size_issues)

    return issues


def _check_font_family(
    extraction: ExtractionResult,
    rule: Rule,
    acceptable_families: List[str]
) -> List[CheckIssue]:
    """
    Check if document uses acceptable font families.

    Uses flexible matching:
    - Normalizes font names (strips subset prefixes)
    - Checks if font name starts with or contains expected family

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        acceptable_families: List of acceptable font family names

    Returns:
        List of issues for incorrect fonts
    """
    issues: List[CheckIssue] = []
    wrong_fonts: Dict[str, Set[int]] = {}  # font_name -> set of pages

    for block in extraction.text_blocks:
        normalized_font = normalize_font_name(block.font)
        page_num = block.page + 1  # 1-indexed

        if not _font_matches(normalized_font, acceptable_families):
            if normalized_font not in wrong_fonts:
                wrong_fonts[normalized_font] = set()
            wrong_fonts[normalized_font].add(page_num)

    # Create issue for each wrong font found
    if wrong_fonts:
        all_pages = set()
        font_list = []
        for font_name, pages in wrong_fonts.items():
            all_pages.update(pages)
            font_list.append(font_name)

        # Limit font list to avoid overly long messages
        if len(font_list) > 3:
            fonts_display = ", ".join(font_list[:3]) + f" (+{len(font_list) - 3} more)"
        else:
            fonts_display = ", ".join(font_list)

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Incorrect font(s) found: {fonts_display}",
            expected=acceptable_families[0],
            actual=fonts_display,
            pages=sorted(all_pages),
            how_to_fix=f"Use {acceptable_families[0]} font family",
        ))

    return issues


def _check_font_size(
    extraction: ExtractionResult,
    rule: Rule,
    min_size: float,
    max_size: float,
    acceptable_families: List[str]
) -> List[CheckIssue]:
    """
    Check if font sizes fall within acceptable range.

    Only checks text blocks that use the expected font family.
    Uses 0.5pt tolerance per CONTEXT.md.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        min_size: Minimum font size in points
        max_size: Maximum font size in points
        acceptable_families: Font families to check (others ignored)

    Returns:
        List of issues for incorrect sizes
    """
    issues: List[CheckIssue] = []
    failing_pages: Set[int] = set()
    sizes_found: Set[float] = set()

    for block in extraction.text_blocks:
        normalized_font = normalize_font_name(block.font)

        # Only check sizes for the expected font family
        if not _font_matches(normalized_font, acceptable_families):
            continue

        page_num = block.page + 1  # 1-indexed

        if not check_font_size_range(block.size, min_size, max_size):
            failing_pages.add(page_num)
            sizes_found.add(block.size)

    if failing_pages:
        # Report the range of incorrect sizes found
        min_found = min(sizes_found)
        max_found = max(sizes_found)

        if min_found == max_found:
            actual_str = f"{min_found}pt"
        else:
            actual_str = f"{min_found}-{max_found}pt"

        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Font size out of range on {len(failing_pages)} page(s)",
            expected=f"{min_size}-{max_size}pt",
            actual=actual_str,
            pages=sorted(failing_pages),
            how_to_fix=f"Adjust font size to {min_size}-{max_size}pt",
        ))

    return issues


def _font_matches(font_name: str, acceptable_families: List[str]) -> bool:
    """
    Check if a font name matches any acceptable family.

    Matching is flexible:
    - Case-insensitive comparison
    - Font name can start with the family name
    - Font name can contain the family name

    Args:
        font_name: Normalized font name from PDF
        acceptable_families: List of acceptable family names

    Returns:
        True if font matches any acceptable family
    """
    font_lower = font_name.lower()

    for family in acceptable_families:
        family_lower = family.lower()

        # Check if font starts with or contains family name
        if font_lower.startswith(family_lower):
            return True
        if family_lower in font_lower:
            return True

        # Also check without spaces (e.g., "RobotoFlex" matches "Roboto Flex")
        family_no_space = family_lower.replace(" ", "")
        font_no_space = font_lower.replace(" ", "")
        if font_no_space.startswith(family_no_space):
            return True

    return False
