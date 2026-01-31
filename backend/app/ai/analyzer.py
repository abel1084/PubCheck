"""
Document analyzer that orchestrates AI analysis across all PDF pages.
Uses concurrent page processing with graceful timeout handling.
"""
import asyncio
import time
from typing import Optional

from app.config.service import DocumentTypeId, RuleService
from app.models.extraction import ExtractionResult

from .client import AIClient, AIClientError, get_ai_client
from .prompts import SYSTEM_PROMPT, build_analysis_prompt, generate_checklist
from .renderer import render_page_to_base64
from .schemas import AIFinding, DocumentAnalysisResult, PageAnalysisResult


# Concurrency limit for parallel page analysis
MAX_CONCURRENT_PAGES = 5

# Timeout per page in seconds
PAGE_TIMEOUT = 30


class DocumentAnalyzer:
    """
    Orchestrates AI-powered document analysis.

    Processes pages concurrently (up to MAX_CONCURRENT_PAGES at a time),
    handles timeouts gracefully, and aggregates results.
    """

    def __init__(
        self,
        pdf_path: str,
        extraction: ExtractionResult,
        document_type: DocumentTypeId,
    ):
        """
        Initialize the document analyzer.

        Args:
            pdf_path: Path to the PDF file
            extraction: Pre-extracted document data
            document_type: Type of document for rule selection
        """
        self.pdf_path = pdf_path
        self.extraction = extraction
        self.document_type = document_type
        self.client: AIClient = get_ai_client()
        self._rule_service = RuleService()

    def _build_page_context(self, page_num: int) -> str:
        """
        Build extraction summary for a specific page.

        Args:
            page_num: 1-indexed page number

        Returns:
            Formatted extraction summary for the page
        """
        lines = []
        page_idx = page_num - 1  # Convert to 0-indexed

        # Page info
        lines.append(f"Page {page_num} of {self.extraction.metadata.page_count}")
        lines.append(f"Document type: {self.document_type}")

        # Margins for this page
        page_margins = [m for m in self.extraction.margins if m.page == page_num]
        if page_margins:
            margin = page_margins[0]
            lines.append(f"Margins (mm): top={margin.top/2.834:.1f}, bottom={margin.bottom/2.834:.1f}, "
                        f"left={margin.left/2.834:.1f}, right={margin.right/2.834:.1f}")

        # Fonts on this page
        page_fonts = [
            f.name for f in self.extraction.fonts
            if page_num in f.pages
        ]
        if page_fonts:
            lines.append(f"Fonts: {', '.join(page_fonts[:5])}")
            if len(page_fonts) > 5:
                lines.append(f"  ... and {len(page_fonts) - 5} more")

        # Images on this page
        page_images = [img for img in self.extraction.images if img.page == page_num]
        if page_images:
            lines.append(f"Images: {len(page_images)}")
            for img in page_images[:3]:
                dpi = min(img.dpi_x, img.dpi_y)
                lines.append(f"  - {img.width}x{img.height}px, {dpi:.0f} DPI")

        # Text snippets from this page (first 500 chars)
        page_text_blocks = [tb for tb in self.extraction.text_blocks if tb.page == page_num]
        if page_text_blocks:
            text_content = " ".join(tb.text for tb in page_text_blocks[:10])
            if len(text_content) > 500:
                text_content = text_content[:500] + "..."
            lines.append(f"Text preview: {text_content}")

        return "\n".join(lines)

    async def _analyze_page(
        self,
        page_num: int,
        checklist: str,
        semaphore: asyncio.Semaphore,
    ) -> PageAnalysisResult:
        """
        Analyze a single page with timeout handling.

        Args:
            page_num: 1-indexed page number
            checklist: Generated checklist for rule checking
            semaphore: Semaphore for concurrency control

        Returns:
            PageAnalysisResult with findings or error
        """
        async with semaphore:
            try:
                # Run with timeout
                return await asyncio.wait_for(
                    self._analyze_page_impl(page_num, checklist),
                    timeout=PAGE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                return PageAnalysisResult(
                    page_number=page_num,
                    findings=[],
                    error=f"Page {page_num} timed out after {PAGE_TIMEOUT} seconds",
                )
            except AIClientError as e:
                return PageAnalysisResult(
                    page_number=page_num,
                    findings=[],
                    error=str(e),
                )
            except Exception as e:
                return PageAnalysisResult(
                    page_number=page_num,
                    findings=[],
                    error=f"Unexpected error: {str(e)}",
                )

    async def _analyze_page_impl(
        self,
        page_num: int,
        checklist: str,
    ) -> PageAnalysisResult:
        """
        Actual page analysis implementation.

        Args:
            page_num: 1-indexed page number
            checklist: Generated checklist

        Returns:
            PageAnalysisResult with findings
        """
        # Render page to base64 (0-indexed for renderer)
        image_data = await asyncio.to_thread(
            render_page_to_base64,
            self.pdf_path,
            page_num - 1,  # Convert to 0-indexed
            72,  # Screen DPI
        )

        # Build page-specific context
        page_context = self._build_page_context(page_num)

        # Build prompt
        prompt = build_analysis_prompt(checklist, page_context)

        # Call AI client (in thread to not block)
        response = await asyncio.to_thread(
            self.client.analyze_page,
            image_data,
            prompt,
            SYSTEM_PROMPT,
        )

        # Parse response into findings
        findings = []
        raw_findings = response.get("findings", [])

        for raw in raw_findings:
            try:
                finding = AIFinding(
                    check_name=raw.get("check_name", "Unknown"),
                    passed=raw.get("passed", True),
                    confidence=raw.get("confidence", "medium"),
                    message=raw.get("message", ""),
                    reasoning=raw.get("reasoning"),
                    location=raw.get("location"),
                    suggestion=raw.get("suggestion"),
                )
                findings.append(finding)
            except Exception:
                # Skip malformed findings
                continue

        return PageAnalysisResult(
            page_number=page_num,
            findings=findings,
        )

    async def analyze(self) -> DocumentAnalysisResult:
        """
        Analyze all pages in the document concurrently.

        Returns:
            DocumentAnalysisResult with all page results
        """
        # Generate checklist from merged rules
        template = self._rule_service.get_merged_rules(self.document_type)
        checklist = generate_checklist(template)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

        # Create tasks for all pages
        page_count = self.extraction.metadata.page_count
        tasks = [
            self._analyze_page(page_num, checklist, semaphore)
            for page_num in range(1, page_count + 1)
        ]

        # Run all tasks concurrently
        page_results = await asyncio.gather(*tasks)

        # Count total findings
        total_findings = sum(
            len(result.findings)
            for result in page_results
            if not result.error
        )

        return DocumentAnalysisResult(
            page_results=list(page_results),
            total_findings=total_findings,
        )


async def analyze_document(
    pdf_path: str,
    extraction: ExtractionResult,
    document_type: DocumentTypeId,
) -> DocumentAnalysisResult:
    """
    Analyze a PDF document using AI vision.

    Convenience function that creates an analyzer and runs analysis.

    Args:
        pdf_path: Path to the PDF file
        extraction: Pre-extracted document data
        document_type: Type of document for rule selection

    Returns:
        DocumentAnalysisResult with findings from all pages
    """
    start_time = time.time()

    analyzer = DocumentAnalyzer(pdf_path, extraction, document_type)
    result = await analyzer.analyze()

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    result.analysis_duration_ms = duration_ms

    return result
