---
phase: 07-ai-first-architecture
plan: 02
subsystem: ai
tags: [anthropic, claude, pdf, streaming, sdk]

dependency_graph:
  requires: []
  provides: [AIClient, review_document_stream, native-pdf-support, async-streaming]
  affects: [07-03, 07-04, 07-05]

tech_stack:
  added: [anthropic>=0.35.0, sse-starlette>=1.6.0]
  removed: [google-genai]
  patterns: [async-streaming, native-pdf-document, singleton-client]

key_files:
  created: []
  modified:
    - backend/app/ai/client.py
    - backend/requirements.txt

decisions:
  - id: ARCH-03
    choice: "AsyncAnthropic for Claude API"
    rationale: "Native PDF support, async streaming, official SDK"

metrics:
  duration: 3m
  completed: 2026-02-01
---

# Phase 7 Plan 02: AI Client for Claude with PDF and Streaming Summary

Claude AI client rewritten with native PDF document support and async streaming for real-time responses.

## What Was Built

### AI Client Rewrite (client.py)
Replaced the Gemini-based client with Anthropic Claude:

- **Native PDF Support**: Uses `type: "document"` with `media_type: "application/pdf"` instead of rendering pages as images
- **Async Streaming**: `review_document_stream()` is an async generator yielding text chunks via `stream.text_stream`
- **Lazy Initialization**: API key validated on first use, not at import time
- **Singleton Pattern**: Shared client instance across requests via `get_ai_client()`
- **Error Handling**: Distinguishes configuration errors (missing/invalid key) from API errors (rate limits)

### Dependencies Updated
- Added `anthropic>=0.35.0` (Claude SDK with native PDF support)
- Added `sse-starlette>=1.6.0` (for streaming SSE endpoint in later plans)
- Removed `google-genai` (replaced by Anthropic)

## Key Technical Details

### API Method Signature
```python
async def review_document_stream(
    self,
    pdf_bytes: bytes,
    user_prompt: str,
    system_prompt: str,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
```

### Native PDF Document Format
```python
{
    "type": "document",
    "source": {
        "type": "base64",
        "media_type": "application/pdf",
        "data": pdf_base64,
    }
}
```

### Environment Variables
- `ANTHROPIC_API_KEY`: Required for Claude API access
- `AI_MODEL`: Optional override, defaults to `claude-sonnet-4-5`

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| AsyncAnthropic client | Supports async streaming required for SSE endpoint |
| Native PDF document type | Better than rendered images: text extraction + visual analysis |
| 8192 max tokens default | Sufficient for prose review with headroom for long documents |
| Lazy initialization | Allows app to start even without API key (fails gracefully on use) |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Ready for 07-03 (Streaming Review Endpoint):
- Client provides `review_document_stream()` async generator
- `sse-starlette` dependency installed for SSE response
- Error exceptions exported for router error handling

## Verification Results

- `python -c "from app.ai.client import AIClient, get_ai_client; print('OK')"` - PASSED
- client.py contains `AsyncAnthropic` and `review_document_stream` - PASSED
- requirements.txt has `anthropic>=0.35.0` - PASSED
- No Gemini/Google AI imports in client.py - PASSED

---
*Completed: 2026-02-01*
