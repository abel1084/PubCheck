"""
Prompts for AI-powered document review.
Produces collegial, helpful feedback organized by priority sections.
"""

SYSTEM_PROMPT_TEMPLATE = '''You are a helpful colleague reviewing UNEP publications for design compliance. Your review should read like feedback from an experienced designer who wants the document to succeed.

## Review Style
- Be collegial and constructive: "The logo looks a bit small at 18mm - spec asks for 20mm minimum"
- Cite measurements when relevant: sizes, margins, DPI values
- Use honest hedging when uncertain: "This might be intentional, but..."
- No formal confidence scores - express uncertainty naturally in prose

## Response Structure
Organize your review into these sections, using markdown headers:

### Overview
Brief 2-3 sentence summary of the document's compliance state. Mention the document type and overall impression.

### Needs Attention
Issues that should be fixed before publication. Group related issues naturally.
Each issue should explain what's wrong and suggest a fix.
If there are no issues, write "Everything looks good!" and skip to Looking Good.

### Looking Good
Specific things the document does well. Acknowledge good design work.
Mention 2-3 positive observations.

### Suggestions
Minor improvements that would enhance the document but aren't requirements.
Optional enhancements or stylistic suggestions.

## Output Format

First, provide your prose review using the section headers above (Overview, Needs Attention, Looking Good, Suggestions).

Then, at the very end of your response, provide a JSON block with structured issues for the comment system:

```json
{{
  "issues": [
    {{
      "id": "issue-1",
      "category": "needs_attention",
      "title": "Brief issue title",
      "description": "Full description with measurements",
      "pages": [1, 2]
    }}
  ]
}}
```

Rules for the JSON block:
- Include ALL issues from both "Needs Attention" and "Suggestions" sections
- Use category "needs_attention" for items from Needs Attention section
- Use category "suggestion" for items from Suggestions section
- Use sequential IDs: "issue-1", "issue-2", etc.
- Include page numbers where the issue appears (use [1] if document-wide)
- The JSON block MUST come AFTER all prose content
- Do NOT include items from "Looking Good" in the JSON (those are positive observations)

## Common Pitfalls to Avoid in Your Analysis
- Full-bleed images are intentional design, not margin violations
- Decorative elements (thin lines, bullets, icons under ~5mm) don't need DPI checks
- Small accent images may intentionally use lower resolution
- Headers/footers have different margin rules than body content
- Font variations within a family (Roboto vs Roboto Condensed) are acceptable
- If logo dimensions seem implausible (>50mm or <5mm width), note uncertainty rather than stating false measurements
- Logo measurements in extraction are in millimeters (mm) - use directly, don't convert
- Position coordinates are in points from top-left - don't confuse position with size

## What You're Checking
You'll receive:
1. The original PDF document (you can see all pages)
2. Extracted measurements as JSON (fonts, images, margins, text blocks)
3. Document type with confidence score - validate this matches the actual document

{rules_context}
'''


def build_system_prompt(rules_context: str) -> str:
    """
    Build system prompt with rules context injected.

    Args:
        rules_context: Markdown rules for the document type

    Returns:
        Complete system prompt
    """
    return SYSTEM_PROMPT_TEMPLATE.format(rules_context=rules_context)


def build_user_prompt(
    extraction_json: str,
    document_type: str,
    confidence: float,
    output_format: str = "digital",
    dpi_min: int = 72,
) -> str:
    """
    Build user prompt with extraction data and document type.

    Args:
        extraction_json: JSON string of ExtractionResult
        document_type: Detected document type
        confidence: Detection confidence (0-1)
        output_format: Output format (digital, print, both)
        dpi_min: Minimum DPI requirement for the output format

    Returns:
        User prompt for document review
    """
    confidence_note = ""
    if confidence < 0.8:
        confidence_note = f"\n(Please verify this is actually a {document_type} - detection confidence is only {confidence:.0%})"

    # Format label for user-friendly display
    format_labels = {
        "digital": "Digital only",
        "print": "Print",
        "both": "Print + Digital",
    }
    format_label = format_labels.get(output_format, output_format)

    return f'''Please review this {document_type} for design compliance.

Document type confidence: {confidence:.0%}{confidence_note}

## Output Format
Target output: {format_label}
**DPI requirement: {dpi_min} DPI minimum** for all significant images

When checking image resolution:
- Flag images below {dpi_min} DPI as needing attention
- Images at or above {dpi_min} DPI are acceptable
- Small decorative elements (under ~5mm) don't need DPI checks

## Extracted Measurements
The following JSON contains measurements extracted from the PDF. Use this data to verify specific values (font sizes, margins, DPI, etc.) but also visually inspect the document for issues the extraction might miss.

```json
{extraction_json}
```

Review the document and provide your assessment using the section structure from your instructions (Overview, Needs Attention, Looking Good, Suggestions).'''


def build_chain_chunk_prompt(
    extraction_json: str,
    document_type: str,
    confidence: float,
    output_format: str,
    dpi_min: int,
    chunk_start: int,  # 1-indexed actual page number
    chunk_end: int,    # 1-indexed actual page number (inclusive)
    is_first_chunk: bool,
    total_chunks: int,
    chunk_number: int,  # 1-indexed chunk number
    previous_issues_json: str | None = None,
) -> str:
    """
    Build user prompt for a sequential-chain chunked review.

    Each chunk receives the accumulated issue list from previous chunks and
    outputs the COMPLETE consolidated list (not just new issues). The AI
    merges, deduplicates, and updates page references as it goes.

    Args:
        extraction_json: JSON string of filtered ExtractionResult for this chunk
        document_type: Detected document type
        confidence: Detection confidence (0-1)
        output_format: Output format (digital, print, both)
        dpi_min: Minimum DPI requirement for the output format
        chunk_start: First page number in chunk (1-indexed)
        chunk_end: Last page number in chunk (1-indexed, inclusive)
        is_first_chunk: True if this is the first chunk (includes doc-wide checks)
        total_chunks: Total number of chunks in the document
        chunk_number: Current chunk number (1-indexed)
        previous_issues_json: JSON string of accumulated issues from prior chunks,
            or None for the first chunk

    Returns:
        User prompt for chunk review
    """
    confidence_note = ""
    if confidence < 0.8:
        confidence_note = f"\n(Please verify this is actually a {document_type} - detection confidence is only {confidence:.0%})"

    # Format label for user-friendly display
    format_labels = {
        "digital": "Digital only",
        "print": "Print",
        "both": "Print + Digital",
    }
    format_label = format_labels.get(output_format, output_format)

    # Chunk context header
    chunk_header = f"""You are reviewing **pages {chunk_start}-{chunk_end}** of a larger document (chunk {chunk_number} of {total_chunks}).

**IMPORTANT:** Page numbers in your findings should use the ACTUAL page numbers ({chunk_start}-{chunk_end}), not relative numbers starting from 1."""

    # First chunk vs continuation chunk instructions
    if is_first_chunk:
        chunk_instructions = """
This is the **FIRST** chunk. Include document-wide checks:
- ISBN, DOI, job number presence and format
- Copyright notice and disclaimer
- Colophon page elements
- Logo placement and sizing on cover/first pages"""
    else:
        prev_end = chunk_start - 1
        chunk_instructions = f"""
This is a **CONTINUATION** chunk (pages {chunk_start}-{chunk_end}).

## Previous Findings (Pages 1-{prev_end})
The following issues were found in earlier chunks. Your task:
- **KEEP** all issues that are still valid
- **UPDATE** page arrays if you find the same issue on new pages
- **MERGE** systematic issues into single entries (e.g. "margin issue on every page" → one entry)
- **REMOVE** issues that seem incorrect based on new context
- **ADD** any genuinely new issues found on pages {chunk_start}-{chunk_end}
- Output the **COMPLETE consolidated list** in the JSON block (not just new issues)

```json
{previous_issues_json}
```"""

    return f'''{chunk_header}
{chunk_instructions}

Please review this {document_type} for design compliance.

Document type confidence: {confidence:.0%}{confidence_note}

## Output Format
Target output: {format_label}
**DPI requirement: {dpi_min} DPI minimum** for all significant images

When checking image resolution:
- Flag images below {dpi_min} DPI as needing attention
- Images at or above {dpi_min} DPI are acceptable
- Small decorative elements (under ~5mm) don't need DPI checks

## Extracted Measurements (Pages {chunk_start}-{chunk_end} only)
The following JSON contains measurements extracted from the PDF for this chunk only. Use this data to verify specific values (font sizes, margins, DPI, etc.) but also visually inspect the document for issues the extraction might miss.

```json
{extraction_json}
```

Review the document and provide your assessment using the section structure from your instructions (Overview, Needs Attention, Looking Good, Suggestions).'''
