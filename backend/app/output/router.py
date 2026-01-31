"""
API router for PDF output generation.
"""
import io
import json

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from .models import AnnotationRequest
from .pdf_annotator import PDFAnnotator

router = APIRouter(prefix="/api/output", tags=["output"])


@router.post("/annotate")
async def annotate_pdf(
    pdf: UploadFile = File(...),
    issues: str = Form(...)
):
    """Generate annotated PDF with sticky notes at issue locations.

    Args:
        pdf: The original PDF file to annotate
        issues: JSON string of AnnotationRequest with issues to mark

    Returns:
        StreamingResponse with annotated PDF for download
    """
    # Parse issues JSON
    request = AnnotationRequest.model_validate_json(issues)

    # Read PDF bytes
    pdf_bytes = await pdf.read()

    # Create annotator
    annotator = PDFAnnotator(pdf_bytes)

    try:
        # Count errors and warnings
        error_count = sum(1 for i in request.issues if i.severity == "error")
        warning_count = len(request.issues) - error_count

        # Add summary annotation first (reserves position at top of page 1)
        if request.issues:
            annotator.add_summary_annotation(error_count, warning_count)

        # Add issue annotations
        for issue in request.issues:
            point = (issue.x, issue.y) if issue.x is not None else None
            annotator.add_issue_annotation(
                page_num=issue.page,
                point=point,
                message=issue.message,
                severity=issue.severity,
                reviewer_note=issue.reviewer_note
            )

        # Get annotated PDF
        result_bytes = annotator.save()
    finally:
        annotator.close()

    # Generate filename with _annotated suffix
    original_name = pdf.filename or "document.pdf"
    base_name = original_name.rsplit(".", 1)[0]
    annotated_name = f"{base_name}_annotated.pdf"

    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{annotated_name}"'
        }
    )
