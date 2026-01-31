"""
Regex check handler for required element validation.

Handles requirements:
- REQD-01: ISBN
- REQD-02: DOI
- REQD-03: Job number
- REQD-04: Disclaimer
- REQD-05: Copyright

Searches for patterns in full document text with normalization.
"""
import re
from typing import List

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import normalize_text_for_matching


def check_regex(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected
) -> List[CheckIssue]:
    """
    Execute regex pattern check against extraction data.

    Searches for pattern in full document text (all text blocks + metadata).
    Uses text normalization for flexible matching.

    Args:
        extraction: The extracted PDF data
        rule: The rule configuration
        expected: Expected values (pattern)

    Returns:
        List containing one issue if pattern not found, empty if found
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    pattern = exp.get("pattern", "")
    if not pattern:
        return issues

    # Build full document text
    document_text = _build_document_text(extraction)

    # Normalize text for matching
    normalized_text = normalize_text_for_matching(document_text)

    # Try to compile and match pattern
    try:
        # For case-insensitive matching, we use IGNORECASE flag
        # DOTALL allows . to match newlines in the normalized text
        regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        match = regex.search(normalized_text)

        if not match:
            # Also try original text in case pattern relies on specific casing
            match = regex.search(document_text)

        if not match:
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message="Required element not found",
                expected=f"Pattern: {pattern}",
                actual="Not found",
                pages=[],  # Element could be anywhere
                how_to_fix=_get_fix_hint(rule.name),
            ))
    except re.error as e:
        # Invalid regex pattern - return error issue
        issues.append(CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity="error",
            message=f"Invalid regex pattern: {str(e)}",
            expected=f"Valid pattern",
            actual=f"Pattern: {pattern}",
            pages=[],
        ))

    return issues


def _build_document_text(extraction: ExtractionResult) -> str:
    """
    Build searchable text from all document sources.

    Combines:
    - All text blocks from all pages
    - Metadata fields (ISBN, DOI, job number)

    Args:
        extraction: The extracted PDF data

    Returns:
        Combined document text for searching
    """
    parts = []

    # Add all text block content
    for block in extraction.text_blocks:
        parts.append(block.text)

    # Add metadata fields that might contain required elements
    metadata = extraction.metadata
    if metadata.isbn:
        parts.append(metadata.isbn)
    if metadata.doi:
        parts.append(metadata.doi)
    if metadata.job_number:
        parts.append(metadata.job_number)
    if metadata.title:
        parts.append(metadata.title)
    if metadata.author:
        parts.append(metadata.author)

    return " ".join(parts)


def _get_fix_hint(rule_name: str) -> str:
    """
    Get appropriate fix hint based on rule name.

    Args:
        rule_name: The rule name to get hint for

    Returns:
        Fix suggestion string
    """
    name_lower = rule_name.lower()

    if "isbn" in name_lower:
        return "Add ISBN number to the document"
    elif "doi" in name_lower:
        return "Add DOI reference to the document"
    elif "job" in name_lower or "number" in name_lower:
        return "Add job/reference number to the document"
    elif "disclaimer" in name_lower:
        return "Add required disclaimer text"
    elif "copyright" in name_lower:
        return "Add copyright notice"
    else:
        return "Add required element to document"
