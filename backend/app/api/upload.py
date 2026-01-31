"""
PubCheck - Upload API
Handles PDF file uploads with extraction and validation
"""
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pymupdf

from app.services.detector import is_rasterized_pdf
from app.services.document_type_detector import detect_document_type
from app.services.pdf_extractor import PDFExtractor
from app.models.upload import UploadResponse, RejectionResponse

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_pdf(file: UploadFile):
    """
    Upload a PDF for extraction and analysis.

    Performs the following:
    1. Validates the file is a PDF
    2. Checks if the PDF is rasterized/scanned (rejects with 422)
    3. Detects the UNEP document type
    4. Extracts all content (text, images, margins, metadata)

    Returns:
        UploadResponse with extraction results on success
        RejectionResponse (422) for rasterized PDFs
        HTTPException (400) for invalid files

    Raises:
        HTTPException: 400 for non-PDF files or invalid PDFs
    """
    # 1. Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf file."
        )

    # 2. Read file content
    content = await file.read()

    # Validate file is not empty
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    # 3. Open with PyMuPDF
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid PDF file: {str(e)}"
        )

    try:
        # 4. Check for rasterized content (UPLD-03)
        is_rasterized, reason = is_rasterized_pdf(doc)
        if is_rasterized:
            return JSONResponse(
                status_code=422,
                content=RejectionResponse(
                    error="rasterized_pdf",
                    message="This PDF appears to be a scanned image without text layers.",
                    details=reason,
                ).model_dump()
            )

        # 5. Detect document type (UPLD-02)
        doc_type, confidence = detect_document_type(doc)

        # 6. Extract content
        extractor = PDFExtractor(content, file.filename or "unknown.pdf")
        try:
            extraction = extractor.extract()
        finally:
            extractor.close()

        return UploadResponse(
            filename=file.filename or "unknown.pdf",
            document_type=doc_type,
            confidence=confidence,
            extraction=extraction,
        )

    finally:
        doc.close()
