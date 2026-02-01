"""
REST API router for AI-powered document review.
Streams review response via Server-Sent Events.
"""
import json
import logging
import os
import tempfile
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sse_starlette import EventSourceResponse

from app.models.extraction import ExtractionResult

from .client import AIClientError, AIConfigurationError
from .reviewer import review_document


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def generate_review_events(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    confidence: float,
) -> AsyncGenerator[dict, None]:
    """
    Generate SSE events from AI review stream.

    Yields:
        SSE event dicts with 'event' and 'data' keys
    """
    try:
        async for text_chunk in review_document(
            pdf_bytes=pdf_bytes,
            extraction=extraction,
            document_type=document_type,
            confidence=confidence,
        ):
            yield {
                "event": "text",
                "data": json.dumps({"text": text_chunk}),
            }

        # Send completion event
        yield {
            "event": "complete",
            "data": json.dumps({"status": "complete"}),
        }

    except AIConfigurationError as e:
        logger.error(f"AI configuration error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e), "type": "configuration"}),
        }

    except AIClientError as e:
        logger.error(f"AI client error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e), "type": "api"}),
        }

    except Exception as e:
        logger.error(f"Unexpected error in review: {e}")
        logger.error(traceback.format_exc())
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e), "type": "unknown"}),
        }


@router.post("/review")
async def review_pdf(
    file: UploadFile = File(...),
    extraction: str = Form(...),
    document_type: str = Form(...),
    confidence: float = Form(...),
):
    """
    Stream AI document review via Server-Sent Events.

    Receives PDF file and extraction data, streams review text chunks.

    Args:
        file: The PDF file to review
        extraction: JSON string of ExtractionResult
        document_type: Type of document (factsheet, publication, etc.)
        confidence: Document type detection confidence (0-1)

    Returns:
        EventSourceResponse streaming text chunks

    SSE Events:
        - text: {"text": "chunk of review text"}
        - complete: {"status": "complete"}
        - error: {"error": "message", "type": "configuration|api|unknown"}
    """
    tmp_path = None
    try:
        logger.info(f"Review request: document_type={document_type}, confidence={confidence}")
        logger.info(f"File: {file.filename}, content_type={file.content_type}")

        # Validate document_type
        valid_types = ["factsheet", "policy-brief", "issue-note", "working-paper", "publication"]
        if document_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document_type: {document_type}. Must be one of: {valid_types}"
            )

        # Parse extraction JSON
        try:
            extraction_data = ExtractionResult.model_validate_json(extraction)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid extraction JSON: {e}"
            )

        logger.info(f"Extraction parsed: {extraction_data.metadata.page_count} pages")

        # Read PDF bytes
        pdf_bytes = await file.read()
        logger.info(f"PDF size: {len(pdf_bytes)} bytes")

        # Return streaming response
        return EventSourceResponse(
            generate_review_events(
                pdf_bytes=pdf_bytes,
                extraction=extraction_data,
                document_type=document_type,
                confidence=confidence,
            ),
            media_type="text/event-stream",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error in review endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


# Keep old analyze endpoint for backward compatibility during transition
# TODO: Remove after frontend migration complete
@router.post("/analyze")
async def analyze_pdf_deprecated(
    file: UploadFile = File(...),
    extraction_file: UploadFile = File(...),
    document_type: str = Form(...),
):
    """
    DEPRECATED: Use /review endpoint instead.
    Kept for backward compatibility during Phase 7 transition.
    """
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /api/ai/review instead."
    )
