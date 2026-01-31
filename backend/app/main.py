"""
PubCheck - UNEP PDF Design Compliance Checker
FastAPI application entry point
"""
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

from app.services.pdf_extractor import extract_document
from app.services.document_classifier import classify_document

app = FastAPI(
    title="PubCheck",
    description="UNEP PDF Design Compliance Checker",
    version="1.0.0"
)

# CORS middleware for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PubCheck"}


@app.get("/api/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/upload")
async def upload_pdf(file: UploadFile):
    """
    Upload and process a PDF file.

    Extracts content, classifies document type, and returns all data.

    Returns:
        JSON with filename, document_type, confidence, and extraction data
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if file.content_type and file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        # Read file bytes
        file_bytes = await file.read()

        # Check for rasterized/scanned PDF (minimal text extraction)
        extraction = extract_document(file_bytes, file.filename)

        # Detect rasterized PDFs: very few text blocks relative to page count
        text_per_page = len(extraction.text_blocks) / max(extraction.metadata.page_count, 1)
        if text_per_page < 2 and extraction.metadata.page_count > 0:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "rasterized_pdf",
                    "message": "This PDF appears to be scanned or rasterized.",
                    "details": "Text extraction found minimal readable content. "
                              "Please provide a PDF with selectable text.",
                }
            )

        # Classify document type
        doc_type, confidence = classify_document(
            extraction.metadata,
            extraction.text_blocks,
        )

        return {
            "filename": file.filename,
            "document_type": doc_type,
            "confidence": confidence,
            "extraction": extraction.dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


# Static files mount placeholder
# Uncomment when static directory exists
# static_path = Path(__file__).parent.parent / "static"
# if static_path.exists():
#     app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
