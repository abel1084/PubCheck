"""
Position check handler for logo placement validation.

Handles requirements:
- COVR-01: UNEP logo position/size
- COVR-04: Partner logo placement

Uses positional heuristics. Full logo detection requires Phase 4 AI.
"""
from typing import List, Optional, Tuple

from app.models.extraction import ExtractionResult, ImageInfo
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import points_to_mm, check_logo_size


def check_position(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute position check against extraction data.

    Checks:
    - Image position (top-right, top-left, etc.)
    - Image size (minimum size in mm)

    For cover checks, focuses on page 0 (first page).

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (position, min_size_mm, target_size_mm)

    Returns:
        List of issues found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    position = exp.get("position", "")
    min_size_mm = exp.get("min_size_mm")
    target_size_mm = exp.get("target_size_mm")

    if not position:
        return issues

    # For cover checks, look at first page only
    cover_images = [img for img in extraction.images if img.page == 0]

    if not cover_images:
        # No images on cover - might be an issue depending on rule
        if "logo" in rule.name.lower():
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message="No images found on cover page",
                expected=f"Logo in {position} position",
                actual="No images",
                pages=[1],
                how_to_fix="Add logo to cover page",
            ))
        return issues

    # Find images in expected position
    positioned_image = _find_image_in_position(cover_images, position, extraction)

    if positioned_image is None:
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"No image found in {position} position",
            expected=f"Image in {position}",
            actual="Image in different position",
            pages=[1],
            how_to_fix=f"Move logo to {position} corner",
        ))
        return issues

    # Check size if specified
    if min_size_mm is not None:
        size_issue = _check_image_size(positioned_image, rule, min_size_mm)
        if size_issue:
            issues.append(size_issue)

    return issues


def _find_image_in_position(
    images: List[ImageInfo],
    position: str,
    extraction: ExtractionResult
) -> Optional[ImageInfo]:
    """
    Find an image in the expected position.

    Position interpretation:
    - "top-right": High on page (low y), right side (high x)
    - "top-left": High on page (low y), left side (low x)
    - "bottom-right": Low on page (high y), right side (high x)
    - "bottom-left": Low on page (high y), left side (low x)

    Note: PDF coordinates have origin at bottom-left in points,
    but PyMuPDF typically uses top-left origin.

    Args:
        images: List of images on the page
        position: Expected position string
        extraction: Full extraction data (for page dimensions)

    Returns:
        Image in expected position, or None if not found
    """
    if not images:
        return None

    # Get page dimensions from margins (using first page)
    # We estimate page width/height from margin data
    # For now, use typical A4 dimensions as fallback: 595 x 842 points
    page_width = 595.0
    page_height = 842.0

    # Parse position
    is_top = "top" in position.lower()
    is_right = "right" in position.lower()

    # Define quadrant thresholds
    # For "top", y should be in upper third (low y values if top-left origin)
    # For "right", x should be in right half
    y_threshold = page_height / 3  # Upper third
    x_threshold = page_width / 2   # Right half

    best_match = None
    best_score = -1

    for img in images:
        # Image center
        center_x = (img.bbox[0] + img.bbox[2]) / 2
        center_y = (img.bbox[1] + img.bbox[3]) / 2

        # Score based on position match
        score = 0

        if is_top:
            # Lower y = higher on page (assuming top-left origin)
            if center_y < y_threshold:
                score += 1
        else:
            if center_y > page_height - y_threshold:
                score += 1

        if is_right:
            if center_x > x_threshold:
                score += 1
        else:
            if center_x < x_threshold:
                score += 1

        if score > best_score:
            best_score = score
            best_match = img

    # Only return if we found a good match (score 2 = both coordinates match)
    if best_score >= 2:
        return best_match

    return None


def _check_image_size(
    image: ImageInfo,
    rule: Rule,
    min_size_mm: float
) -> Optional[CheckIssue]:
    """
    Check if image meets minimum size requirement.

    Uses 1mm tolerance per CONTEXT.md.

    Args:
        image: The image to check
        rule: The rule configuration
        min_size_mm: Minimum size in mm

    Returns:
        Issue if image too small, None otherwise
    """
    # Calculate image dimensions in mm
    width_pt = image.bbox[2] - image.bbox[0]
    height_pt = image.bbox[3] - image.bbox[1]

    width_mm = points_to_mm(width_pt)
    height_mm = points_to_mm(height_pt)

    # Use the smaller dimension for size check
    actual_size_mm = min(width_mm, height_mm)

    if not check_logo_size(actual_size_mm, min_size_mm):
        return CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message="Image too small",
            expected=f"{min_size_mm}mm minimum",
            actual=f"{actual_size_mm:.1f}mm",
            pages=[image.page + 1],
            how_to_fix=f"Increase image size to at least {min_size_mm}mm",
        )

    return None
