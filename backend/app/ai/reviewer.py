"""
Document reviewer module.
Orchestrates AI document review by combining PDF, extraction, and rules context.
"""
import asyncio
import gc
import json
import logging
import re
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from app.models.extraction import ExtractionResult

from .chunker import (
    DocumentChunker,
    compress_pdf_for_ai,
    extract_page_range,
    filter_extraction_for_chunk,
    needs_compression,
)
from .client import get_ai_client
from .prompts import build_chain_chunk_prompt, build_system_prompt, build_user_prompt


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


CHUNK_TIMEOUT = 300  # 5 minutes per chunk


async def _collect_stream(client, chunk_pdf: bytes, user_prompt: str, system_prompt: str) -> str:
    """Collect all text from AI review stream into a single string."""
    parts = []
    async for text in client.review_document_stream(
        pdf_bytes=chunk_pdf, user_prompt=user_prompt, system_prompt=system_prompt
    ):
        parts.append(text)
    return "".join(parts)


async def review_document_chunked(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    confidence: float,
    output_format: str = "digital",
) -> AsyncGenerator[str, None]:
    """
    Review large document in sequential chunks with chain consolidation.

    Each chunk receives the accumulated issue list from all previous chunks.
    The AI consolidates, deduplicates, and updates page references as it goes,
    so the last successful chunk's output IS the final issue list.

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
        f"Starting sequential chain review: {total_chunks} chunks, "
        f"{extraction.metadata.page_count} pages"
    )

    # Emit start event
    yield json.dumps({"event": "review_start", "total_chunks": total_chunks})

    # Pre-extract all chunk PDFs in a single pass, then release original PDF
    logger.info(f"Pre-extracting {total_chunks} chunk PDFs...")
    chunk_pdfs: list[bytes | None] = []
    for start, end in chunks:
        chunk_pdf = extract_page_range(pdf_bytes, start, end)
        chunk_pdfs.append(chunk_pdf)

    # Release original PDF — chunks are self-contained now
    del pdf_bytes
    gc.collect()
    logger.info("Chunk extraction complete, original PDF released")

    client = get_ai_client()
    accumulated_issues: List[Dict[str, Any]] = []
    all_content: List[str] = [""] * total_chunks
    errors: List[Dict[str, Any]] = []

    for chunk_idx, (start, end) in enumerate(chunks):
        # 1-indexed page numbers for prompts
        actual_start = start + 1
        actual_end = end  # end is exclusive 0-indexed = inclusive 1-indexed

        logger.info(
            f"Processing chunk {chunk_idx + 1}/{total_chunks}: "
            f"pages {actual_start}-{actual_end}"
        )

        try:
            chunk_pdf = chunk_pdfs[chunk_idx]

            # Filter extraction for this chunk
            chunk_extraction = filter_extraction_for_chunk(extraction, start, end)
            extraction_json = json.dumps(
                chunk_extraction.dict(), indent=2, default=str
            )

            # Pass accumulated issues to continuation chunks
            previous_issues_json = (
                json.dumps(accumulated_issues, indent=2)
                if accumulated_issues else None
            )

            user_prompt = build_chain_chunk_prompt(
                extraction_json=extraction_json,
                document_type=document_type,
                confidence=confidence,
                output_format=output_format,
                dpi_min=dpi_info["min"],
                chunk_start=actual_start,
                chunk_end=actual_end,
                is_first_chunk=(chunk_idx == 0),
                total_chunks=total_chunks,
                chunk_number=chunk_idx + 1,
                previous_issues_json=previous_issues_json,
            )

            # Collect full stream with timeout
            content = await asyncio.wait_for(
                _collect_stream(client, chunk_pdf, user_prompt, system_prompt),
                timeout=CHUNK_TIMEOUT,
            )
            all_content[chunk_idx] = content

            # Parse issues from this chunk's response
            chunk_issues = parse_chunk_issues(content)

            # Check if AI actually consolidated (issues reference prior pages)
            has_prior_pages = any(
                any(p < actual_start for p in issue.get("pages", []))
                for issue in chunk_issues
            )

            if has_prior_pages or chunk_idx == 0:
                # AI properly consolidated — replace with full list
                accumulated_issues = chunk_issues
            else:
                # AI only returned new issues for its pages — extend
                logger.info(
                    f"Chunk {chunk_idx + 1}: AI did not consolidate, "
                    f"extending ({len(chunk_issues)} new + "
                    f"{len(accumulated_issues)} prior)"
                )
                accumulated_issues = accumulated_issues + chunk_issues

            yield json.dumps(
                {
                    "event": "chunk_progress",
                    "chunk": chunk_idx + 1,
                    "total": total_chunks,
                    "pages": f"{actual_start}-{actual_end}",
                    "status": "complete",
                }
            )

        except asyncio.TimeoutError:
            errors.append(
                {"chunk": chunk_idx + 1, "pages": f"{actual_start}-{actual_end}",
                 "error": "Chunk processing timed out after 5 minutes"}
            )
            yield json.dumps(
                {
                    "event": "chunk_progress",
                    "chunk": chunk_idx + 1,
                    "total": total_chunks,
                    "pages": f"{actual_start}-{actual_end}",
                    "status": "error",
                    "error": "Chunk processing timed out after 5 minutes",
                }
            )
            # Don't break the chain — next chunk gets same accumulated_issues

        except Exception as e:
            logger.error(f"Chunk {chunk_idx + 1} failed: {e}")
            errors.append(
                {"chunk": chunk_idx + 1, "pages": f"{actual_start}-{actual_end}",
                 "error": str(e)}
            )
            yield json.dumps(
                {
                    "event": "chunk_progress",
                    "chunk": chunk_idx + 1,
                    "total": total_chunks,
                    "pages": f"{actual_start}-{actual_end}",
                    "status": "error",
                    "error": str(e),
                }
            )

        finally:
            # Release chunk PDF after processing
            chunk_pdfs[chunk_idx] = None
            gc.collect()

    # Build merged review — accumulated_issues is already consolidated
    if any(all_content):
        merged = build_merged_review(all_content, accumulated_issues, errors, total_chunks)
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
    For documents over 40 pages, splits into sequential chunks with chain consolidation.
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
    # Strategy for large documents:
    # 1. Try compression first (single coherent review, lower cost)
    # 2. Fall back to chunking if compression fails

    pdf_to_review = pdf_bytes
    pdf_size_mb = len(pdf_bytes) / 1024 / 1024
    page_count = extraction.metadata.page_count

    # Strategy for large documents:
    # - Token limit is ~1M tokens, each page uses ~1500 visual tokens
    # - Safe limit is ~50 pages for single review (~75K visual tokens + JSON + prompts)
    # - Documents over 40 pages MUST be chunked regardless of file size
    # - Compression helps reduce file transfer but doesn't reduce token count significantly

    chunker = DocumentChunker()
    if chunker.needs_chunking(page_count):
        logger.info(f"Large document ({page_count} pages, {pdf_size_mb:.1f}MB) - using chunked review")
        async for event in review_document_chunked(
            pdf_bytes=pdf_bytes,
            extraction=extraction,
            document_type=document_type,
            confidence=confidence,
            output_format=output_format,
        ):
            yield event
        return

    # For smaller documents, try compression if file is large
    if needs_compression(pdf_bytes, threshold_mb=20.0):
        logger.info(f"Compressing PDF ({pdf_size_mb:.1f}MB)")
        try:
            compressed = compress_pdf_for_ai(pdf_bytes, target_size_mb=18.0)
            if compressed:
                pdf_to_review = compressed
                logger.info(f"Compressed: {len(compressed)/1024/1024:.1f}MB")
        except Exception as e:
            logger.warning(f"Compression failed: {e}")

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

    # Stream from AI client (use possibly-compressed PDF)
    client = get_ai_client()
    async for chunk in client.review_document_stream(
        pdf_bytes=pdf_to_review,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
    ):
        yield chunk

    logger.info("Review stream complete")
