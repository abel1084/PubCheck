---
phase: 09
plan: 01
subsystem: ai-chunking
tags: [chunking, pdf, prompts, gemini]
dependency_graph:
  requires: []
  provides: [DocumentChunker, extract_page_range, filter_extraction_for_chunk, build_chunk_user_prompt]
  affects: [09-02, 09-03]
tech-stack:
  added: []
  patterns: [page-range-subsetting, extraction-filtering, chunk-aware-prompts]
key-files:
  created:
    - backend/app/ai/chunker.py
  modified:
    - backend/app/ai/prompts.py
decisions:
  - name: "35 pages per chunk"
    rationale: "Conservative for Gemini 1M token limit with extraction JSON overhead"
  - name: "2-page overlap between chunks"
    rationale: "Provides context continuity across chunk boundaries"
  - name: "40-page threshold"
    rationale: "Small documents don't need chunking overhead"
  - name: "Preserve actual page numbers"
    rationale: "AI findings must reference correct document pages, not chunk-relative"
metrics:
  duration: "5 min"
  completed: "2026-02-05"
---

# Phase 9 Plan 01: Chunking Foundation Summary

**One-liner:** DocumentChunker class with page range calculation, PDF subsetting via PyMuPDF select(), extraction filtering, and chunk-aware prompt builder.

## What Was Built

### Task 1: DocumentChunker Class
Created `backend/app/ai/chunker.py` with:

1. **DocumentChunker class** with tuned constants:
   - PAGES_PER_CHUNK = 35 (conservative for 1M token limit)
   - OVERLAP_PAGES = 2 (context continuity)
   - PAGE_THRESHOLD = 40 (trigger chunking above this)
   - MAX_CONCURRENT = 2 (parallel chunk reviews)

2. **needs_chunking(page_count)** - Returns True if document > 40 pages

3. **calculate_chunks(page_count)** - Returns list of (start, end) tuples with overlap
   - Example: 105 pages -> [(0, 35), (33, 68), (66, 101), (99, 105)]

4. **extract_page_range(pdf_bytes, start, end)** - Creates subset PDF using PyMuPDF select()

5. **filter_extraction_for_chunk(extraction, start, end)** - Filters extraction data while preserving actual page numbers

### Task 2: Chunk-Aware Prompt Builder
Added `build_chunk_user_prompt()` to `backend/app/ai/prompts.py`:

- Includes chunk context header with page range and chunk number
- Instructs AI to use ACTUAL page numbers in findings
- First chunk: includes document-wide checks (ISBN, DOI, copyright, colophon)
- Continuation chunks: skip document-wide checks, focus on typography/images/margins/layout
- Reuses output format and DPI info from standard prompts

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| 35 pages per chunk | Conservative margin for Gemini's 1M token limit with extraction JSON |
| 2-page overlap | Provides context continuity without excessive duplication |
| 40-page threshold | Documents under 40 pages don't need chunking overhead |
| Actual page numbers preserved | AI must reference correct document pages in findings |
| First chunk includes doc-wide checks | ISBN/DOI/copyright only need checking once |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed infinite loop in calculate_chunks**

- **Found during:** Task 1 verification
- **Issue:** When remaining pages < OVERLAP_PAGES, loop would never terminate
- **Fix:** Added early exit when chunk reaches document end, plus progress check
- **Files modified:** backend/app/ai/chunker.py
- **Commit:** 3d55c45

## Verification Results

All verifications passed:
1. Chunker module imports without errors
2. Prompts module imports without errors
3. calculate_chunks(105) produces correct 4 chunks with overlaps
4. First chunk prompt includes document-wide checks (ISBN, DOI, etc.)
5. Continuation chunk prompt says SKIP document-wide checks

## Commits

| Hash | Message |
|------|---------|
| 3d55c45 | feat(09-01): add DocumentChunker for large PDF splitting |
| a23a12d | feat(09-01): add build_chunk_user_prompt for chunked review |

## Next Steps

Plan 09-02 will use these primitives to implement the chunk review workflow:
- Chunk orchestrator with progress tracking
- Concurrent chunk processing with MAX_CONCURRENT limit
- Result merging from multiple chunks
