"""
REST API router for AI-powered document analysis.
"""
import logging
import os
import tempfile
import traceback

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config.service import DocumentTypeId
from app.models.extraction import ExtractionResult

from .analyzer import analyze_document
from .client import AIClientError, AIConfigurationError
from .schemas import DocumentAnalysisResult


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze", response_model=DocumentAnalysisResult)
async def analyze_pdf(
    file: UploadFile = File(...),
    extraction_file: UploadFile = File(...),
    document_type: str = Form(...),
) -> DocumentAnalysisResult:
    """
    Run AI analysis on uploaded PDF.

    Receives PDF file and extraction data, returns AI findings.
    Extraction is sent as a JSON file to avoid Form field size limits.

    Args:
        file: The PDF file to analyze
        extraction_file: JSON file containing ExtractionResult
        document_type: Type of document for rule selection

    Returns:
        DocumentAnalysisResult with per-page findings
    """
    tmp_path = None
    try:
        logger.info(f"AI analyze request: document_type={document_type}")
        logger.info(f"File: {file.filename}, content_type={file.content_type}")
        logger.info(f"Extraction file: {extraction_file.filename}")

        # Validate document_type
        valid_types = ["factsheet", "policy-brief", "issue-note", "working-paper", "publication"]
        if document_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid document_type: {document_type}. Must be one of: {valid_types}")

        # Read and parse extraction from JSON file
        extraction_content = await extraction_file.read()
        logger.info(f"Extraction size: {len(extraction_content)} bytes")
        extraction_data = ExtractionResult.model_validate_json(extraction_content)
        logger.info(f"Extraction parsed: {extraction_data.metadata.page_count} pages")

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        logger.info(f"PDF saved to temp: {tmp_path}")

        # Cast to DocumentTypeId (already validated above)
        doc_type: DocumentTypeId = document_type  # type: ignore
        result = await analyze_document(tmp_path, extraction_data, doc_type)
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
