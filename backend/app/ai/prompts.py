"""
Prompt templates and checklist generation for AI analysis.
"""
from typing import Any, Dict

from app.config.models import Template


SYSTEM_PROMPT = """You are a document compliance analyst for UNEP publications. Your task is to analyze page images against a design checklist and report any issues found.

Return your analysis as a JSON object with this structure:
{
  "findings": [
    {
      "check_name": "Name of the check",
      "passed": true/false,
      "confidence": "high" | "medium" | "low",
      "message": "Brief description of finding",
      "reasoning": "Explanation (only for non-obvious findings)",
      "location": "Descriptive location (e.g., 'top-right corner')",
      "suggestion": "Fix suggestion (only for failures)"
    }
  ]
}

Confidence calibration:
- "high": Clear violation or clear compliance, no ambiguity
- "medium": Likely issue but visual inspection should confirm
- "low": Possible issue, requires human judgment

Guidelines:
- Only include findings for checks that are relevant to this page
- Include reasoning only for non-obvious findings (skip for clear violations like "No ISBN")
- Include suggestion only for failures
- Use descriptive locations, not coordinates
- Be concise in messages (one sentence)
- Return empty findings array if page passes all relevant checks"""


def generate_checklist(template: Template) -> str:
    """
    Generate a simplified checklist from rule template.

    Takes merged rules from RuleService and creates a bullet-point
    checklist grouped by category.

    Args:
        template: Merged Template with rules

    Returns:
        Markdown-formatted checklist string
    """
    lines = []

    for cat_id, category in template.categories.items():
        # Only include categories with enabled rules
        enabled_rules = [
            (rule_id, rule)
            for rule_id, rule in category.rules.items()
            if rule.enabled
        ]

        if not enabled_rules:
            continue

        lines.append(f"## {category.name}")

        for rule_id, rule in enabled_rules:
            # Build requirement description from expected values
            expected = rule.expected.dict()
            requirement_parts = []

            # Handle different check types
            if rule.check_type == "position":
                if expected.get("position"):
                    requirement_parts.append(f"Position: {expected['position']}")
                if expected.get("min_size_mm"):
                    requirement_parts.append(f"Minimum size: {expected['min_size_mm']}mm")

            elif rule.check_type == "range":
                if expected.get("min") is not None:
                    requirement_parts.append(f"Minimum: {expected['min']}")
                if expected.get("max") is not None:
                    requirement_parts.append(f"Maximum: {expected['max']}")
                if expected.get("unit"):
                    requirement_parts[-1] += expected['unit']

            elif rule.check_type == "font":
                if expected.get("font_family"):
                    requirement_parts.append(f"Font: {expected['font_family']}")
                if expected.get("min_size") and expected.get("max_size"):
                    requirement_parts.append(f"Size: {expected['min_size']}-{expected['max_size']}pt")

            elif rule.check_type == "regex":
                if expected.get("pattern"):
                    requirement_parts.append(f"Pattern: {expected['pattern']}")

            elif rule.check_type == "presence":
                if expected.get("required"):
                    requirement_parts.append("Required")
                if expected.get("location"):
                    requirement_parts.append(f"Location: {expected['location']}")

            elif rule.check_type == "color":
                if expected.get("hex"):
                    requirement_parts.append(f"Color: {expected['hex']}")

            # Build the checklist line
            if requirement_parts:
                requirement_str = ", ".join(requirement_parts)
                lines.append(f"- {rule.name}: {requirement_str}")
            else:
                lines.append(f"- {rule.name}: {rule.description}")

        lines.append("")  # Blank line between categories

    return "\n".join(lines)


def build_analysis_prompt(checklist: str, extraction_summary: str) -> str:
    """
    Build the analysis prompt for a page.

    Combines the checklist with page-specific context from extraction.

    Args:
        checklist: Markdown checklist from generate_checklist
        extraction_summary: Page-specific extraction data summary

    Returns:
        Complete prompt for Claude API
    """
    return f"""Analyze this page image against the following design checklist.

## Checklist
{checklist}

## Page Context
{extraction_summary}

Review the page image and report any compliance issues found. Return your findings as JSON.
If no issues are found for this page, return an empty findings array."""
