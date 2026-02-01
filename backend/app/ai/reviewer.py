"""
Document reviewer module.
Orchestrates AI document review by combining PDF, extraction, and rules context.
"""
import json
import logging
from pathlib import Path
from typing import AsyncGenerator

from app.models.extraction import ExtractionResult

from .client import get_ai_client
from .prompts import build_system_prompt, build_user_prompt


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


async def review_document(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    confidence: float,
) -> AsyncGenerator[str, None]:
    """
    Stream AI document review.

    Sends PDF + extraction + rules context to Claude and yields text chunks.

    Args:
        pdf_bytes: Raw PDF file bytes
        extraction: Extracted document data
        document_type: Document type ID
        confidence: Document type detection confidence

    Yields:
        Text chunks from AI response

    Raises:
        AIClientError: On API errors
        FileNotFoundError: If rules context missing
    """
    # Load rules context
    rules_context = load_rules_context(document_type)
    logger.info(f"Loaded rules context for {document_type}: {len(rules_context)} chars")

    # Build prompts
    system_prompt = build_system_prompt(rules_context)
    extraction_json = json.dumps(extraction.dict(), indent=2, default=str)
    user_prompt = build_user_prompt(extraction_json, document_type, confidence)

    logger.info(f"Starting review: {extraction.metadata.page_count} pages, type={document_type}")

    # Stream from AI client
    client = get_ai_client()
    async for chunk in client.review_document_stream(
        pdf_bytes=pdf_bytes,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
    ):
        yield chunk

    logger.info("Review stream complete")
