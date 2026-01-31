---
phase: 04
plan: 02
subsystem: ai-infrastructure
tags: [ai, concurrent, asyncio, fastapi, claude-vision]

dependency_graph:
  requires: [04-01]
  provides: [document-analyzer, ai-api-endpoint]
  affects: [04-03, 04-04]

tech_stack:
  added: []
  patterns: [asyncio-semaphore, concurrent-page-processing, multipart-form-upload]

key_files:
  created:
    - backend/app/ai/analyzer.py
    - backend/app/ai/router.py
  modified:
    - backend/app/checks/models.py
    - backend/app/ai/__init__.py
    - backend/app/ai/prompts.py
    - backend/app/ai/renderer.py
    - backend/app/main.py

decisions:
  - name: 5-page concurrent limit
    rationale: Balanced parallelism without overwhelming API rate limits
  - name: 30-second timeout per page
    rationale: Per CONTEXT.md decision for graceful timeout handling
  - name: Multipart form for PDF upload
    rationale: Avoids re-extraction by passing existing ExtractionResult as JSON

metrics:
  duration: ~3 minutes
  completed: 2026-01-31
---

# Phase 4 Plan 02: Document Analyzer with Concurrent Page Processing Summary

Document analyzer orchestrates AI analysis across all PDF pages with 5-page concurrent limit, 30-second timeouts, and REST API endpoint.

## What Was Built

### 1. Extended CheckIssue Model
Added AI-specific fields to CheckIssue for frontend display:
- `ai_verified: bool` - marks findings from AI analysis
- `ai_confidence: Optional[Literal["high", "medium", "low"]]` - confidence level
- `ai_reasoning: Optional[str]` - explanation for non-obvious findings

### 2. DocumentAnalyzer Class
Orchestrates concurrent page analysis:
- `asyncio.Semaphore(5)` for 3-5 concurrent pages
- 30-second timeout per page with graceful error handling
- Builds page context from extraction data (margins, fonts, images, text)
- Generates checklist from merged YAML rules at runtime
- Returns `DocumentAnalysisResult` with per-page findings

### 3. REST API Endpoint
`POST /api/ai/analyze` accepting multipart form:
- `document_type`: factsheet, policy-brief, etc.
- `extraction`: JSON-serialized ExtractionResult
- `file`: PDF file upload

Returns `DocumentAnalysisResult` with:
- Per-page findings array
- Total findings count
- Analysis duration in milliseconds

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Implemented prompts.py and renderer.py**

- **Found during:** Task 2 preparation
- **Issue:** P4-T1 left prompts.py and renderer.py as stubs; analyzer required working implementations
- **Fix:** Implemented SYSTEM_PROMPT, generate_checklist, build_analysis_prompt in prompts.py; render_page_to_base64 in renderer.py
- **Files modified:** backend/app/ai/prompts.py, backend/app/ai/renderer.py
- **Commit:** 8c695d9

## Code Snippets

### Document Analyzer Core Logic
```python
async def _analyze_page(self, page_num, checklist, semaphore):
    async with semaphore:
        try:
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
```

### API Endpoint
```python
@router.post("/api/ai/analyze", response_model=DocumentAnalysisResult)
async def analyze_pdf(
    document_type: DocumentTypeId = Form(...),
    extraction: str = Form(...),
    file: UploadFile = File(...),
) -> DocumentAnalysisResult:
```

## Verification Results

All success criteria met:
1. CheckIssue model has ai_verified, ai_confidence, ai_reasoning fields
2. DocumentAnalyzer processes pages with 5-concurrent limit
3. 30-second timeout per page with graceful error handling
4. POST /api/ai/analyze endpoint accepts PDF and extraction data
5. Results include per-page findings and document summary fields

## Files Changed

| File | Change |
|------|--------|
| backend/app/checks/models.py | Added 3 AI fields to CheckIssue |
| backend/app/ai/analyzer.py | NEW: DocumentAnalyzer, analyze_document |
| backend/app/ai/router.py | NEW: POST /api/ai/analyze endpoint |
| backend/app/ai/prompts.py | Implemented SYSTEM_PROMPT, generate_checklist, build_analysis_prompt |
| backend/app/ai/renderer.py | Implemented render_page_to_base64 |
| backend/app/ai/__init__.py | Added exports for analyzer and router |
| backend/app/main.py | Registered ai_router |

## Next Phase Readiness

Ready for Plan 04-03 (AI Analysis UI Integration):
- DocumentAnalyzer available for import
- REST API endpoint operational
- CheckIssue extended with AI fields for frontend display
- Duration tracking in place for progress indication

## Commits

| Hash | Message |
|------|---------|
| 470c600 | feat(04-02): extend CheckIssue with AI fields |
| 8c695d9 | feat(04-02): create document analyzer with concurrent page processing |
| 93818fb | feat(04-02): create AI analysis API endpoint |
