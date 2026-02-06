---
phase: 09-chunked-document-review
plan: 05
subsystem: ai-review
tags: [sequential-chain, consolidation, uat, chunked-review]
completed: 2026-02-06
duration: 30m

dependency-graph:
  requires: ["09-04"]
  provides: ["sequential-chain-review", "consolidation-fallback"]
  affects: []

tech-stack:
  patterns:
    - Sequential chain prompting (accumulated issues passed between chunks)
    - Consolidation detection (prior-page heuristic)
    - Fallback extend when AI doesn't consolidate

file-tracking:
  modified:
    - backend/app/ai/prompts.py
    - backend/app/ai/reviewer.py
    - frontend/src/components/CommentList/CommentList.tsx

decisions:
  - name: Sequential chain over parallel
    choice: Sequential for-loop replacing asyncio.as_completed
    rationale: Each chunk needs accumulated issues from prior chunks for consolidation
  - name: Consolidation detection fallback
    choice: Check if returned issues reference pages before current chunk
    rationale: AI doesn't always consolidate as instructed; extend instead of replace when it fails
  - name: Page tag truncation threshold
    choice: Show first 5 pages + last page when >6 pages
    rationale: Prevents long page lists from overflowing card layout

metrics:
  tasks: 3
  commits: 1
---

# Phase 09 Plan 05: UAT & Sequential Chain Review Summary

**One-liner:** Replaced parallel chunk processing with sequential chain consolidation, added consolidation fallback, truncated page tags, and passed UAT.

## What Was Built

### Sequential Chain Chunked Review
- Replaced `build_chunk_user_prompt` with `build_chain_chunk_prompt` accepting `previous_issues_json`
- First chunk: identical behavior (doc-wide checks for ISBN, DOI, logos)
- Continuation chunks: "Previous Findings" section with KEEP/UPDATE/MERGE/REMOVE/ADD instructions
- AI outputs complete consolidated issue list per chunk

### Consolidation Fallback
- Detects whether AI actually consolidated by checking if returned issues reference prior pages
- If consolidated: replace `accumulated_issues` with full list
- If not consolidated: extend with new issues (preserves prior findings)
- First chunk always replaces (starts accumulation)

### Frontend Page Tag Truncation
- 1 page: `p. 5`
- 2-6 pages: `pp. 1, 2, 3, 4, 5`
- 7+ pages: `pp. 1, 2, 3, 4, 5... 138`

### Cleanup
- Removed `deduplicate_issues()` function (AI consolidates inline)
- Removed `hashlib` import
- Removed `Semaphore` and `as_completed` parallel processing
- Added `_collect_stream()` helper for `asyncio.wait_for` compatibility

## Commits

| Hash | Type | Description |
|------|------|-------------|
| e37964c | feat | Sequential chain chunked review with consolidation fallback |

## UAT Results

- Large PDF (140 pages): chunks processed sequentially, chunk progress displayed correctly
- Comment list populated with consolidated issues across all chunks
- Page tags truncated properly on cards
- Small PDFs: unchanged behavior (no chunking)

## Deviations from Original Plan

1. **Consolidation fallback added**: Original plan assumed AI would always consolidate. Testing revealed AI sometimes only returns its own chunk's issues. Added prior-page detection heuristic to fall back to extend mode.
2. **Page tag truncation**: Added as a UX fix discovered during testing (not in original 09-05 plan).
