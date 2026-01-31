"""
REST API router for AI-powered document analysis.
"""
import json
import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from app.config.service import DocumentTypeId
from app.models.extraction import ExtractionResult

from .analyzer import analyze_document
from .schemas import DocumentAnalysisResult


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
    # Parse extraction from JSON
    extraction_data = ExtractionResult.parse_raw(extraction)

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await analyze_document(tmp_path, extraction_data, document_type)
        return result
    finally:
        # Clean up temp file
        os.unlink(tmp_path)
