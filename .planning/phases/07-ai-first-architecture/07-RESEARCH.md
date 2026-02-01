# Phase 7: AI-First Architecture Overhaul - Research

**Researched:** 2026-02-01
**Domain:** AI-driven document compliance, Claude PDF support, streaming responses, architecture migration
**Confidence:** HIGH

## Summary

This phase fundamentally restructures PubCheck from a programmatic-check-with-AI-augmentation system to an AI-first architecture where Claude makes ALL compliance decisions. The research confirms a clear implementation path: use Claude's native PDF support (not rendered screenshots), pass the entire document in one API call with extracted measurements as structured JSON, and stream the response for real-time UI updates.

The key architectural change is removing the `checks/` module entirely (executor, handlers, router) and replacing it with a single AI review endpoint. The extractor becomes measurement-only (stripping all compliance logic), and the frontend transforms from a categorized issue list to a prose-based review interface with sectioned cards. Claude's native PDF support accepts base64-encoded PDFs up to 100 pages, with each page processed as both text and image for full visual understanding.

Streaming is essential for UX during AI processing. FastAPI supports SSE via `sse-starlette`, and the Anthropic SDK provides `client.messages.stream()` with `text_stream` for incremental text output. The frontend receives streaming text and displays it progressively in sectioned cards (Overview, Needs Attention, Looking Good, Suggestions).

**Primary recommendation:** Replace the entire check pipeline with a single streaming AI review endpoint that sends the original PDF + extracted measurements + rules context to Claude, streaming back prose-style review content organized by priority sections.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.35.0 | Claude API Python SDK | Official SDK with native PDF support, streaming, async |
| sse-starlette | 3.2.0 | Server-Sent Events for FastAPI | Production-ready SSE, automatic disconnect detection |
| pymupdf | >=1.26.0 | PDF extraction (measurements only) | Already in stack, continues extraction role |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 1.10.x | Request/response models | AI response schema, extraction models |
| aiofiles | >=24.1.0 | Async file operations | Temp PDF file handling |
| httpx | >=0.27.0 | Async HTTP client | Optional aiohttp backend for anthropic |

### Removed
| Library | Reason |
|---------|--------|
| checks module handlers | Replaced by AI-driven decisions |
| tolerance.py | Measurements kept, compliance judgments removed |

**Installation:**
```bash
pip install anthropic>=0.35.0 sse-starlette==3.2.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── ai/                      # AI review module (EXISTING, MODIFIED)
│   │   ├── __init__.py
│   │   ├── client.py           # MODIFY: Add PDF support, streaming
│   │   ├── reviewer.py         # NEW: Single-call document reviewer
│   │   ├── prompts.py          # MODIFY: Collegial review prompts
│   │   ├── schemas.py          # MODIFY: AIReviewResult with sections
│   │   └── router.py           # MODIFY: Streaming SSE endpoint
│   ├── services/
│   │   ├── pdf_extractor.py    # MODIFY: Measurements only, no violations
│   │   └── ...
│   ├── config/
│   │   ├── rules_context/      # NEW: Markdown rules files
│   │   │   ├── working_paper.md
│   │   │   ├── publication.md
│   │   │   ├── brief.md
│   │   │   └── factsheet.md
│   │   └── ...
│   └── checks/                  # DELETE ENTIRE MODULE
│       ├── executor.py          # DELETE
│       ├── handlers/            # DELETE
│       └── ...
```

### Pattern 1: Native PDF Document Input
**What:** Send original PDF to Claude using document content block (not rendered images)
**When to use:** All document reviews
**Example:**
```python
# backend/app/ai/client.py
import anthropic
import base64

class AIReviewClient:
    """Claude API client with native PDF support."""

    def __init__(self):
        self._client = anthropic.Anthropic()
        self._model = "claude-sonnet-4-5"

    async def review_document_stream(
        self,
        pdf_bytes: bytes,
        extraction_json: str,
        rules_context: str,
        document_type: str,
        confidence: float,
    ):
        """
        Stream document review using Claude's native PDF support.

        Sends: Original PDF + extracted measurements + rules markdown
        Returns: Async generator of text chunks
        """
        pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        async with self._client.messages.stream(
            model=self._model,
            max_tokens=8192,
            system=self._build_system_prompt(rules_context),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            }
                        },
                        {
                            "type": "text",
                            "text": self._build_user_prompt(
                                extraction_json,
                                document_type,
                                confidence
                            ),
                        }
                    ],
                }
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text
```

### Pattern 2: Streaming SSE Response
**What:** Stream AI review to frontend using Server-Sent Events
**When to use:** AI review endpoint
**Example:**
```python
# backend/app/ai/router.py
from fastapi import APIRouter, UploadFile, File, Form
from sse_starlette import EventSourceResponse
import json

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/review")
async def review_document(
    file: UploadFile = File(...),
    extraction: str = Form(...),
    document_type: str = Form(...),
    confidence: float = Form(...),
):
    """
    Stream AI document review via SSE.

    Client receives text chunks as they're generated.
    """
    pdf_bytes = await file.read()

    async def generate_events():
        client = get_ai_client()
        rules_context = load_rules_context(document_type)

        async for text_chunk in client.review_document_stream(
            pdf_bytes=pdf_bytes,
            extraction_json=extraction,
            rules_context=rules_context,
            document_type=document_type,
            confidence=confidence,
        ):
            yield {"event": "text", "data": json.dumps({"text": text_chunk})}

        yield {"event": "complete", "data": "{}"}

    return EventSourceResponse(generate_events())
```

### Pattern 3: Collegial Review System Prompt
**What:** System prompt that produces helpful colleague review style
**When to use:** All document reviews
**Example:**
```python
# backend/app/ai/prompts.py

SYSTEM_PROMPT = """You are a helpful colleague reviewing UNEP publications for design compliance. Your review should read like feedback from an experienced designer who wants the document to succeed.

## Review Style
- Be collegial and constructive: "The logo looks a bit small at 18mm - spec asks for 20mm minimum"
- Cite measurements when relevant: sizes, margins, DPI values
- Use honest hedging when uncertain: "This might be intentional, but..."
- No formal confidence scores - express uncertainty naturally in prose

## Response Structure
Organize your review into these sections, using markdown headers:

### Overview
Brief 2-3 sentence summary of the document's compliance state.

### Needs Attention
Issues that should be fixed before publication. Group related issues naturally.
Each issue should explain what's wrong and suggest a fix.

### Looking Good
Specific things the document does well. Acknowledge good design work.

### Suggestions
Minor improvements that would enhance the document but aren't requirements.

## Common Pitfalls to Avoid in Your Analysis
- Full-bleed images are intentional design, not margin violations
- Decorative elements (thin lines, bullets, icons) don't need DPI checks
- Small accent images may intentionally use lower resolution
- Headers/footers have different margin rules than body content

## What You're Checking
You'll receive:
1. The original PDF document
2. Extracted measurements as JSON (fonts, images, margins, text blocks)
3. Document type with confidence score - validate this matches the actual document

{rules_context}
"""

def build_user_prompt(extraction_json: str, document_type: str, confidence: float) -> str:
    return f"""Please review this {document_type} for design compliance.

Document type confidence: {confidence:.0%}
{"(Please verify this is actually a " + document_type + ")" if confidence < 0.8 else ""}

## Extracted Measurements
```json
{extraction_json}
```

Review the document and provide your assessment using the section structure from your instructions."""
```

### Pattern 4: Rules Context as Markdown
**What:** Type-specific rules as prose + measurements in markdown files
**When to use:** Loaded and injected into system prompt
**Example:**
```markdown
# config/rules_context/working_paper.md

## Working Paper Design Requirements

### Cover Page
- UNEP logo: top-right corner, minimum 20mm width, target 27.5mm
- Title: clear hierarchy, readable at a glance
- UN Blue (#0099CC) used for accents is preferred

### Typography
- Body text: 10-12pt, preferably Roboto or similar sans-serif
- Minimum text size: 7pt for footnotes
- Consistent font usage throughout (avoid mixing more than 3 font families)

### Images
- Photos: minimum 150 DPI at print size, 300 DPI preferred
- Logos and diagrams: vector or 300+ DPI
- All images should have adequate contrast and be clearly visible

### Margins
- Minimum margins: 15mm on all sides
- Inside margins (binding edge): may be slightly larger (20mm)
- Full-bleed images are acceptable and intentional

### Required Elements
- ISBN on back cover or copyright page
- DOI if assigned
- Copyright notice
- Publication date
- UNEP contact information
```

### Pattern 5: Frontend Streaming Display
**What:** React component that receives and displays streaming text
**When to use:** AI review results display
**Example:**
```typescript
// frontend/src/hooks/useAIReview.ts
import { useState, useCallback } from 'react';

interface ReviewState {
  content: string;
  isStreaming: boolean;
  isComplete: boolean;
  error: string | null;
}

export function useAIReview() {
  const [state, setState] = useState<ReviewState>({
    content: '',
    isStreaming: false,
    isComplete: false,
    error: null,
  });

  const startReview = useCallback(async (
    file: File,
    extraction: ExtractionResult,
    documentType: string,
    confidence: number,
  ) => {
    setState({ content: '', isStreaming: true, isComplete: false, error: null });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('extraction', JSON.stringify(extraction));
    formData.append('document_type', documentType);
    formData.append('confidence', confidence.toString());

    try {
      const response = await fetch('/api/ai/review', {
        method: 'POST',
        body: formData,
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // Parse SSE format
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.text) {
              setState(prev => ({
                ...prev,
                content: prev.content + data.text,
              }));
            }
          }
        }
      }

      setState(prev => ({ ...prev, isStreaming: false, isComplete: true }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Review failed',
      }));
    }
  }, []);

  return { ...state, startReview };
}
```

### Pattern 6: Sectioned Review Cards
**What:** Display streaming review content in sectioned cards
**When to use:** AI review results UI
**Example:**
```typescript
// frontend/src/components/ReviewResults/ReviewResults.tsx
import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';

interface ReviewResultsProps {
  content: string;
  isStreaming: boolean;
}

// Parse markdown content into sections
function parseReviewSections(content: string) {
  const sections = {
    overview: '',
    needsAttention: '',
    lookingGood: '',
    suggestions: '',
  };

  const sectionPatterns = [
    { key: 'overview', pattern: /### Overview\n([\s\S]*?)(?=###|$)/ },
    { key: 'needsAttention', pattern: /### Needs Attention\n([\s\S]*?)(?=###|$)/ },
    { key: 'lookingGood', pattern: /### Looking Good\n([\s\S]*?)(?=###|$)/ },
    { key: 'suggestions', pattern: /### Suggestions\n([\s\S]*?)(?=###|$)/ },
  ];

  for (const { key, pattern } of sectionPatterns) {
    const match = content.match(pattern);
    if (match) {
      sections[key as keyof typeof sections] = match[1].trim();
    }
  }

  return sections;
}

export function ReviewResults({ content, isStreaming }: ReviewResultsProps) {
  const sections = useMemo(() => parseReviewSections(content), [content]);

  return (
    <div className="review-results">
      {sections.overview && (
        <section className="review-results__section review-results__section--overview">
          <h3>Overview</h3>
          <ReactMarkdown>{sections.overview}</ReactMarkdown>
        </section>
      )}

      {sections.needsAttention && (
        <section className="review-results__section review-results__section--attention">
          <h3>Needs Attention</h3>
          <ReactMarkdown>{sections.needsAttention}</ReactMarkdown>
        </section>
      )}

      {sections.lookingGood && (
        <section className="review-results__section review-results__section--good">
          <h3>Looking Good</h3>
          <ReactMarkdown>{sections.lookingGood}</ReactMarkdown>
        </section>
      )}

      {sections.suggestions && (
        <section className="review-results__section review-results__section--suggestions">
          <h3>Suggestions</h3>
          <ReactMarkdown>{sections.suggestions}</ReactMarkdown>
        </section>
      )}

      {isStreaming && (
        <div className="review-results__streaming-indicator">
          Reviewing document...
        </div>
      )}
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Rendering PDF to images:** Claude has native PDF support. Use `type: "document"` not rendered screenshots.
- **Page-by-page analysis:** Process entire document in one call for cross-page consistency.
- **Structured JSON output for review:** Prose review is more natural. Only structure issues array for PDF annotations.
- **Keeping programmatic checks alongside AI:** Delete the checks module entirely - AI makes all decisions.
- **Buffering entire response before display:** Stream text to UI for responsiveness.
- **Per-page rate limiting:** Single document call eliminates the need.
- **Confidence scores in output:** Express uncertainty naturally in prose ("might be intentional").

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE streaming | Custom StreamingResponse | sse-starlette | Handles disconnects, ping, proper format |
| PDF to Claude | Render as images | Native PDF document type | Better text extraction, visual understanding |
| Streaming text consumption | Manual chunk parsing | SDK's `text_stream` | Handles all event types correctly |
| Markdown parsing in React | Regex parsing | react-markdown | Handles edge cases, XSS safe |
| Section splitting | Complex regex | Heading-based split | More maintainable, handles partial content |
| Response accumulation | Manual string concat | SDK stream helpers | `get_final_message()` for complete text |

**Key insight:** Claude's native PDF support extracts text AND renders each page as an image, providing both text search and visual analysis in one call. This is superior to rendering screenshots manually.

## Common Pitfalls

### Pitfall 1: PDF Size Limits
**What goes wrong:** Documents over 100 pages fail or get truncated
**Why it happens:** Claude PDF support has 100-page limit with full visual analysis
**How to avoid:**
- Validate page count before sending
- For larger docs, consider text-only mode or splitting
- Warn users about limits upfront
**Warning signs:** API errors on large documents

### Pitfall 2: Token Costs with PDFs
**What goes wrong:** Unexpectedly high API costs
**Why it happens:** Each PDF page uses 1,500-3,000 tokens (text + image)
**How to avoid:**
- Estimate cost before processing: pages x ~2,500 tokens avg
- Consider prompt caching for repeated rules context
- Display cost estimate to users
**Warning signs:** Bills higher than expected

### Pitfall 3: Streaming Connection Drops
**What goes wrong:** Partial review displayed, no completion
**Why it happens:** Network issues, client navigates away, timeout
**How to avoid:**
- Use sse-starlette's disconnect detection
- Implement client-side reconnection
- Save partial content locally
- Handle `complete` event explicitly
**Warning signs:** Reviews that end mid-sentence

### Pitfall 4: Inconsistent Section Formatting
**What goes wrong:** AI doesn't always use exact section headers
**Why it happens:** LLM output variability
**How to avoid:**
- Use clear instructions with exact headers
- Parse sections flexibly (case-insensitive, variations)
- Fall back to showing raw markdown if parsing fails
**Warning signs:** Empty sections when content exists

### Pitfall 5: False Positives from Extractor
**What goes wrong:** AI flags issues based on incorrect measurements
**Why it happens:** Extractor reports decorative elements as content
**How to avoid:**
- Include extraction caveats in system prompt
- AI should verify measurements against visual inspection
- Bake common false positive patterns into prompt
**Warning signs:** AI flagging obvious false positives

### Pitfall 6: Slow Initial Response
**What goes wrong:** Long wait before any text appears
**Why it happens:** PDF processing and analysis before streaming starts
**How to avoid:**
- Show "Processing document..." immediately
- Consider showing extraction results while waiting
- Set appropriate timeout expectations (60+ seconds for large docs)
**Warning signs:** Users abandoning before response starts

## Code Examples

Verified patterns from official sources:

### Complete PDF Document Analysis Request
```python
# Source: https://platform.claude.com/docs/en/docs/build-with-claude/pdf-support
import anthropic
import base64

client = anthropic.Anthropic()

# Load PDF file
with open("document.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=8192,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": "Review this document for design compliance."
                }
            ]
        }
    ],
)
print(message.content)
```

### Async Streaming with SDK
```python
# Source: https://platform.claude.com/docs/en/api/messages-streaming
# Source: https://github.com/anthropics/anthropic-sdk-python
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def stream_review(pdf_base64: str, prompt: str):
    async with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
    ) as stream:
        async for text in stream.text_stream:
            yield text

        # Get final message for usage stats
        final_message = await stream.get_final_message()
        print(f"Tokens used: {final_message.usage}")
```

### FastAPI SSE Endpoint
```python
# Source: https://pypi.org/project/sse-starlette/
from fastapi import APIRouter, UploadFile, File, Form
from sse_starlette import EventSourceResponse
import json

router = APIRouter()

@router.post("/api/ai/review")
async def review_document(
    file: UploadFile = File(...),
    extraction: str = Form(...),
    document_type: str = Form(...),
    confidence: float = Form(...),
):
    pdf_bytes = await file.read()

    async def generate():
        async for chunk in stream_review(pdf_bytes, extraction, document_type):
            yield {"data": json.dumps({"text": chunk})}
        yield {"event": "complete", "data": "{}"}

    return EventSourceResponse(
        generate(),
        media_type="text/event-stream",
    )
```

### Frontend EventSource Client
```typescript
// Standard EventSource API for SSE consumption
function streamReview(formData: FormData, onChunk: (text: string) => void) {
  return new Promise<void>((resolve, reject) => {
    fetch('/api/ai/review', {
      method: 'POST',
      body: formData,
    }).then(response => {
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            resolve();
            return;
          }

          const text = decoder.decode(value);
          const lines = text.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.text) {
                  onChunk(data.text);
                }
              } catch (e) {
                // Skip malformed JSON
              }
            }
          }

          read();
        }).catch(reject);
      }

      read();
    }).catch(reject);
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Render PDF pages as images | Native PDF document type | Nov 2024 | Better text + visual understanding |
| Page-by-page analysis | Full document in one call | Best practice | Cross-page consistency |
| Programmatic checks + AI verification | AI-only compliance decisions | This phase | Simpler architecture, better UX |
| Structured JSON responses | Prose review with sections | This phase | More natural, collegial feedback |
| Per-rule ignore settings | Universal rules per doc type | This phase | Simpler config, better AI context |

**Deprecated/outdated:**
- `type: "image"` for PDFs: Use `type: "document"` with `media_type: "application/pdf"`
- Temperature>0 for compliance: Still use temperature=0 for consistency
- Tool use for structured output: Native `output_format` or prose is simpler
- Page-by-page processing: Loses cross-page context

## Open Questions

Things that couldn't be fully resolved:

1. **Structured issues array for PDF annotations**
   - What we know: Frontend needs issue positions for PDF annotations
   - What's unclear: How to get structured data from prose review
   - Recommendation: Include separate JSON issues array in response OR parse prose client-side OR make a second structured call

2. **Optimal max_tokens for reviews**
   - What we know: Typical review might be 500-2000 tokens
   - What's unclear: What's the right limit to prevent runaway responses?
   - Recommendation: Start with 8192, monitor actual usage, adjust

3. **Document type validation failure handling**
   - What we know: AI validates document type and may disagree with detection
   - What's unclear: What happens if AI says "this isn't a working paper"?
   - Recommendation: Include in Overview section, let user override if needed

4. **Cost display to users**
   - What we know: Users may want to know cost before reviewing
   - What's unclear: How to estimate without calling API (page count x ~2500 tokens)
   - Recommendation: Show estimated cost based on page count before review

## Sources

### Primary (HIGH confidence)
- [Claude PDF Support Documentation](https://platform.claude.com/docs/en/docs/build-with-claude/pdf-support) - Native PDF input, limits, best practices
- [Claude Messages Streaming](https://platform.claude.com/docs/en/api/messages-streaming) - SSE format, event types, SDK helpers
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) - AsyncAnthropic, stream(), text_stream
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - EventSourceResponse, FastAPI integration
- Existing codebase: `ai/client.py`, `ai/analyzer.py`, `App.tsx` - Current patterns to migrate

### Secondary (MEDIUM confidence)
- [FastAPI SSE Patterns](https://medium.com/@nandagopal05/server-sent-events-with-python-fastapi-f1960e0c8e4b) - Integration patterns
- WebSearch: AI-first architecture patterns 2026 - General guidance on LLM-centric systems

### Tertiary (LOW confidence)
- WebSearch: Collegial review writing style - Subjective, will need iteration on prompts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Anthropic SDK, official SSE library
- PDF support: HIGH - Official Claude documentation, verified API
- Streaming: HIGH - SDK provides clear patterns, FastAPI SSE well documented
- Prompt engineering: MEDIUM - Collegial style will need iteration
- Frontend patterns: MEDIUM - Standard React patterns, section parsing needs testing

**Research date:** 2026-02-01
**Valid until:** 60 days (PDF support GA, streaming stable)
