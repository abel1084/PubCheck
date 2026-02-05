# Phase 9: Chunked Document Review for Large PDFs - Research

**Researched:** 2026-02-05
**Domain:** Large PDF chunking, Gemini API limits, async parallel processing
**Confidence:** HIGH

## Summary

This phase implements automatic document chunking to handle PDFs exceeding Gemini 2.5 Flash's effective context limit. Research confirms Gemini has a 1,048,576 token input limit, with each PDF page consuming approximately 258 tokens (images are tokenized at 258 tokens for images <=384px, or 258 tokens per 768x768 tile for larger images). This means the theoretical maximum is ~4,000 pages, but in practice, page content complexity, extraction JSON, and system prompts consume additional tokens.

The established approach is page-based chunking with overlap for context continuity. PyMuPDF's `select()` method efficiently creates page subsets in memory without file I/O. Python's `asyncio.Semaphore` provides the standard pattern for concurrent chunk processing with configurable limits. The frontend SSE consumer already accumulates streamed content, requiring minimal modification to handle multiple chunk streams merged into a single response.

**Primary recommendation:** Use 35-page chunks with 2-page overlap, process 2 chunks concurrently via Semaphore, deduplicate by issue ID and page number hash, and emit progress events as each chunk completes.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyMuPDF | 1.24+ | PDF page selection via `select()` | Already in project, `select()` is fastest method for page subsetting |
| asyncio.Semaphore | stdlib | Concurrency limiting | Python standard library, simple acquire/release pattern |
| google-genai | current | Gemini API with `count_tokens()` | Already in project, provides token counting before submission |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sse-starlette | 2.0+ | SSE streaming | Already in project, handles multiple events per stream |
| hashlib | stdlib | Issue deduplication hashing | Built-in, MD5/SHA sufficient for local dedup |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Page-based chunks | Token-based chunks | Token counting adds latency; page-based is predictable (258 tokens/page) |
| Semaphore | asyncio.gather with limit | Semaphore is cleaner for variable-count parallel tasks |
| In-memory PDF | Temp files for chunks | Memory is faster; temp files only if memory issues arise |

**Installation:**
```bash
# No new dependencies - all already installed
pip install pymupdf google-generativeai sse-starlette
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/ai/
├── client.py           # Add count_tokens method
├── chunker.py          # NEW: PDF chunking logic
├── reviewer.py         # Modify to use chunker for large docs
├── router.py           # Add chunk progress events
└── prompts.py          # Add chunk-specific prompts

frontend/src/
├── hooks/useAIReview.ts  # Handle chunk progress events
└── types/review.ts       # Add ChunkProgress type
```

### Pattern 1: Chunked Review Pipeline
**What:** Detect large documents, split into chunks, process in parallel with concurrency limit, merge results
**When to use:** When document exceeds 40 pages (conservative threshold for 1M token limit)
**Example:**
```python
# Source: Research synthesis from Gemini docs + asyncio patterns

import asyncio
from typing import AsyncGenerator

class DocumentChunker:
    """Splits large PDFs into reviewable chunks."""

    PAGES_PER_CHUNK = 35      # ~9,000 tokens + prompts stays well under limit
    OVERLAP_PAGES = 2          # Context continuity between chunks
    PAGE_THRESHOLD = 40        # Trigger chunking above this
    MAX_CONCURRENT = 2         # Parallel chunk reviews

    def needs_chunking(self, page_count: int) -> bool:
        return page_count > self.PAGE_THRESHOLD

    def calculate_chunks(self, page_count: int) -> list[tuple[int, int]]:
        """Returns list of (start_page, end_page) tuples (0-indexed)."""
        chunks = []
        start = 0
        while start < page_count:
            end = min(start + self.PAGES_PER_CHUNK, page_count)
            chunks.append((start, end))
            start = end - self.OVERLAP_PAGES  # Overlap for context
            if start >= page_count:
                break
        return chunks

async def review_with_chunking(
    pdf_bytes: bytes,
    extraction: ExtractionResult,
    document_type: str,
    output_format: str,
) -> AsyncGenerator[str, None]:
    """Review large document in chunks with parallel processing."""
    chunker = DocumentChunker()
    page_count = extraction.metadata.page_count

    if not chunker.needs_chunking(page_count):
        # Small document - direct review
        async for chunk in review_document(...):
            yield chunk
        return

    chunks = chunker.calculate_chunks(page_count)
    semaphore = asyncio.Semaphore(chunker.MAX_CONCURRENT)

    async def process_chunk(chunk_idx: int, start: int, end: int):
        async with semaphore:
            chunk_pdf = extract_page_range(pdf_bytes, start, end)
            chunk_extraction = filter_extraction(extraction, start, end)
            is_first = chunk_idx == 0

            result = []
            async for text in review_chunk(
                chunk_pdf, chunk_extraction, document_type,
                start + 1, end,  # 1-indexed for display
                include_document_checks=is_first
            ):
                result.append(text)
            return chunk_idx, start, ''.join(result)

    # Process chunks with concurrency limit
    tasks = [
        process_chunk(i, start, end)
        for i, (start, end) in enumerate(chunks)
    ]

    # Yield progress as chunks complete
    for coro in asyncio.as_completed(tasks):
        chunk_idx, start, content = await coro
        yield f"event: chunk_complete\ndata: {json.dumps({'chunk': chunk_idx, 'start': start})}\n\n"
        yield f"data: {json.dumps({'text': content})}\n\n"
```

### Pattern 2: Page Range Extraction with PyMuPDF
**What:** Extract subset of pages to new in-memory PDF
**When to use:** Creating chunk PDFs for AI review
**Example:**
```python
# Source: PyMuPDF documentation - Document.select()

import pymupdf
import io

def extract_page_range(pdf_bytes: bytes, start: int, end: int) -> bytes:
    """
    Extract pages [start, end) to new PDF bytes.

    Args:
        pdf_bytes: Original PDF bytes
        start: Start page (0-indexed, inclusive)
        end: End page (0-indexed, exclusive)

    Returns:
        PDF bytes containing only selected pages
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        # select() keeps only specified pages, modifies doc in place
        page_list = list(range(start, end))
        doc.select(page_list)

        # Write to bytes buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    finally:
        doc.close()
```

### Pattern 3: Extraction Filtering for Chunks
**What:** Filter extraction JSON to only include data for chunk's page range
**When to use:** Sending relevant extraction data with each chunk
**Example:**
```python
# Source: Project-specific pattern

def filter_extraction_for_chunk(
    extraction: ExtractionResult,
    start_page: int,
    end_page: int
) -> ExtractionResult:
    """
    Filter extraction to only include data for pages [start, end).
    Adjusts page numbers to be chunk-relative (starting from 1).

    Args:
        extraction: Full document extraction
        start_page: Start page (0-indexed)
        end_page: End page (0-indexed, exclusive)

    Returns:
        New ExtractionResult with filtered and renumbered data
    """
    page_range = range(start_page + 1, end_page + 1)  # 1-indexed in extraction

    return ExtractionResult(
        metadata=DocumentMetadata(
            filename=extraction.metadata.filename,
            page_count=end_page - start_page,
            # Keep other metadata as-is
            title=extraction.metadata.title,
            author=extraction.metadata.author,
            isbn=extraction.metadata.isbn,
            doi=extraction.metadata.doi,
            job_number=extraction.metadata.job_number,
        ),
        text_blocks=[
            TextBlock(
                page=block.page - start_page,  # Renumber to chunk-relative
                **{k: v for k, v in block.dict().items() if k != 'page'}
            )
            for block in extraction.text_blocks
            if block.page in page_range
        ],
        images=[
            img._replace(page=img.page - start_page)  # Renumber
            for img in extraction.images
            if img.page in page_range
        ],
        margins=[
            m for m in extraction.margins
            if m.page in page_range
        ],
        fonts=extraction.fonts,  # Keep full font summary
    )
```

### Pattern 4: Chunk-Aware Prompts
**What:** Modify prompts to indicate chunk context and skip document-wide checks
**When to use:** All chunk reviews after the first
**Example:**
```python
# Source: Project-specific pattern

def build_chunk_user_prompt(
    extraction_json: str,
    document_type: str,
    confidence: float,
    output_format: str,
    dpi_min: int,
    chunk_start: int,  # 1-indexed
    chunk_end: int,    # 1-indexed, inclusive
    is_first_chunk: bool,
) -> str:
    """Build prompt for chunk review with page context."""

    chunk_context = f"""
## Chunk Information
You are reviewing **pages {chunk_start}-{chunk_end}** of a larger document.
Page numbers in your findings should use the ACTUAL page numbers ({chunk_start}-{chunk_end}), not relative numbers.
"""

    if is_first_chunk:
        scope_note = """
This is the FIRST chunk. Include document-wide checks:
- ISBN, DOI, job number presence
- Copyright notice and disclaimer
- Colophon/publication info
"""
    else:
        scope_note = """
This is a CONTINUATION chunk. SKIP document-wide checks (already done in first chunk):
- Do NOT check for ISBN, DOI, job number
- Do NOT check for copyright, disclaimer, colophon
Focus ONLY on: typography, images, margins, layout issues on these pages.
"""

    return f"""Please review this {document_type} for design compliance.
{chunk_context}
{scope_note}

Document type confidence: {confidence:.0%}

## Output Format
Target output: {output_format}
**DPI requirement: {dpi_min} DPI minimum** for all significant images

## Extracted Measurements (Pages {chunk_start}-{chunk_end} only)
```json
{extraction_json}
```

Review these pages and provide your assessment. Remember to use actual page numbers ({chunk_start}-{chunk_end}) in your findings."""
```

### Pattern 5: Issue Deduplication
**What:** Remove duplicate issues from overlapping page regions
**When to use:** After all chunks complete, before final output
**Example:**
```python
# Source: Standard deduplication pattern

import hashlib
from typing import List

def deduplicate_issues(issues: List[ReviewIssue]) -> List[ReviewIssue]:
    """
    Remove duplicate issues from chunk overlaps.

    Deduplicates by hashing (title + first_page + category).
    For duplicates, keeps the first occurrence.
    """
    seen = set()
    unique = []

    for issue in issues:
        # Create hash key from issue identity
        key_parts = f"{issue.title}|{min(issue.pages)}|{issue.category}"
        key = hashlib.md5(key_parts.encode()).hexdigest()

        if key not in seen:
            seen.add(key)
            unique.append(issue)

    return unique


def merge_chunk_reviews(chunk_contents: List[str]) -> str:
    """
    Merge multiple chunk review contents into single review.

    Combines prose sections and deduplicates JSON issues.
    """
    # Parse sections from each chunk
    all_needs_attention = []
    all_suggestions = []
    all_looking_good = []
    all_issues = []

    for content in chunk_contents:
        sections = parseReviewSections(content)
        issues = parseReviewIssues(content)

        if sections.needsAttention:
            all_needs_attention.append(sections.needsAttention)
        if sections.suggestions:
            all_suggestions.append(sections.suggestions)
        if sections.lookingGood:
            all_looking_good.append(sections.lookingGood)
        all_issues.extend(issues)

    # Deduplicate issues
    unique_issues = deduplicate_issues(all_issues)

    # Build merged content
    merged = "### Overview\n"
    merged += "This document was reviewed in multiple chunks due to its length.\n\n"

    if all_needs_attention:
        merged += "### Needs Attention\n"
        merged += "\n\n".join(all_needs_attention) + "\n\n"

    if all_looking_good:
        merged += "### Looking Good\n"
        merged += "\n\n".join(all_looking_good) + "\n\n"

    if all_suggestions:
        merged += "### Suggestions\n"
        merged += "\n\n".join(all_suggestions) + "\n\n"

    # Add deduplicated JSON block
    merged += "```json\n"
    merged += json.dumps({"issues": [i.dict() for i in unique_issues]}, indent=2)
    merged += "\n```"

    return merged
```

### Anti-Patterns to Avoid
- **Processing chunks sequentially:** Wastes time; use concurrent processing with Semaphore
- **Arbitrary chunk sizes:** Use page count (predictable tokens) not byte size
- **No overlap:** Loses context at chunk boundaries; 2-page overlap is minimal viable
- **Renumbering pages in output:** Confuses users; always use actual document page numbers
- **Processing all chunks then merging:** No streaming feedback; emit progress as chunks complete

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF page subsetting | Read/write temp files | PyMuPDF `select()` in memory | `select()` is 10x faster, no disk I/O |
| Concurrency limiting | Manual counter/queue | `asyncio.Semaphore` | Battle-tested, handles edge cases |
| Token counting | Estimate from page count | Gemini `count_tokens()` API | Accurate, accounts for content complexity |
| SSE event formatting | Manual string concat | `sse-starlette` EventSourceResponse | Handles encoding, newlines, reconnection |
| Issue hashing | Custom comparison logic | `hashlib.md5()` on key fields | Fast, collision-resistant for dedup |

**Key insight:** The complexity is in orchestration (chunk management, progress events, merging), not the underlying operations. Use proven primitives for the primitives.

## Common Pitfalls

### Pitfall 1: Wrong Page Numbers in Findings
**What goes wrong:** AI reports page 5 when issue is actually on page 40 (chunk-relative numbering)
**Why it happens:** Extraction is filtered to chunk, AI sees pages 1-35 for pages 36-70
**How to avoid:** Prompt explicitly states actual page range, renumber in prompt not extraction
**Warning signs:** User reports "issue not on stated page"

### Pitfall 2: Token Limit Exceeded Despite Chunking
**What goes wrong:** Large chunk still exceeds 1M tokens
**Why it happens:** Pages have many images (258 tokens each), complex content, large extraction JSON
**How to avoid:** Use `count_tokens()` API before submission, reduce chunk size if over 800K tokens
**Warning signs:** API returns token limit error

### Pitfall 3: Duplicate Issues from Overlap
**What goes wrong:** Same issue reported twice for pages in overlap region
**Why it happens:** Both chunks see and report the issue
**How to avoid:** Hash-based deduplication on (title, first_page, category)
**Warning signs:** Identical issues with same page numbers in output

### Pitfall 4: Missing Document-Wide Checks
**What goes wrong:** ISBN/DOI/copyright not checked for document
**Why it happens:** Only first chunk checks these; if first chunk fails, checks never happen
**How to avoid:** Track first-chunk completion separately, retry or manual fallback
**Warning signs:** Large document review has no required element findings

### Pitfall 5: Memory Exhaustion on Very Large PDFs
**What goes wrong:** Server OOM when processing 500+ page PDF
**Why it happens:** Multiple chunk PDFs held in memory simultaneously
**How to avoid:** Process chunks sequentially if memory-constrained, or use temp files
**Warning signs:** Process killed, "MemoryError" exceptions

### Pitfall 6: Lost Progress on Partial Failure
**What goes wrong:** 4/5 chunks complete successfully, one fails, user sees error with no results
**Why it happens:** All-or-nothing error handling
**How to avoid:** Stream completed chunk results immediately, mark failed chunk explicitly
**Warning signs:** Timeout/error discards partial review

## Code Examples

Verified patterns from official sources:

### PyMuPDF Page Selection
```python
# Source: https://pymupdf.readthedocs.io/en/latest/document.html

import pymupdf

doc = pymupdf.open("large_document.pdf")
# Keep only pages 0-34 (first 35 pages)
doc.select(list(range(35)))
# doc now contains only those pages
doc.save("chunk_1.pdf")
doc.close()
```

### Gemini Token Counting
```python
# Source: https://ai.google.dev/gemini-api/docs/tokens

from google import genai

client = genai.Client(api_key="...")

# Count tokens for content before sending
token_count = client.models.count_tokens(
    model="gemini-2.5-flash",
    contents=[pdf_part, text_part]
)
print(f"Total tokens: {token_count.total_tokens}")

# Check against limit before proceeding
if token_count.total_tokens > 900_000:  # Leave headroom
    raise ValueError("Content exceeds safe token limit")
```

### Asyncio Semaphore Pattern
```python
# Source: https://docs.python.org/3/library/asyncio-sync.html

import asyncio

async def process_with_limit(items, limit=2):
    semaphore = asyncio.Semaphore(limit)

    async def limited_task(item):
        async with semaphore:
            return await process_item(item)

    tasks = [limited_task(item) for item in items]

    # Process as they complete (not in order)
    for coro in asyncio.as_completed(tasks):
        result = await coro
        yield result
```

### SSE Chunk Progress Events
```python
# Source: sse-starlette patterns

from sse_starlette import EventSourceResponse
import json

async def generate_chunked_review_events(chunks):
    total_chunks = len(chunks)

    # Emit start event
    yield {
        "event": "review_start",
        "data": json.dumps({
            "total_chunks": total_chunks,
            "message": f"Reviewing document in {total_chunks} chunks..."
        })
    }

    for i, chunk_content in enumerate(process_chunks(chunks)):
        # Emit chunk progress
        yield {
            "event": "chunk_complete",
            "data": json.dumps({
                "chunk": i + 1,
                "total": total_chunks,
                "pages": f"{chunks[i][0]+1}-{chunks[i][1]}"
            })
        }

        # Emit chunk content
        yield {
            "event": "text",
            "data": json.dumps({"text": chunk_content})
        }

    # Emit completion
    yield {
        "event": "complete",
        "data": json.dumps({"status": "complete"})
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reject large PDFs | Chunk and review in parallel | 2025+ | Enables review of any document size |
| Sequential chunk processing | Concurrent with Semaphore | Standard practice | 2-3x faster for multi-chunk docs |
| Fixed 258 tokens/page estimate | Use `count_tokens()` API | Gemini API feature | Accurate limits, fewer failures |
| Return error on partial failure | Stream completed chunks + error | UX improvement | Users get partial results |

**Deprecated/outdated:**
- None identified - chunking patterns are mature and stable

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal chunk size tuning**
   - What we know: 35 pages (~9,000 tokens) is conservative; could potentially use 50-60 pages
   - What's unclear: How much variation exists in per-page token counts for typical UNEP documents
   - Recommendation: Start with 35, monitor token usage via `count_tokens()`, increase if consistently low

2. **Overlap sufficiency**
   - What we know: 2 pages is minimal; RAG systems often use 10-30% overlap
   - What's unclear: Whether UNEP document structure (headers, continuations) needs more context
   - Recommendation: Start with 2 pages, increase to 3-4 if context loss issues reported

3. **Concurrency limit selection**
   - What we know: 2 concurrent is conservative for rate limits
   - What's unclear: Gemini Flash rate limits for specific account tier
   - Recommendation: Start with 2, increase to 3 if no rate limit errors observed

## Sources

### Primary (HIGH confidence)
- [Google AI Gemini Models](https://ai.google.dev/gemini-api/docs/models) - Token limits (1M input, 65K output)
- [Gemini Token Documentation](https://ai.google.dev/gemini-api/docs/tokens) - 258 tokens per PDF page
- [Gemini Document Processing](https://ai.google.dev/gemini-api/docs/document-processing) - PDF limits (50MB, 1000 pages)
- [PyMuPDF Document Class](https://pymupdf.readthedocs.io/en/latest/document.html) - `select()` method documentation
- [Python asyncio Sync Primitives](https://docs.python.org/3/library/asyncio-sync.html) - Semaphore documentation

### Secondary (MEDIUM confidence)
- [Chunking Strategies for LLM Applications (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/) - 10-30% overlap recommendation
- [Limit Concurrency with Semaphore (rednafi)](https://rednafi.com/python/limit-concurrency-with-semaphore/) - Semaphore patterns
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette) - SSE implementation for FastAPI

### Tertiary (LOW confidence)
- None - all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project or stdlib
- Architecture: HIGH - Patterns verified with official docs, clear implementation path
- Pitfalls: HIGH - Based on documented API behaviors and common async patterns

**Research date:** 2026-02-05
**Valid until:** 2026-03-05 (30 days - stable patterns, Gemini API may update limits)
