"""
Document reviewer module.
Orchestrates AI document review by combining PDF, extraction, and rules context.
"""
import asyncio
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from app.models.extraction import ExtractionResult

from .chunker import DocumentChunker, extract_page_range, filter_extraction_for_chunk
from .client import get_ai_client
from .prompts import build_chunk_user_prompt, build_system_prompt, build_user_prompt


logger = logging.getLogger(__name__)

# Rules context directory
RULES_CONTEXT_DIR = Path(__file__).parent.parent / "config" / "rules_context"

# Map document type IDs to rules context files
RULES_CONTEXT_MAP = {
    "factsheet": "factsheet.md",
    "policy-brief": "brief.md",
    "issue-note": "brief.md",  # Uses same rules as brief
    "working-paper": "working_paper.md",
    "publication": "publication.md",
}


def deduplicate_issues(all_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate issues from chunk overlaps.

    Deduplicates by hashing (title + min_page + category).
    For duplicates, keeps the first occurrence.

    Args:
        all_issues: List of issue dicts from parsed JSON

    Returns:
        Deduplicated list of issues
    """
    seen = set()
    unique = []

    for issue in all_issues:
        # Create hash key from issue identity
        pages = issue.get("pages", [1])
        min_page = min(pages) if pages else 1
        key_parts = f"{issue.get('title', '')}|{min_page}|{issue.get('category', '')}"
        key = hashlib.md5(key_parts.encode()).hexdigest()

        if key not in seen:
            seen.add(key)
            unique.append(issue)

    return unique


def load_rules_context(document_type: str) -> str:
    """
    Load rules context markdown for document type.

    Args:
        document_type: Document type ID (factsheet, publication, etc.)

    Returns:
        Markdown rules context content

    Raises:
        FileNotFoundError: If rules file doesn't exist
    """
    filename = RULES_CONTEXT_MAP.get(document_type)
    if not filename:
        logger.warning(f"Unknown document type: {document_type}, using publication rules")
        filename = "publication.md"

    rules_path = RULES_CONTEXT_DIR / filename
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules context not found: {rules_path}")

    return rules_path.read_text(encoding="utf-8")


def parse_chunk_issues(content: str) -> List[Dict[str, Any]]:
    """
    Parse issues from chunk content JSON block.

    Args:
        content: Full AI response content

    Returns:
        List of issue dicts from JSON block, or empty list if parsing fails
    """
    json_match = re.search(r"```(?:json)?\s*\n(\{[\s\S]*?\})\s*\n```", content)
    if not json_match:
        return []
    try:
        parsed = json.loads(json_match.group(1))
        return parsed.get("issues", [])
    except json.JSONDecodeError:
        return []


def build_merged_review(
    chunk_contents: List[str],
    unique_issues: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    total_chunks: int,
) -> str:
    """
    Build merged review from chunk contents.

    Combines prose sections from all chunks and rebuilds the JSON block
    with deduplicated issues.

    Args:
        chunk_contents: List of content strings from each chunk
        unique_issues: Deduplicated list of issues
        errors: List of error dicts for failed chunks
        total_chunks: Total number of chunks

    Returns:
        Merged review content with combined sections and JSON block
    """
    # Extract sections from each chunk
    all_overview = []
    all_needs_attention = []
    all_looking_good = []
    all_suggestions = []

    for i, content in enumerate(chunk_contents):
        if not content:
            continue

        chunk_num = i + 1

        # Extract Overview section
        overview_match = re.search(
            r"###\s*Overview\s*\n([\s\S]*?)(?=###|\Z)", content, re.IGNORECASE
        )
        if overview_match:
            text = overview_match.group(1).strip()
            if text:
                all_overview.append(f"**Chunk {chunk_num}:** {text}")

        # Extract Needs Attention section
        needs_match = re.search(
            r"###\s*Needs\s*Attention\s*\n([\s\S]*?)(?=###|\Z)", content, re.IGNORECASE
        )
        if needs_match:
            text = needs_match.group(1).strip()
            if text and "everything looks good" not in text.lower():
                all_needs_attention.append(text)

        # Extract Looking Good section
        good_match = re.search(
            r"###\s*Looking\s*Good\s*\n([\s\S]*?)(?=###|\Z)", content, re.IGNORECASE
        )
        if good_match:
            text = good_match.group(1).strip()
            if text:
                all_looking_good.append(text)

        # Extract Suggestions section
        suggestions_match = re.search(
            r"###\s*Suggestions\s*\n([\s\S]*?)(?=###|```|\Z)", content, re.IGNORECASE
        )
        if suggestions_match:
            text = suggestions_match.group(1).strip()
            if text:
                all_suggestions.append(text)

    # Build merged content
    merged = []

    # Overview - summarize the chunked review
    merged.append("### Overview\n")
    if errors:
        merged.append(
            f"*This document was reviewed in {total_chunks} chunks. "
            f"{len(errors)} chunk(s) failed to process.*\n\n"
        )
    else:
        merged.append(
            f"*This document was reviewed in {total_chunks} chunks.*\n\n"
        )
    if all_overview:
        merged.append("\n\n".join(all_overview))
    merged.append("\n\n")

    # Needs Attention - combine all issues
    merged.append("### Needs Attention\n")
    if all_needs_attention:
        merged.append("\n\n".join(all_needs_attention))
    else:
        merged.append("Everything looks good!")
    merged.append("\n\n")

    # Looking Good - combine positive notes
    merged.append("### Looking Good\n")
    if all_looking_good:
        # Deduplicate similar positive observations
        merged.append("\n\n".join(all_looking_good[:3]))  # Limit to avoid repetition
    else:
        merged.append("Review completed.")
    merged.append("\n\n")

    # Suggestions - combine all suggestions
    merged.append("### Suggestions\n")
    if all_suggestions:
        merged.append("\n\n".join(all_suggestions))
    else:
        merged.append("No additional suggestions.")
    merged.append("\n\n")

    # Add JSON block with deduplicated issues
    if unique_issues:
        # Re-number issue IDs sequentially
        for idx, issue in enumerate(unique_issues, 1):
            issue["id"] = f"issue-{idx}"

        json_block = json.dumps({"issues": unique_issues}, indent=2)
        merged.append(f"```json\n{json_block}\n```")

    return "".join(merged)


async def review_document_chunked(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    confidence: float,
    output_format: str = "digital",
) -> AsyncGenerator[str, None]:
    """
    Review large document in chunks with parallel processing.

    Yields:
        JSON-encoded SSE events:
        - review_start: {"total_chunks": N, "message": "..."}
        - chunk_progress: {"chunk": N, "total": M, "pages": "X-Y", "status": "..."}
        - text: {"text": "chunk content..."}
        - complete: {"status": "complete"}
        - error: {"error": "...", "type": "..."}
    """
    chunker = DocumentChunker()
    chunks = chunker.calculate_chunks(extraction.metadata.page_count)
    total_chunks = len(chunks)

    # DPI requirements by output format
    DPI_REQUIREMENTS = {
        "digital": {"min": 72, "label": "Digital"},
        "print": {"min": 300, "label": "Print"},
        "both": {"min": 150, "label": "Print + Digital"},
    }
    dpi_info = DPI_REQUIREMENTS.get(output_format, DPI_REQUIREMENTS["digital"])

    # Load rules context
    rules_context = load_rules_context(document_type)
    system_prompt = build_system_prompt(rules_context)

    logger.info(
        f"Starting chunked review: {total_chunks} chunks, "
        f"{extraction.metadata.page_count} pages"
    )

    # Emit start event
    yield json.dumps({"event": "review_start", "total_chunks": total_chunks})

    semaphore = asyncio.Semaphore(chunker.MAX_CONCURRENT)
    all_content: List[str] = [""] * total_chunks  # Store content by chunk index
    all_issues: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    async def process_chunk(chunk_idx: int, start: int, end: int) -> tuple:
        """Process a single chunk and return (index, content, issues, error)."""
        async with semaphore:
            try:
                # 1-indexed page numbers for prompts
                actual_start = start + 1
                actual_end = end  # end is exclusive 0-indexed = inclusive 1-indexed

                logger.info(
                    f"Processing chunk {chunk_idx + 1}/{total_chunks}: "
                    f"pages {actual_start}-{actual_end}"
                )

                # Extract chunk PDF
                chunk_pdf = extract_page_range(pdf_bytes, start, end)

                # Filter extraction for this chunk
                chunk_extraction = filter_extraction_for_chunk(extraction, start, end)
                extraction_json = json.dumps(
                    chunk_extraction.dict(), indent=2, default=str
                )

                # Build chunk-specific prompt
                is_first = chunk_idx == 0
                user_prompt = build_chunk_user_prompt(
                    extraction_json=extraction_json,
                    document_type=document_type,
                    confidence=confidence,
                    output_format=output_format,
                    dpi_min=dpi_info["min"],
                    chunk_start=actual_start,
                    chunk_end=actual_end,
                    is_first_chunk=is_first,
                    total_chunks=total_chunks,
                    chunk_number=chunk_idx + 1,
                )

                # Stream from AI client
                client = get_ai_client()
                content_parts = []
                async for text in client.review_document_stream(
                    pdf_bytes=chunk_pdf,
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                ):
                    content_parts.append(text)

                content = "".join(content_parts)

                # Parse issues from this chunk's content
                chunk_issues = parse_chunk_issues(content)

                return (chunk_idx, content, chunk_issues, None)

            except Exception as e:
                logger.error(f"Chunk {chunk_idx + 1} failed: {e}")
                return (chunk_idx, "", [], str(e))

    # Create tasks for all chunks
    tasks = [process_chunk(i, start, end) for i, (start, end) in enumerate(chunks)]

    # Process as they complete
    for coro in asyncio.as_completed(tasks):
        chunk_idx, content, chunk_issues, error = await coro
        start, end = chunks[chunk_idx]

        if error:
            errors.append(
                {"chunk": chunk_idx + 1, "pages": f"{start + 1}-{end}", "error": error}
            )
            yield json.dumps(
                {
                    "event": "chunk_progress",
                    "chunk": chunk_idx + 1,
                    "total": total_chunks,
                    "pages": f"{start + 1}-{end}",
                    "status": "error",
                    "error": error,
                }
            )
        else:
            all_content[chunk_idx] = content
            all_issues.extend(chunk_issues)
            yield json.dumps(
                {
                    "event": "chunk_progress",
                    "chunk": chunk_idx + 1,
                    "total": total_chunks,
                    "pages": f"{start + 1}-{end}",
                    "status": "complete",
                }
            )

    # Merge and deduplicate results
    if any(all_content):
        # Deduplicate issues from overlapping regions
        unique_issues = deduplicate_issues(all_issues)

        # Build merged content with overview noting chunked review
        merged = build_merged_review(all_content, unique_issues, errors, total_chunks)

        # Emit merged content as text event
        yield json.dumps({"event": "text", "text": merged})

    # Emit completion
    if errors:
        yield json.dumps(
            {
                "event": "complete",
                "status": "partial",
                "completed_chunks": total_chunks - len(errors),
                "failed_chunks": len(errors),
                "errors": errors,
            }
        )
    else:
        yield json.dumps({"event": "complete", "status": "complete"})


async def review_document(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    confidence: float,
    output_format: str = "digital",
) -> AsyncGenerator[str, None]:
    """
    Stream AI document review.

    Automatically detects large documents and delegates to chunked review.
    For documents over 40 pages, splits into chunks and processes in parallel.
    For smaller documents, processes directly.

    Args:
        pdf_bytes: Raw PDF file bytes
        extraction: Extracted document data
        document_type: Document type ID
        confidence: Document type detection confidence
        output_format: Output format (digital, print, both)

    Yields:
        Text chunks from AI response (or JSON events for chunked review)

    Raises:
        AIClientError: On API errors
        FileNotFoundError: If rules context missing
    """
    # Check if document needs chunking
    chunker = DocumentChunker()
    if chunker.needs_chunking(extraction.metadata.page_count):
        logger.info(
            f"Large document ({extraction.metadata.page_count} pages) - "
            "using chunked review"
        )
        async for event in review_document_chunked(
            pdf_bytes=pdf_bytes,
            extraction=extraction,
            document_type=document_type,
            confidence=confidence,
            output_format=output_format,
        ):
            yield event
        return

    # Standard review for smaller documents
    # DPI requirements by output format
    DPI_REQUIREMENTS = {
        "digital": {"min": 72, "label": "Digital"},
        "print": {"min": 300, "label": "Print"},
        "both": {"min": 150, "label": "Print + Digital"},
    }
    dpi_info = DPI_REQUIREMENTS.get(output_format, DPI_REQUIREMENTS["digital"])
    # Load rules context
    rules_context = load_rules_context(document_type)
    logger.info(f"Loaded rules context for {document_type}: {len(rules_context)} chars")

    # Build prompts
    system_prompt = build_system_prompt(rules_context)
    extraction_json = json.dumps(extraction.dict(), indent=2, default=str)
    user_prompt = build_user_prompt(
        extraction_json, document_type, confidence, output_format, dpi_info["min"]
    )

    logger.info(
        f"Starting review: {extraction.metadata.page_count} pages, "
        f"type={document_type}, format={output_format} ({dpi_info['min']} DPI)"
    )

    # Stream from AI client
    client = get_ai_client()
    async for chunk in client.review_document_stream(
        pdf_bytes=pdf_bytes,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
    ):
        yield chunk

    logger.info("Review stream complete")
