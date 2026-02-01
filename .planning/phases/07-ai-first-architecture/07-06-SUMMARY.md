---
phase: 07-ai-first-architecture
plan: 06
subsystem: ai-review
tags: [streaming, sse, fastapi, claude, api]

dependency_graph:
  requires:
    - 07-01 (rules_context markdown files)
    - 07-02 (Claude client with streaming)
    - 07-04 (reviewer.py, prompts.py, schemas.py)
  provides:
    - POST /api/ai/review streaming SSE endpoint
    - Backward compatibility stub for old /analyze endpoint
  affects:
    - 07-07 (frontend streaming consumption)

tech-stack:
  added:
    - sse-starlette>=1.6.0
  patterns:
    - EventSourceResponse for SSE streaming
    - Async generator for event production
    - Error event classification (configuration/api/unknown)

files:
  key-files:
    created:
      - backend/app/ai/reviewer.py
      - backend/app/config/rules_context/factsheet.md
      - backend/app/config/rules_context/brief.md
      - backend/app/config/rules_context/working_paper.md
      - backend/app/config/rules_context/publication.md
    modified:
      - backend/app/ai/router.py
      - backend/app/ai/__init__.py
      - backend/app/ai/prompts.py
      - backend/app/ai/schemas.py
    deleted:
      - backend/app/ai/analyzer.py
      - backend/app/ai/renderer.py

decisions:
  - decision: "Extraction sent as Form field JSON string"
    rationale: "Simpler than multipart file upload for JSON data"
  - decision: "Confidence as Form field float"
    rationale: "Matches document type detection output format"
  - decision: "Error events yield with type classification"
    rationale: "Frontend can distinguish config vs API vs unknown errors"
  - decision: "Old /analyze returns 410 Gone"
    rationale: "Clear deprecation signal during Phase 7 transition"

metrics:
  duration: "5 min"
  completed: "2026-02-01"
  commits: 2
---

# Phase 7 Plan 06: Streaming SSE Review Endpoint Summary

Streaming SSE review endpoint using EventSourceResponse with async generator for real-time AI response delivery.

## What Was Built

### 1. Streaming Review Endpoint
Rewrote `router.py` with new POST `/api/ai/review` endpoint:

```python
@router.post("/review")
async def review_pdf(
    file: UploadFile = File(...),
    extraction: str = Form(...),
    document_type: str = Form(...),
    confidence: float = Form(...),
):
    return EventSourceResponse(
        generate_review_events(pdf_bytes, extraction_data, document_type, confidence),
        media_type="text/event-stream",
    )
```

### 2. SSE Event Generator
Created `generate_review_events()` async generator yielding three event types:
- **text**: `{"text": "chunk of review text"}` - streaming content
- **complete**: `{"status": "complete"}` - signals stream end
- **error**: `{"error": "message", "type": "configuration|api|unknown"}` - error handling

### 3. Module Cleanup
- Deleted obsolete `analyzer.py` (page-by-page DocumentAnalyzer)
- Deleted obsolete `renderer.py` (PDF-to-image rendering)
- Updated `__init__.py` exports for new architecture

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing P7-T4 dependencies**
- **Found during:** Plan load
- **Issue:** P7-T6 depends on P7-T4 which hadn't been executed. reviewer.py, prompts.py updates, schemas.py updates, and rules_context/ directory were missing.
- **Fix:** Created all required dependencies inline:
  - Created `backend/app/ai/reviewer.py` with `review_document()` and `load_rules_context()`
  - Updated `backend/app/ai/prompts.py` with collegial review system prompt
  - Updated `backend/app/ai/schemas.py` with `ReviewRequest` and `ReviewMetadata`
  - Created `backend/app/config/rules_context/` with 4 markdown files
- **Files created:** reviewer.py, prompts.py, schemas.py, rules_context/*.md
- **Commit:** aec1567

**2. [Rule 3 - Blocking] sse-starlette not installed**
- **Found during:** Import verification
- **Issue:** Module was in requirements.txt but not installed in environment
- **Fix:** Ran `python -m pip install sse-starlette>=1.6.0`
- **Commit:** (runtime fix, not code change)

**3. [Rule 3 - Blocking] Old modules causing import errors**
- **Found during:** Cleanup
- **Issue:** Old analyzer.py and renderer.py no longer needed, could cause confusion
- **Fix:** Deleted both files
- **Files deleted:** analyzer.py, renderer.py
- **Commit:** a48c22f

## Verification Results

| Check | Result |
|-------|--------|
| Router contains EventSourceResponse | PASS |
| `python -c "from app.ai.router import router"` | PASS |
| `python -c "from sse_starlette import EventSourceResponse"` | PASS |
| __init__.py exports review_document, get_ai_client | PASS |
| Old /analyze endpoint returns 410 | PASS |

## API Contract

### Request
```
POST /api/ai/review
Content-Type: multipart/form-data

file: <PDF file>
extraction: <JSON string of ExtractionResult>
document_type: factsheet|policy-brief|issue-note|working-paper|publication
confidence: <float 0-1>
```

### Response
```
Content-Type: text/event-stream

event: text
data: {"text": "### Overview\n\nThis publication..."}

event: text
data: {"text": " looks well-designed overall..."}

event: complete
data: {"status": "complete"}
```

### Error Response
```
event: error
data: {"error": "ANTHROPIC_API_KEY not set.", "type": "configuration"}
```

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| router.py | Rewritten | Streaming SSE endpoint |
| reviewer.py | Created | Document review orchestration |
| prompts.py | Updated | Collegial system prompt |
| schemas.py | Simplified | ReviewRequest, ReviewMetadata only |
| __init__.py | Updated | New module exports |
| rules_context/*.md | Created | Document type rules |
| analyzer.py | Deleted | Old page-by-page analysis |
| renderer.py | Deleted | Old PDF rendering |

## Next Phase Readiness

**Ready for:** 07-07 (Frontend Streaming UI)

**Blockers:** None

**Notes:**
- Frontend will consume SSE stream via fetch API
- Error events enable graceful error handling in UI
- Complete event signals when to stop loading indicator
