---
phase: 09
plan: 03
subsystem: ai-review
tags: [chunking, parallel, deduplication, gemini]

dependency-graph:
  requires: [09-01]
  provides: [chunked-review-orchestration, issue-deduplication]
  affects: [09-04, 09-05]

tech-stack:
  added: []
  patterns: [parallel-processing, semaphore-limiting, issue-hashing]

key-files:
  created: []
  modified:
    - backend/app/ai/reviewer.py

decisions:
  - id: issue-hash-key
    choice: "title + min_page + category for deduplication"
    rationale: "Stable identity across chunk overlaps without requiring exact match"
  - id: parallel-completion
    choice: "asyncio.as_completed for chunk processing"
    rationale: "Emit progress events as chunks complete, not in submission order"
  - id: merged-review-structure
    choice: "Combine prose sections, deduplicate JSON issues"
    rationale: "Unified review output maintains familiar structure"

metrics:
  duration: 4 min
  completed: 2026-02-05
---

# Phase 9 Plan 03: Chunked Review Orchestration Summary

Parallel chunk processing with Semaphore(2) limiting and issue deduplication across overlaps.

## What Was Built

### Issue Deduplication (`deduplicate_issues`)
- Removes duplicate issues from chunk overlaps using MD5 hash
- Key: `{title}|{min_page}|{category}`
- Keeps first occurrence of duplicates

### Chunk Issue Parser (`parse_chunk_issues`)
- Extracts issues array from JSON code block in AI response
- Handles missing or malformed JSON gracefully

### Merged Review Builder (`build_merged_review`)
- Combines prose sections (Overview, Needs Attention, Looking Good, Suggestions)
- Extracts and merges sections from all chunk responses
- Rebuilds JSON block with deduplicated, re-numbered issues
- Notes chunked review in overview (e.g., "reviewed in 4 chunks")

### Chunked Review Generator (`review_document_chunked`)
- Emits SSE events: `review_start`, `chunk_progress`, `text`, `complete`
- Processes chunks in parallel with `asyncio.Semaphore(2)` limiting
- Uses `asyncio.as_completed` for progress events as chunks finish
- Handles partial failures gracefully with error events
- Merges and deduplicates after all chunks complete

### Auto-Delegation (`review_document`)
- Checks `chunker.needs_chunking(page_count)` at start
- Documents over 40 pages delegate to `review_document_chunked`
- Smaller documents use standard single-pass review
- Transparent to callers - same function signature

## SSE Event Flow

```
review_start:     {"event": "review_start", "total_chunks": 4}
chunk_progress:   {"event": "chunk_progress", "chunk": 1, "total": 4, "pages": "1-35", "status": "complete"}
chunk_progress:   {"event": "chunk_progress", "chunk": 2, "total": 4, "pages": "34-68", "status": "complete"}
...
text:             {"event": "text", "text": "### Overview\n*This document was reviewed in 4 chunks.*\n\n..."}
complete:         {"event": "complete", "status": "complete"}
```

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/ai/reviewer.py` | Added deduplication, chunk processing, auto-delegation |

## Commits

| Hash | Description |
|------|-------------|
| a920f51 | Add issue deduplication function |
| 79b1122 | Add chunked review orchestration |
| a091ea7 | Auto-delegate to chunked review for large docs |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Ready for 09-04 (Frontend Progress UI):
- SSE events defined and implemented
- Progress events emitted as chunks complete
- Error handling for partial failures
- Merged content includes chunk count in overview

## Technical Notes

- Semaphore(2) limits concurrent API calls to avoid rate limits
- `as_completed` enables real-time progress tracking
- Issue hashing uses MD5 for speed (not cryptographic)
- Merged review re-numbers issue IDs sequentially (issue-1, issue-2, etc.)
