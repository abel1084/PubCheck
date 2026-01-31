"""
REST API router for AI-powered document analysis.
"""
import logging
import os
import tempfile
import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config.service import DocumentTypeId
from app.models.extraction import ExtractionResult

from .analyzer import analyze_document
from .client import AIClientError, AIConfigurationError
from .schemas import DocumentAnalysisResult


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze", response_model=DocumentAnalysisResult)
async def analyze_pdf(
    document_type: DocumentTypeId = Form(...),
    extraction: str = Form(...),  # JSON string of ExtractionResult
    file: UploadFile = File(...),
) -> DocumentAnalysisResult:
    """
    Run AI analysis on uploaded PDF.

    Receives PDF file and extraction data, returns AI findings.
    Uses multipart form to send PDF alongside extraction JSON.

    Args:
        document_type: Type of document for rule selection
        extraction: JSON-serialized ExtractionResult
        file: The PDF file to analyze

    Returns:
        DocumentAnalysisResult with per-page findings
    """
    tmp_path = None
    try:
        # Parse extraction from JSON (Pydantic v2 method)
        logger.info(f"AI analyze request: document_type={document_type}")
        extraction_data = ExtractionResult.model_validate_json(extraction)
        logger.info(f"Extraction parsed: {extraction_data.metadata.page_count} pages")

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        logger.info(f"PDF saved to temp: {tmp_path}")

        result = await analyze_document(tmp_path, extraction_data, document_type)
        logger.info(f"Analysis complete: {result.total_findings} findings")
        return result

    except AIConfigurationError as e:
        logger.error(f"AI configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except AIClientError as e:
        logger.error(f"AI client error: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in AI analyze: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
