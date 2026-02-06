"""
REST API router for AI-powered document review.
Streams review response via Server-Sent Events.

The review pipeline runs in a subprocess so that all memory
(CPython/PyMuPDF) is reclaimed by the OS when the process exits.
"""
import asyncio
import gc
import json
import logging
import os
import subprocess
import sys
import tempfile
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from sse_starlette import EventSourceResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def generate_review_events(
    pdf_path: str,
    extraction_path: str,
    document_type: str,
    confidence: float,
    output_format: str,
) -> AsyncGenerator[dict, None]:
    """
    Spawn review_worker subprocess and translate its JSON-line output to SSE events.

    Uses subprocess.Popen with threaded I/O (Windows compatible).

    Args:
        pdf_path: Path to temp file containing PDF bytes
        extraction_path: Path to temp file containing extraction JSON
        document_type: Document type ID
        confidence: Detection confidence
        output_format: Output format (digital, print, both)

    Yields:
        SSE event dicts with 'event' and 'data' keys
    """
    config = json.dumps({
        "pdf_path": pdf_path,
        "extraction_path": extraction_path,
        "document_type": document_type,
        "confidence": confidence,
        "output_format": output_format,
    })

    proc = None
    chunked_mode = False
    loop = asyncio.get_event_loop()

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "app.ai.review_worker", config],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Read stdout line-by-line via thread pool to avoid blocking the event loop
        while True:
            line = await loop.run_in_executor(None, proc.stdout.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON line from worker: {line}")
                continue

            msg_type = msg.get("type")

            if msg_type == "item":
                item = msg["data"]
                # Same dispatch logic as before: JSON event vs plain text
                try:
                    event_data = json.loads(item)
                    event_type = event_data.pop("event", "text")
                    chunked_mode = True
                    yield {
                        "event": event_type,
                        "data": json.dumps(event_data),
                    }
                except json.JSONDecodeError:
                    yield {
                        "event": "text",
                        "data": json.dumps({"text": item}),
                    }

            elif msg_type == "error":
                error_msg = msg.get("message", "Unknown worker error")
                logger.error(f"Worker error: {error_msg}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": error_msg, "type": "unknown"}),
                }
                return

            elif msg_type == "done":
                break

        # Wait for subprocess to finish
        returncode = await loop.run_in_executor(None, proc.wait)

        # Log stderr if any
        stderr_text = await loop.run_in_executor(None, proc.stderr.read)
        if stderr_text:
            for stderr_line in stderr_text.splitlines():
                logger.info(f"[worker] {stderr_line}")

        # Check exit code
        if returncode and returncode != 0:
            logger.error(f"Worker exited with code {returncode}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": f"Review worker crashed (exit code {returncode})",
                    "type": "unknown",
                }),
            }
            return

        # Send completion event for non-chunked mode
        if not chunked_mode:
            yield {
                "event": "complete",
                "data": json.dumps({"status": "complete"}),
            }

    except Exception as e:
        logger.error(f"Unexpected error in review subprocess: {e}")
        logger.error(traceback.format_exc())
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e), "type": "unknown"}),
        }

    finally:
        if proc and proc.poll() is None:
            try:
                proc.kill()
                proc.wait()
            except OSError:
                pass


@router.post("/review")
async def review_pdf(request: Request):
    """
    Stream AI document review via Server-Sent Events.

    Receives PDF file and extraction data, streams review text chunks.
    The review runs in a subprocess for memory isolation.

    Uses Request directly (instead of File/Form params) so we can
    explicitly close the multipart form and reclaim memory before
    the long-lived SSE stream begins.

    SSE Events:
        - text: {"text": "chunk of review text"}
        - complete: {"status": "complete"}
        - error: {"error": "message", "type": "configuration|api|unknown"}
    """
    pdf_path = extraction_path = None
    form = None

    try:
        form = await request.form()

        # Extract form fields
        document_type = str(form.get("document_type", ""))
        try:
            confidence = float(form.get("confidence", 0))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid confidence value")
        output_format = str(form.get("output_format", "digital"))

        file = form.get("file")
        extraction_file = form.get("extraction_file")

        if not file or not extraction_file:
            raise HTTPException(status_code=400, detail="Missing file or extraction_file")

        logger.info(f"Review request: document_type={document_type}, confidence={confidence}, output_format={output_format}")

        # Validate document_type
        valid_types = ["factsheet", "policy-brief", "issue-note", "working-paper", "publication"]
        if document_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document_type: {document_type}. Must be one of: {valid_types}"
            )

        # Validate output_format
        valid_formats = ["digital", "print", "both"]
        if output_format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output_format: {output_format}. Must be one of: {valid_formats}"
            )

        # Stream uploads directly to temp files — never hold full content in memory.
        # Validation of extraction JSON happens in the subprocess.
        CHUNK_SIZE = 64 * 1024  # 64KB chunks

        pdf_fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
        pdf_size = 0
        try:
            while chunk := await file.read(CHUNK_SIZE):
                os.write(pdf_fd, chunk)
                pdf_size += len(chunk)
        finally:
            os.close(pdf_fd)
        logger.info(f"PDF streamed to disk: {pdf_size} bytes")

        extraction_fd, extraction_path = tempfile.mkstemp(suffix=".json")
        extraction_size = 0
        try:
            while chunk := await extraction_file.read(CHUNK_SIZE):
                os.write(extraction_fd, chunk)
                extraction_size += len(chunk)
        finally:
            os.close(extraction_fd)
        logger.info(f"Extraction streamed to disk: {extraction_size} bytes")

        logger.info(f"Temp files: pdf={pdf_path}, extraction={extraction_path}")

        # Release multipart form memory BEFORE the long-lived SSE stream.
        # This closes SpooledTemporaryFiles and lets pymalloc return arenas to OS.
        await form.close()
        form = None
        gc.collect()

        # Wrap generator to ensure temp file cleanup
        async def event_stream():
            try:
                async for event in generate_review_events(
                    pdf_path=pdf_path,
                    extraction_path=extraction_path,
                    document_type=document_type,
                    confidence=confidence,
                    output_format=output_format,
                ):
                    yield event
            finally:
                for path in (pdf_path, extraction_path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

        return EventSourceResponse(
            event_stream(),
            media_type="text/event-stream",
        )

    except HTTPException:
        # Clean up temp files on validation errors
        for path in (pdf_path, extraction_path):
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass
        if form:
            await form.close()
        raise

    except Exception as e:
        # Clean up temp files on unexpected errors
        for path in (pdf_path, extraction_path):
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass
        if form:
            await form.close()
        logger.error(f"Unexpected error in review endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


# Keep old analyze endpoint for backward compatibility during transition
# TODO: Remove after frontend migration complete
@router.post("/analyze")
async def analyze_pdf_deprecated(request: Request):
    """
    DEPRECATED: Use /review endpoint instead.
    Kept for backward compatibility during Phase 7 transition.
    """
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /api/ai/review instead."
    )
