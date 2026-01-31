# Phase 4: AI Verification - Research

**Researched:** 2026-01-31
**Domain:** Claude Vision API, structured outputs, PDF/image analysis for document verification
**Confidence:** HIGH

## Summary

This phase implements AI-augmented verification for visual checks that programmatic rules struggle with. The research confirms a straightforward integration path: use the Anthropic Python SDK with Claude's vision capabilities to analyze page images, structured outputs via Pydantic for reliable response parsing, and content-hash caching for cost control.

The existing Phase 3 check infrastructure provides a clean extension point. AI verification can be implemented as a new check handler type ("ai_vision") that integrates seamlessly with the existing `CheckExecutor` pattern. The handler renders PDF pages to images using PyMuPDF (already in the stack), sends them to Claude with structured prompts, and returns `CheckIssue` objects like any other handler.

Key technical decisions are driven by requirements: temperature=0 for deterministic results, Pydantic models for structured outputs (matching existing v1 patterns), and selective verification with content-hash caching to control costs. The Anthropic SDK provides native support for both base64 image input and Pydantic schema integration.

**Primary recommendation:** Implement AI verification as a new check handler type that renders pages to images, calls Claude Vision with temperature=0 and structured outputs, then returns CheckIssue objects compatible with existing results UI.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.35.0 | Claude API Python SDK | Official Anthropic SDK with vision and structured output support |
| pydantic | 1.10.x | Response validation schemas | Already in use, SDK supports Pydantic v1 |
| pymupdf | >=1.26.0 | PDF page to image rendering | Already in stack, provides page.get_pixmap() for image conversion |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | built-in | Content hash for caching | Cache key generation from page content |
| base64 (stdlib) | built-in | Image encoding | Encode page images for API transmission |
| aiofiles | >=24.1.0 | Async file operations | Already in stack, cache file I/O |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct anthropic SDK | instructor library | Instructor adds convenience but anthropic SDK has native Pydantic support now |
| Base64 image encoding | Files API | Files API is beta, base64 is stable and works for ephemeral use |
| Temperature=0 | Extended thinking | Extended thinking adds cost and latency, not needed for verification |

**Installation:**
```bash
pip install anthropic>=0.35.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── checks/
│   │   ├── handlers/
│   │   │   ├── ai_vision.py      # NEW: AI vision verification handler
│   │   │   └── ...existing handlers
│   │   ├── ai/                    # NEW: AI verification module
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # Anthropic client singleton
│   │   │   ├── schemas.py        # Pydantic response schemas
│   │   │   ├── prompts.py        # Verification prompts
│   │   │   ├── cache.py          # Content-hash caching
│   │   │   └── renderer.py       # PDF page to image rendering
│   │   └── executor.py           # Add ai_vision handler registration
│   └── ...existing modules
```

### Pattern 1: AI Verification Handler
**What:** New check handler type for AI-powered visual verification
**When to use:** Visual checks that can't be done programmatically (logo detection, image quality, layout balance)
**Example:**
```python
# backend/app/checks/handlers/ai_vision.py
from typing import List
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..ai.client import get_ai_client
from ..ai.schemas import AIVerificationResult
from ..ai.renderer import render_page_to_base64
from ..ai.prompts import build_verification_prompt

async def check_ai_vision(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected,
    pdf_path: str,  # Path to PDF file for rendering
) -> List[CheckIssue]:
    """
    Execute AI vision verification.

    Renders relevant pages to images, sends to Claude for analysis,
    returns structured verification results.
    """
    issues: List[CheckIssue] = []
    exp = expected.dict() if hasattr(expected, 'dict') else dict(expected)

    verification_type = exp.get("verification_type", "")
    target_pages = exp.get("pages", [0])  # 0-indexed, default to first page

    client = get_ai_client()

    for page_num in target_pages:
        # Render page to base64 image
        image_data = render_page_to_base64(pdf_path, page_num)

        # Build prompt for this verification type
        prompt = build_verification_prompt(verification_type, rule, exp)

        # Call Claude with structured output
        result = await client.verify_page(
            image_data=image_data,
            prompt=prompt,
            response_schema=AIVerificationResult,
        )

        if not result.passed:
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message=result.issue_description,
                expected=result.expected_description,
                actual=result.actual_description,
                pages=[page_num + 1],  # 1-indexed for display
                how_to_fix=result.how_to_fix,
                ai_confidence=result.confidence,  # NEW field
                ai_reasoning=result.reasoning,     # NEW field
            ))

    return issues
```

### Pattern 2: Structured Output Schema
**What:** Pydantic models for Claude's verification responses
**When to use:** All AI verification responses
**Example:**
```python
# backend/app/checks/ai/schemas.py
from typing import Literal, Optional
from pydantic import BaseModel, Field

class AIVerificationResult(BaseModel):
    """Structured response from AI verification."""

    passed: bool = Field(
        description="Whether the verification check passed"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the verification result"
    )
    reasoning: str = Field(
        description="Explanation of why the check passed or failed"
    )
    issue_description: Optional[str] = Field(
        None,
        description="Description of the issue if check failed"
    )
    expected_description: Optional[str] = Field(
        None,
        description="What was expected if check failed"
    )
    actual_description: Optional[str] = Field(
        None,
        description="What was actually found if check failed"
    )
    how_to_fix: Optional[str] = Field(
        None,
        description="Suggestion for fixing the issue"
    )

    class Config:
        # Pydantic v1 config
        extra = "forbid"


class LogoVerificationResult(AIVerificationResult):
    """Extended result for logo verification."""

    logo_detected: bool = Field(
        description="Whether a UNEP logo was detected"
    )
    logo_position: Optional[str] = Field(
        None,
        description="Detected position of logo (top-right, top-left, etc.)"
    )
    logo_size_adequate: Optional[bool] = Field(
        None,
        description="Whether logo size meets minimum requirements"
    )


class ImageQualityResult(AIVerificationResult):
    """Extended result for image quality assessment."""

    blur_detected: bool = Field(
        description="Whether blur or softness was detected"
    )
    artifacts_detected: bool = Field(
        description="Whether compression artifacts were detected"
    )
    noise_detected: bool = Field(
        description="Whether excessive noise was detected"
    )
    quality_score: Literal["good", "acceptable", "poor"] = Field(
        description="Overall quality assessment"
    )


class LayoutBalanceResult(AIVerificationResult):
    """Extended result for layout balance assessment."""

    alignment_issues: bool = Field(
        description="Whether alignment issues were detected"
    )
    balance_issues: bool = Field(
        description="Whether visual balance issues were detected"
    )
    spacing_issues: bool = Field(
        description="Whether spacing inconsistencies were detected"
    )
```

### Pattern 3: Anthropic Client with Structured Outputs
**What:** Singleton client wrapper for Claude API calls with Pydantic integration
**When to use:** All AI verification requests
**Example:**
```python
# backend/app/checks/ai/client.py
import os
from typing import Type, TypeVar
import anthropic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AIVerificationClient:
    """Wrapper for Anthropic Claude API with structured outputs."""

    def __init__(self):
        self._client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self._model = os.getenv("AI_VERIFICATION_MODEL", "claude-sonnet-4-5")

    async def verify_page(
        self,
        image_data: str,
        prompt: str,
        response_schema: Type[T],
    ) -> T:
        """
        Send page image to Claude for verification.

        Uses temperature=0 for deterministic results.
        Uses structured outputs for reliable parsing.

        Args:
            image_data: Base64-encoded image data
            prompt: Verification prompt
            response_schema: Pydantic model for response

        Returns:
            Parsed and validated response
        """
        # Use the SDK's parse() method for automatic schema handling
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=1024,
            temperature=0,  # Deterministic for verification
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            output_format=response_schema,
        )

        return response.parsed_output


# Singleton instance
_client: AIVerificationClient = None

def get_ai_client() -> AIVerificationClient:
    """Get or create AI verification client singleton."""
    global _client
    if _client is None:
        _client = AIVerificationClient()
    return _client
```

### Pattern 4: PDF Page to Image Rendering
**What:** Convert PDF pages to base64-encoded images for Claude
**When to use:** Before sending to AI verification
**Example:**
```python
# backend/app/checks/ai/renderer.py
import base64
import pymupdf

def render_page_to_base64(
    pdf_path: str,
    page_num: int,
    dpi: int = 150,  # Balance quality vs token cost
    max_dimension: int = 1568,  # Claude's optimal size
) -> str:
    """
    Render a PDF page to a base64-encoded PNG image.

    Optimizes for Claude's vision capabilities:
    - 150 DPI provides good quality at reasonable token cost
    - Max 1568px on any side per Claude recommendations
    - PNG format for lossless text clarity

    Args:
        pdf_path: Path to PDF file
        page_num: 0-indexed page number
        dpi: Resolution for rendering (default 150)
        max_dimension: Maximum pixels on any edge

    Returns:
        Base64-encoded PNG image data
    """
    doc = pymupdf.open(pdf_path)

    try:
        page = doc[page_num]

        # Calculate zoom to hit target DPI
        zoom = dpi / 72.0  # PyMuPDF default is 72 DPI
        mat = pymupdf.Matrix(zoom, zoom)

        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Scale down if exceeds max dimension
        if pix.width > max_dimension or pix.height > max_dimension:
            scale = max_dimension / max(pix.width, pix.height)
            new_width = int(pix.width * scale)
            new_height = int(pix.height * scale)

            # Re-render at scaled size
            new_zoom = zoom * scale
            mat = pymupdf.Matrix(new_zoom, new_zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to PNG bytes and base64 encode
        png_bytes = pix.tobytes("png")
        return base64.standard_b64encode(png_bytes).decode("utf-8")

    finally:
        doc.close()
```

### Pattern 5: Content-Hash Caching
**What:** Cache AI verification results by content hash to avoid repeated API calls
**When to use:** All AI verification to control costs
**Example:**
```python
# backend/app/checks/ai/cache.py
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

CACHE_DIR = Path(".cache/ai_verification")

def get_content_hash(
    image_data: str,
    prompt: str,
    schema_name: str,
) -> str:
    """
    Generate hash key from image content, prompt, and schema.

    Changes to any of these invalidate the cache.
    """
    content = f"{image_data}:{prompt}:{schema_name}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_cached_result(
    cache_key: str,
    schema: type[T],
) -> Optional[T]:
    """
    Retrieve cached verification result if exists.

    Returns None if not cached or cache is invalid.
    """
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        return schema.parse_obj(data)
    except Exception:
        # Invalid cache, return None
        return None


def cache_result(
    cache_key: str,
    result: BaseModel,
) -> None:
    """
    Store verification result in cache.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    with open(cache_file, "w") as f:
        json.dump(result.dict(), f)


# Integration with client
async def verify_with_cache(
    client: "AIVerificationClient",
    image_data: str,
    prompt: str,
    response_schema: type[T],
) -> T:
    """
    Verify with caching layer.

    Checks cache first, calls API only if not cached.
    """
    cache_key = get_content_hash(image_data, prompt, response_schema.__name__)

    # Try cache first
    cached = get_cached_result(cache_key, response_schema)
    if cached is not None:
        return cached

    # Call API
    result = await client.verify_page(image_data, prompt, response_schema)

    # Cache result
    cache_result(cache_key, result)

    return result
```

### Pattern 6: Extended CheckIssue for AI Results
**What:** Add AI-specific fields to CheckIssue model
**When to use:** Displaying AI verification results in UI
**Example:**
```python
# Update backend/app/checks/models.py
from typing import List, Literal, Optional
from pydantic import BaseModel

class CheckIssue(BaseModel):
    """A single compliance issue found during checking."""
    rule_id: str
    rule_name: str
    severity: Literal["error", "warning"]
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    pages: List[int]
    how_to_fix: Optional[str] = None

    # NEW: AI verification fields
    ai_verified: bool = False  # True if this was an AI check
    ai_confidence: Optional[Literal["high", "medium", "low"]] = None
    ai_reasoning: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
```

### Anti-Patterns to Avoid

- **Calling AI for every check:** Only use AI for visual checks that can't be done programmatically. Use heuristic pre-filters first.
- **Not caching results:** AI calls are expensive. Always cache by content hash.
- **Using high temperature:** Always use temperature=0 for deterministic verification results.
- **Sending full PDFs:** Render only the specific pages needed, not the entire document.
- **Large image sizes:** Keep images under 1568px on longest edge to avoid Claude's resizing overhead.
- **Ignoring confidence levels:** Always expose confidence to users so they can validate low-confidence results.
- **Synchronous AI calls in request path:** Consider async patterns or background processing for multiple checks.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured output parsing | Custom JSON parsing | anthropic SDK's `messages.parse()` | Handles schema validation, retries, error cases |
| Pydantic schema to JSON schema | Manual conversion | SDK's `transform_schema()` | Handles edge cases, adds description metadata |
| PDF page rendering | PIL/custom code | PyMuPDF's `get_pixmap()` | Already in stack, handles complex PDFs correctly |
| Logo detection prompts | Generic prompts | Specific verification prompts | Domain-specific prompts significantly improve accuracy |
| Response validation | Manual field checks | Pydantic model validation | Type-safe, automatic, handles Optional fields |
| Cache invalidation | Manual tracking | Content-based hashing | Automatic invalidation when content changes |

**Key insight:** The Anthropic SDK now provides native Pydantic support via `messages.parse()` method. This handles schema transformation, response validation, and error handling automatically. Don't use the older tool-use pattern for structured outputs.

## Common Pitfalls

### Pitfall 1: API Key Exposure
**What goes wrong:** API key committed to repo or exposed in frontend
**Why it happens:** Quick testing without proper config management
**How to avoid:** Use environment variables, never hardcode keys
**Warning signs:** API key in any Python file, .env committed to git

### Pitfall 2: Token Cost Explosion
**What goes wrong:** AI verification costs more than expected
**Why it happens:** Large images, many pages, no caching, repeated calls
**How to avoid:**
- Render at 150 DPI, max 1568px
- Cache by content hash
- Pre-filter with heuristics (only AI-verify if programmatic check fails)
- Batch verification where possible
**Warning signs:** API costs increasing linearly with document volume

### Pitfall 3: Timeout on Large Documents
**What goes wrong:** AI verification times out or blocks UI
**Why it happens:** Processing many pages sequentially
**How to avoid:**
- Set reasonable timeout (60 seconds per phase requirements)
- Process pages in parallel where possible
- Show progress indicator
- Fail fast if time budget exhausted
**Warning signs:** Requests exceeding 60 second requirement

### Pitfall 4: Inconsistent Results Without Temperature=0
**What goes wrong:** Same document gets different verification results
**Why it happens:** Default temperature > 0 introduces randomness
**How to avoid:** Always set `temperature=0` for verification tasks
**Warning signs:** Flaky tests, user complaints about inconsistent results

### Pitfall 5: Schema Validation Failures
**What goes wrong:** `messages.parse()` fails with schema errors
**Why it happens:** Pydantic v2 syntax used with v1, unsupported schema features
**How to avoid:**
- Use Pydantic v1 class Config syntax (project requirement)
- Avoid unsupported JSON Schema features (see docs)
- Test schemas with sample responses
**Warning signs:** 400 errors mentioning schema, validation exceptions

### Pitfall 6: Prompt Injection via Document Content
**What goes wrong:** Malicious document content affects AI behavior
**Why it happens:** Document text included in prompt without sanitization
**How to avoid:**
- Use images rather than extracted text for verification
- If using text, clearly separate it from instructions
- Use structured output constraints to limit response format
**Warning signs:** Unexpected AI responses, verification bypasses

### Pitfall 7: Missing Confidence Calibration
**What goes wrong:** Users don't know when to trust AI results
**Why it happens:** Confidence not surfaced in UI, or AI overconfident
**How to avoid:**
- Always include confidence in response schema
- Display confidence prominently in UI
- Consider requiring human review for low confidence
**Warning signs:** Users treating all AI results as authoritative

## Code Examples

Verified patterns from official sources:

### Complete AI Verification Request
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/vision
# Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
import anthropic
from pydantic import BaseModel, Field
from typing import Literal, Optional

class LogoVerificationResult(BaseModel):
    """Structured response for logo verification."""
    passed: bool
    confidence: Literal["high", "medium", "low"]
    logo_detected: bool
    logo_position: Optional[str] = None
    reasoning: str
    issue_description: Optional[str] = None
    how_to_fix: Optional[str] = None

client = anthropic.Anthropic()

response = client.messages.parse(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    temperature=0,  # Deterministic
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64,  # From render_page_to_base64()
                    },
                },
                {
                    "type": "text",
                    "text": """Analyze this PDF cover page for UNEP logo verification.

Check for:
1. Is a UNEP (United Nations Environment Programme) logo present?
2. Is it positioned in the top-right corner area?
3. Is it at least 20mm in apparent size?

The UNEP logo features a stylized human figure within laurel leaves,
often with "UNEP" or "UN Environment" text."""
                }
            ],
        }
    ],
    output_format=LogoVerificationResult,
)

result = response.parsed_output
print(f"Passed: {result.passed}")
print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning}")
```

### Page Rendering with PyMuPDF
```python
# Source: PyMuPDF documentation, verified in existing codebase
import base64
import pymupdf

def render_page_for_ai(pdf_path: str, page_num: int) -> str:
    """Render page optimized for Claude Vision."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]

    # 150 DPI balances quality and token cost
    # ~1590 tokens for 1092x1092 image per Claude docs
    zoom = 150 / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    # Scale if needed (max 1568px per Claude recommendation)
    if max(pix.width, pix.height) > 1568:
        scale = 1568 / max(pix.width, pix.height)
        mat = pymupdf.Matrix(zoom * scale, zoom * scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)

    png_bytes = pix.tobytes("png")
    doc.close()

    return base64.standard_b64encode(png_bytes).decode("utf-8")
```

### Verification Prompt Templates
```python
# backend/app/checks/ai/prompts.py

LOGO_VERIFICATION_PROMPT = """Analyze this PDF cover page for logo verification.

Check for the {logo_name} logo:
1. Is the logo present and clearly visible?
2. Is it positioned in the {expected_position} area?
3. Does it appear to be at least {min_size_mm}mm in size?

{logo_description}

Respond with your analysis including confidence level (high/medium/low).
If the check fails, explain what was found and how to fix it."""

IMAGE_QUALITY_PROMPT = """Analyze the images on this PDF page for quality issues.

Check for:
1. Blur or softness that reduces readability
2. Compression artifacts (blocky areas, color banding)
3. Excessive noise or graininess
4. Pixelation from over-enlargement

Focus on images that are meant to be high quality (photos, diagrams).
Ignore intentionally stylized or low-resolution elements.

Rate overall image quality as: good, acceptable, or poor.
Explain any issues found and their severity."""

LAYOUT_BALANCE_PROMPT = """Analyze this PDF page layout for design issues.

Check for:
1. Element alignment - are similar elements aligned consistently?
2. Visual balance - is content distributed evenly across the page?
3. Spacing consistency - are margins and gaps between elements uniform?
4. Text/image relationships - do captions align with their images?

Focus on obvious issues that would be noticeable to a typical reader.
Minor variations in alignment (under 2mm) can be ignored.

Describe any issues found and suggest corrections."""

def build_verification_prompt(
    verification_type: str,
    rule,
    expected: dict,
) -> str:
    """Build prompt for specific verification type."""
    if verification_type == "logo":
        return LOGO_VERIFICATION_PROMPT.format(
            logo_name=expected.get("logo_name", "UNEP"),
            expected_position=expected.get("position", "top-right"),
            min_size_mm=expected.get("min_size_mm", 20),
            logo_description=expected.get("logo_description", ""),
        )
    elif verification_type == "image_quality":
        return IMAGE_QUALITY_PROMPT
    elif verification_type == "layout_balance":
        return LAYOUT_BALANCE_PROMPT
    else:
        raise ValueError(f"Unknown verification type: {verification_type}")
```

### Integration with Existing Check Executor
```python
# Update backend/app/checks/executor.py
from .handlers import (
    check_position,
    check_range,
    check_font,
    check_regex,
    check_presence,
    check_color,
)
from .handlers.ai_vision import check_ai_vision  # NEW

def create_executor() -> CheckExecutor:
    executor = CheckExecutor()
    executor.register("position", check_position)
    executor.register("range", check_range)
    executor.register("font", check_font)
    executor.register("regex", check_regex)
    executor.register("presence", check_presence)
    executor.register("color", check_color)
    executor.register("ai_vision", check_ai_vision)  # NEW
    return executor
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tool use for structured output | Native `output_format` parameter | 2025 | Simpler, more reliable |
| Manual JSON parsing | `messages.parse()` with Pydantic | 2025 | Type-safe, automatic validation |
| External image URLs | Base64 in request body | Stable | Works offline, no hosting needed |
| Generic vision prompts | Domain-specific verification prompts | Best practice | Much higher accuracy |

**Deprecated/outdated:**
- `beta.prompt_caching.messages.create()`: Now just `messages.create()` with cache_control
- Tool use for structured outputs: Use `output_format` parameter instead
- anthropic-beta headers for structured outputs: Now generally available

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal DPI for different verification types**
   - What we know: 150 DPI is a good balance, Claude docs recommend max 1568px
   - What's unclear: Whether logo detection needs higher resolution than layout checks
   - Recommendation: Start with 150 DPI, increase selectively if accuracy issues

2. **Confidence threshold for automatic pass/fail**
   - What we know: AI returns high/medium/low confidence
   - What's unclear: What threshold should require human review?
   - Recommendation: Display all confidence levels, let users configure threshold

3. **Cost projection per document**
   - What we know: ~1600 tokens per page image at optimal size, $3/million input tokens for Sonnet
   - What's unclear: Actual average tokens with structured output overhead
   - Recommendation: Implement token counting and cost tracking

4. **Fallback when API unavailable**
   - What we know: AI verification is augmentation, not replacement for programmatic checks
   - What's unclear: How to gracefully degrade if API is down
   - Recommendation: Mark AI checks as "pending" if API fails, allow manual override

## Sources

### Primary (HIGH confidence)
- [Claude Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) - Image input, formats, sizing, token costs
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - Pydantic integration, SDK methods
- [Claude Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) - Cache control, pricing, TTL
- [Claude PDF Support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) - Page limits, rendering approach
- Existing codebase: `checks/executor.py`, `checks/models.py`, `image_processor.py` - Established patterns

### Secondary (MEDIUM confidence)
- [Instructor Library Anthropic Integration](https://python.useinstructor.com/integrations/anthropic/) - Alternative approach for structured outputs
- [PyMuPDF get_pixmap documentation](https://pymupdf.readthedocs.io/) - Page rendering API

### Tertiary (LOW confidence)
- WebSearch results for temperature=0 determinism - Note: Not fully deterministic even at 0
- WebSearch results for vision best practices - Community patterns, not official

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Anthropic SDK, existing PyMuPDF
- Architecture patterns: HIGH - Follows existing handler registry pattern
- Structured outputs: HIGH - Official SDK documentation verified
- Caching strategy: MEDIUM - Content hash approach is standard, implementation details to validate
- Prompt engineering: MEDIUM - Domain-specific prompts will need iteration

**Research date:** 2026-01-31
**Valid until:** 60 days (API stable, structured outputs GA)
