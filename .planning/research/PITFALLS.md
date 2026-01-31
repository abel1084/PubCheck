# Domain Pitfalls: PDF Design Compliance Checking

**Domain:** PDF publication design compliance verification
**Project:** PubCheck (UNEP PDF publication validator)
**Researched:** 2026-01-31
**Confidence:** HIGH (verified via PyMuPDF documentation, Anthropic API docs, industry sources)

---

## Critical Pitfalls

Mistakes that cause rewrites or major architectural issues.

---

### Pitfall 1: Font Name Normalization Failures

**What goes wrong:** Programmatic font checks produce massive false positives because the same font appears with different names in PDF metadata.

**Why it happens:** PDFs store fonts with variations including:
- Subset prefixes: `ABCDEF+Roboto-Regular` vs `Roboto-Regular`
- Style suffixes: `Roboto`, `Roboto-Regular`, `Roboto-Bold`, `RobotoBold`
- PostScript vs TrueType names: `ArialMT` vs `Arial`
- Encoding variations: Some fonts have encoding issues in their names ([PyMuPDF discussion #1934](https://github.com/pymupdf/PyMuPDF/discussions/1934))

**Consequences:**
- Valid documents flagged as non-compliant
- Users lose trust in the tool
- Support burden from false positive reports

**Prevention:**
1. **Normalize font names aggressively:**
   ```python
   def normalize_font_name(raw_name: str) -> str:
       # Strip subset prefix (6 uppercase + "+")
       if len(raw_name) > 7 and raw_name[6] == '+':
           raw_name = raw_name[7:]

       # Strip common suffixes
       for suffix in ['-Regular', '-Roman', 'MT', '-Identity-H']:
           raw_name = raw_name.replace(suffix, '')

       # Normalize case and whitespace
       return raw_name.lower().replace(' ', '').replace('-', '')
   ```

2. **Use PyMuPDF's subset control:**
   ```python
   import pymupdf
   pymupdf.TOOLS.set_subset_fontnames(False)  # Hide subset prefixes
   ```

3. **Build a font alias mapping** for known variations:
   ```python
   FONT_ALIASES = {
       'arial': ['arialmt', 'arial', 'arialnarrow'],
       'roboto': ['roboto', 'robotoregular', 'robotobold', 'robotolight'],
   }
   ```

**Detection:** Track false positive rate in production. If users frequently override font warnings, investigate normalization gaps.

**Phase:** Phase 1 (Core Parsing) - Must be solved before rule engine is useful.

**Sources:** [PyMuPDF Font Documentation](https://pymupdf.readthedocs.io/en/latest/font.html), [PyMuPDF Discussion #1934](https://github.com/pymupdf/PyMuPDF/discussions/1934)

---

### Pitfall 2: Text Reading Order Chaos

**What goes wrong:** Extracted text appears in wrong order, making paragraph/heading detection unreliable.

**Why it happens:** PDF is a visual format, not a logical document format. Text order in the file often reflects insertion order, not reading order:
- Headers inserted after body text appear at end
- Multi-column layouts interleave columns incorrectly
- Text boxes added as annotations appear out of order

**Consequences:**
- Heading detection fails (heading text mixed with body)
- Paragraph flow analysis produces garbage
- AI analysis receives scrambled context

**Prevention:**
1. **Always use sorting in PyMuPDF:**
   ```python
   # Sort by visual position (top-left to bottom-right)
   text = page.get_text("dict", sort=True)
   ```

2. **Use layout-preserving extraction:**
   ```bash
   python -m pymupdf gettext -layout input.pdf
   ```

3. **Detect multi-column layouts** before extraction:
   ```python
   def detect_columns(page):
       blocks = page.get_text("blocks", sort=True)
       # Analyze x-coordinate clustering to detect column boundaries
       x_coords = [b[0] for b in blocks]
       # Use clustering algorithm to find column boundaries
   ```

4. **Validate reading order** with AI for critical sections.

**Detection:** Compare extracted text against visual rendering. Large discrepancies indicate ordering issues.

**Phase:** Phase 1 (Core Parsing) - Fundamental to all downstream processing.

**Sources:** [PyMuPDF Common Issues](https://pymupdf.readthedocs.io/en/latest/recipes-common-issues-and-their-solutions.html), [PyMuPDF Text Extraction](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)

---

### Pitfall 3: Rasterized/Flattened PDF Detection Failure

**What goes wrong:** The system attempts text extraction on image-only PDFs and produces garbage or nothing, without warning the user.

**Why it happens:** Some PDFs are:
- Scanned documents (no text layer at all)
- Flattened for print (text converted to outlines/images)
- "Printed to PDF" from applications that rasterize

**Consequences:**
- Silent failures in text-based checks (fonts, spacing, etc.)
- Misleading compliance reports (no issues found because no text extracted)
- User confusion about why checks don't work

**Prevention:**
1. **Detect image-only pages early:**
   ```python
   def is_image_only_page(page) -> bool:
       text = page.get_text("text").strip()
       images = page.get_images()

       # Heuristic: minimal text + large images = likely rasterized
       if len(text) < 50 and len(images) > 0:
           # Check if images cover most of page
           page_area = page.rect.width * page.rect.height
           for img in images:
               xref = img[0]
               img_rect = page.get_image_bbox(xref)
               if img_rect and (img_rect.width * img_rect.height) > page_area * 0.8:
                   return True
       return False
   ```

2. **Warn users prominently** when rasterized content detected:
   ```
   WARNING: Page 3 appears to be rasterized/scanned.
   Text-based checks (fonts, spacing) cannot be performed.
   Only visual checks via AI analysis are available.
   ```

3. **Offer OCR option** for scanned documents (using OCRmyPDF or PyMuPDF OCR).

4. **Track page types** in analysis metadata:
   ```python
   page_info = {
       "page_num": 1,
       "type": "rasterized" | "native" | "mixed",
       "text_extractable": True | False,
       "checks_available": ["visual", "color"]  # No font/text checks
   }
   ```

**Detection:** Log text extraction yield per page. Pages with < 10 characters warrant investigation.

**Phase:** Phase 1 (Core Parsing) - Detection must happen before any rule checking.

**Sources:** [OCRmyPDF Introduction](https://ocrmypdf.readthedocs.io/en/latest/introduction.html), [PyMuPDF OCR Recipes](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html)

---

### Pitfall 4: Coordinate System Confusion

**What goes wrong:** Margin calculations, bounding box comparisons, and position-based checks produce incorrect results.

**Why it happens:** PDF has multiple coordinate systems:
- PDF coordinates: origin at bottom-left, Y increases upward
- PyMuPDF default: origin at top-left, Y increases downward
- Different DPI assumptions (72 DPI in PDF points)
- CropBox vs MediaBox vs ArtBox confusion

**Consequences:**
- Margins calculated from wrong edge
- Element positions reported incorrectly
- Annotation placement in wrong location on output PDF

**Prevention:**
1. **Standardize on one coordinate system** project-wide:
   ```python
   # Use PyMuPDF's default (top-left origin) consistently
   # Document this choice prominently

   # When converting, be explicit:
   def pdf_coords_to_pymupdf(x, y, page_height):
       """Convert PDF coordinates (bottom-left origin) to PyMuPDF (top-left)."""
       return x, page_height - y
   ```

2. **Use the correct page rectangle:**
   ```python
   # MediaBox = physical page size
   # CropBox = visible/printable area (use this for margin calculations)
   # TrimBox = intended final size after trimming

   page_rect = page.cropbox  # Not page.rect (which is MediaBox)
   ```

3. **Calculate margins from CropBox:**
   ```python
   def calculate_margins(page, content_bbox):
       crop = page.cropbox
       return {
           "top": content_bbox.y0 - crop.y0,
           "bottom": crop.y1 - content_bbox.y1,
           "left": content_bbox.x0 - crop.x0,
           "right": crop.x1 - content_bbox.x1,
       }
   ```

4. **Unit conversion helpers:**
   ```python
   def points_to_mm(points: float) -> float:
       return points * 25.4 / 72

   def mm_to_points(mm: float) -> float:
       return mm * 72 / 25.4
   ```

**Detection:** Visual verification of annotated output PDFs. If annotations appear offset, coordinate handling is wrong.

**Phase:** Phase 1 (Core Parsing) - Foundational for all spatial analysis.

**Sources:** [PyMuPDF Basics - Coordinates](https://pymupdf.readthedocs.io/en/latest/the-basics.html)

---

### Pitfall 5: AI Inconsistency Across Runs

**What goes wrong:** Same PDF analyzed twice produces different compliance verdicts.

**Why it happens:**
- LLM outputs are inherently probabilistic
- Prompt variations (image quality, context length)
- Temperature settings not controlled
- Image compression artifacts in different runs

**Consequences:**
- User confusion and distrust
- "Try again and it might pass" gaming
- Impossible to reproduce issues for debugging

**Prevention:**
1. **Set temperature to 0** for deterministic checks:
   ```python
   response = client.messages.create(
       model="claude-sonnet-4-20250514",
       temperature=0,  # Deterministic output
       messages=[...]
   )
   ```

2. **Use structured output schemas:**
   ```python
   from anthropic import Anthropic

   # Force structured JSON output
   system_prompt = """
   You are a design compliance checker. Respond ONLY with valid JSON:
   {
       "compliant": true|false,
       "confidence": "high"|"medium"|"low",
       "issues": [{"type": "...", "description": "...", "location": "..."}]
   }
   """
   ```

3. **Consistent image preprocessing:**
   ```python
   def prepare_image_for_analysis(page, dpi=150):
       """Always render at same DPI and format."""
       pix = page.get_pixmap(dpi=dpi)
       # Convert to PNG with consistent compression
       return pix.tobytes("png")
   ```

4. **Cache AI verdicts** with content hash:
   ```python
   def get_cached_verdict(page_hash, rule_id):
       # Return cached result if page content unchanged
       pass
   ```

5. **Implement confidence thresholds:**
   ```python
   if result["confidence"] == "low":
       # Flag for human review instead of auto-verdict
       return "NEEDS_REVIEW"
   ```

**Detection:** Run same document through system 3 times. Any variance indicates inconsistency problem.

**Phase:** Phase 2 (AI Integration) - Must be addressed when implementing AI verification.

**Sources:** [Claude API Rate Limits](https://docs.claude.com/en/api/rate-limits), [Structured Outputs for LLMs](https://generative-ai-newsroom.com/structured-outputs-making-llms-reliable-for-document-processing-c3b6b2baed36)

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

---

### Pitfall 6: Color Matching Tolerance Miscalibration

**What goes wrong:** Color checks are either too strict (flagging acceptable variations) or too loose (missing real violations).

**Why it happens:**
- RGB/CMYK color space differences
- Monitor calibration variations
- Perceptual vs mathematical color distance
- Not using industry-standard Delta-E

**Prevention:**
1. **Use Delta-E 2000** for color comparison:
   ```python
   from colormath.color_objects import LabColor
   from colormath.color_diff import delta_e_cie2000

   def colors_match(color1_lab, color2_lab, tolerance=2.0):
       """Delta-E < 2.0 is generally imperceptible."""
       delta = delta_e_cie2000(color1_lab, color2_lab)
       return delta < tolerance
   ```

2. **Convert to LAB color space** for comparison:
   ```python
   # RGB and CMYK are device-dependent
   # LAB is perceptually uniform
   def rgb_to_lab(r, g, b):
       # Use colormath or colour-science library
       pass
   ```

3. **Industry-standard thresholds:**
   - Delta-E < 1.0: Imperceptible difference
   - Delta-E < 2.0: Minor difference, trained eye only
   - Delta-E < 3.5: Noticeable but acceptable for most uses
   - Delta-E > 5.0: Clearly different colors

4. **Document color space expectations** in rules:
   ```yaml
   brand_blue:
     rgb: [0, 80, 158]
     cmyk: [100, 50, 0, 38]
     tolerance_delta_e: 3.0  # Allow print variation
   ```

**Phase:** Phase 2 (Rule Engine) - When implementing color compliance checks.

**Sources:** [Delta-E Color Difference Survey](https://www.researchgate.net/publication/236023905_Color_difference_Delta_E_-_A_survey), [Color Accuracy and Delta-E](https://formlabs.com/blog/color-accuracy-delta-e/)

---

### Pitfall 7: Image Extraction Complexity

**What goes wrong:** Images appear corrupted, have wrong colors, or are missing from extraction.

**Why it happens:**
- Images with masks/transparency need special handling
- CMYK images need color space conversion for display
- Stencil masks (transparency) extracted as separate images
- Multi-layer/overdraw images appear as fragments

**Prevention:**
1. **Handle color space conversion:**
   ```python
   def extract_image_as_rgb(doc, xref):
       pix = pymupdf.Pixmap(doc, xref)

       # Convert CMYK to RGB
       if pix.colorspace and pix.colorspace.n > 3:
           pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

       # Handle transparency
       if pix.alpha:
           pix = pymupdf.Pixmap(pix, 0)  # Remove alpha for simpler handling

       return pix
   ```

2. **Skip stencil masks:**
   ```python
   for img in page.get_images(full=True):
       xref = img[0]
       if img[1] != 0:  # Has mask reference
           # This is a masked image, handle specially
           pass
   ```

3. **Use extract_image() for format preservation:**
   ```python
   img_data = doc.extract_image(xref)
   # Returns dict with "image" (bytes), "ext" (format), dimensions
   # Preserves original JPEG without re-encoding
   ```

**Phase:** Phase 1 (Core Parsing) - When implementing image analysis.

**Sources:** [PyMuPDF Images Documentation](https://pymupdf.readthedocs.io/en/latest/recipes-images.html), [pikepdf Images](https://pikepdf.readthedocs.io/en/latest/topics/images.html)

---

### Pitfall 8: API Cost Explosion

**What goes wrong:** Claude API costs spiral out of control during development or production.

**Why it happens:**
- Sending full-resolution images when thumbnails suffice
- Analyzing every page when sampling would work
- No caching of repeated analyses
- Development testing without limits

**Prevention:**
1. **Implement aggressive caching:**
   ```python
   import hashlib

   def get_page_hash(page):
       pix = page.get_pixmap(dpi=72)  # Low-res for hashing
       return hashlib.sha256(pix.tobytes()).hexdigest()

   def analyze_with_cache(page, rule_id, cache):
       page_hash = get_page_hash(page)
       cache_key = f"{page_hash}:{rule_id}"

       if cache_key in cache:
           return cache[cache_key]

       result = call_claude_api(page, rule_id)
       cache[cache_key] = result
       return result
   ```

2. **Use appropriate image resolution:**
   ```python
   # For text/layout checks: 150 DPI sufficient
   # For color checks: 72 DPI often enough
   # For fine detail: 300 DPI only when needed

   dpi_by_check = {
       "layout": 150,
       "color": 72,
       "logo_placement": 200,
       "fine_typography": 300,
   }
   ```

3. **Batch multiple checks per API call:**
   ```python
   # Instead of 10 API calls for 10 rules:
   prompt = """
   Analyze this page for ALL of the following:
   1. Header placement
   2. Logo positioning
   3. Margin compliance
   4. Color usage
   ...
   Return results for each check.
   """
   ```

4. **Use Anthropic's Batch API** for non-urgent processing:
   - 50% cost reduction
   - 24-hour processing window
   - Perfect for bulk/nightly analysis

5. **Implement spending alerts:**
   ```python
   class CostTracker:
       def __init__(self, daily_limit_usd=10.0):
           self.daily_limit = daily_limit_usd
           self.daily_spent = 0.0

       def check_budget(self, estimated_cost):
           if self.daily_spent + estimated_cost > self.daily_limit:
               raise BudgetExceededError("Daily API budget exceeded")
   ```

**Phase:** Phase 2 (AI Integration) - Must be designed from the start.

**Sources:** [Claude API Rate Limits](https://docs.claude.com/en/api/rate-limits), [Claude Pricing Guide](https://www.aifreeapi.com/en/posts/claude-api-quota-tiers-limits)

---

### Pitfall 9: Rate Limit Handling

**What goes wrong:** Bulk document processing fails partway through due to rate limits.

**Why it happens:**
- Anthropic rate limits are per-organization, not per-key
- Token limits (RPM, ITPM, OTPM) vary by tier
- Burst usage hits limits even if average is fine
- No backoff/retry logic implemented

**Prevention:**
1. **Implement exponential backoff with jitter:**
   ```python
   import time
   import random

   def call_with_retry(func, max_retries=5):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise

               # Exponential backoff with jitter
               wait = (2 ** attempt) + random.uniform(0, 1)

               # Use retry-after header if provided
               if hasattr(e, 'retry_after'):
                   wait = e.retry_after

               time.sleep(wait)
   ```

2. **Use prompt caching** to reduce token usage:
   ```python
   # Cached tokens don't count toward ITPM limits
   # Cache system prompts and repeated context
   ```

3. **Implement request queuing:**
   ```python
   from asyncio import Queue, sleep

   class RateLimitedQueue:
       def __init__(self, requests_per_minute=50):
           self.rpm = requests_per_minute
           self.interval = 60.0 / requests_per_minute

       async def process(self, request):
           await sleep(self.interval)
           return await self.execute(request)
   ```

4. **Monitor usage proactively:**
   - Track requests/tokens per minute
   - Alert at 80% of limit
   - Throttle before hitting limits

**Phase:** Phase 2 (AI Integration) - Required for production reliability.

**Sources:** [Claude Rate Limits Documentation](https://platform.claude.com/docs/en/api/rate-limits), [Fixing 429 Errors](https://www.aifreeapi.com/en/posts/fix-claude-api-429-rate-limit-error)

---

### Pitfall 10: Multi-Column Layout Confusion

**What goes wrong:** Text extraction interleaves columns, margin detection fails on columnar pages.

**Why it happens:**
- PyMuPDF's default sorting doesn't understand columns
- Content bounding box spans both columns (wrong margins)
- Reading order jumps between columns

**Prevention:**
1. **Detect columns before extraction:**
   ```python
   def detect_columns(page):
       blocks = page.get_text("dict", sort=True)["blocks"]

       # Cluster x-coordinates of text blocks
       x_positions = []
       for block in blocks:
           if block["type"] == 0:  # Text block
               x_positions.append(block["bbox"][0])  # Left edge

       # Simple 2-column detection: bimodal x distribution
       if x_positions:
           median_x = sorted(x_positions)[len(x_positions)//2]
           left_col = [x for x in x_positions if x < median_x - 50]
           right_col = [x for x in x_positions if x > median_x + 50]

           if len(left_col) > 3 and len(right_col) > 3:
               return "two_column"

       return "single_column"
   ```

2. **Calculate margins per column:**
   ```python
   def calculate_columnar_margins(page, layout_type):
       if layout_type == "single_column":
           # Use overall content bounds
           pass
       elif layout_type == "two_column":
           # Calculate margins from outer edges only
           # Ignore the gutter between columns
           pass
   ```

3. **Use layout analysis libraries** for complex layouts:
   - [pdf-document-layout-analysis](https://github.com/huridocs/pdf-document-layout-analysis)
   - Document Layout Analysis models (YOLO, DINO-based)

**Phase:** Phase 2 (Rule Engine) - When implementing margin checks.

**Sources:** [PDF Document Layout Analysis](https://github.com/huridocs/pdf-document-layout-analysis), [PyMuPDF Text Extraction](https://pymupdf.readthedocs.io/en/latest/app1.html)

---

### Pitfall 11: Tagged PDF Parsing Assumptions

**What goes wrong:** Accessibility tag structure used for analysis produces incorrect results on untagged PDFs.

**Why it happens:**
- Many PDFs lack proper tagging
- Tags may be present but incorrect/incomplete
- Tag structure doesn't match visual structure

**Prevention:**
1. **Check for tags before using:**
   ```python
   def has_valid_tags(doc):
       try:
           # Check if document has structure tree
           catalog = doc.pdf_catalog()
           if "StructTreeRoot" not in catalog:
               return False
           # Further validation...
           return True
       except:
           return False
   ```

2. **Fall back to visual analysis** when tags unavailable or unreliable.

3. **Don't assume tags = accessibility compliant:**
   - Tags may be auto-generated and wrong
   - Reading order in tags may not match visual
   - Always verify against visual rendering

**Phase:** Phase 1 (Core Parsing) - When implementing structure analysis.

**Sources:** [Adobe Accessibility Checker](https://helpx.adobe.com/acrobat/using/create-verify-pdf-accessibility.html), [Tagged PDF Internals](https://www.overleaf.com/learn/latex/An_introduction_to_tagged_PDF_files%3A_internals_and_the_challenges_of_accessibility)

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

---

### Pitfall 12: Word Boundary Detection Failures

**What goes wrong:** Text extraction has no spaces or spaces between every letter.

**Why it happens:**
- PDF stores glyphs, not words
- Space detection depends on glyph positioning
- Some PDFs use small x-gaps that look like word spaces visually

**Prevention:**
```python
# Use appropriate flags
text = page.get_text("text", flags=pymupdf.TEXT_INHIBIT_SPACES)

# Or use dict extraction and reconstruct with proper spacing
blocks = page.get_text("dict")
```

**Phase:** Phase 1 (Core Parsing).

**Sources:** [PyMuPDF Bounding Box Discussion](https://github.com/pymupdf/PyMuPDF/discussions/3250)

---

### Pitfall 13: Missing Character Glyphs

**What goes wrong:** Some characters extract as `?` or empty boxes.

**Why it happens:**
- Font lacks character mapping (CMAP)
- Custom/decorative fonts without proper Unicode mapping
- Subset fonts missing glyphs

**Prevention:**
1. Detect and flag pages with high unknown character rates
2. Fall back to AI-based text recognition for problematic pages
3. Report font embedding issues to user

**Phase:** Phase 1 (Core Parsing).

**Sources:** [PyMuPDF Text Extraction Details](https://pymupdf.readthedocs.io/en/latest/app1.html)

---

### Pitfall 14: Encoding Detection Failures

**What goes wrong:** Non-Latin text (Arabic, Chinese, etc.) extracts as garbage.

**Why it happens:**
- Font encoding not properly specified
- Complex script rendering issues
- Right-to-left text ordering problems

**Prevention:**
1. Detect script/language of document
2. Test extraction on representative sample pages
3. Have language-specific extraction paths if needed

**Phase:** Phase 1 (Core Parsing) - Important for UNEP's multilingual publications.

---

## UX Pitfalls

User experience issues that undermine adoption.

---

### Pitfall 15: Issue Overload

**What goes wrong:** Users presented with 200+ issues feel overwhelmed and abandon the tool.

**Why it happens:**
- Every minor deviation flagged equally
- No prioritization or grouping
- Same issue repeated per-page instead of summarized

**Prevention:**
1. **Categorize by severity:**
   ```python
   class IssueSeverity(Enum):
       CRITICAL = "critical"  # Must fix before publication
       MAJOR = "major"        # Should fix
       MINOR = "minor"        # Nice to fix
       INFO = "info"          # FYI only
   ```

2. **Group similar issues:**
   ```
   Instead of:
   - Page 1: Wrong font (Arial instead of Roboto)
   - Page 2: Wrong font (Arial instead of Roboto)
   - Page 3: Wrong font (Arial instead of Roboto)

   Show:
   - Wrong font used: Arial instead of Roboto (Pages 1-3, 5, 7-12)
   ```

3. **Progressive disclosure:**
   - Show summary first: "12 Critical, 45 Major, 89 Minor issues"
   - Expand to see categories
   - Drill down to individual issues

4. **Actionable first:**
   - Lead with issues the user can actually fix
   - Deprioritize issues that require designer intervention

**Phase:** Phase 3 (Review Interface) - Core UX design consideration.

**Sources:** [UX Debt Prioritization](https://www.nngroup.com/articles/ux-debt/), [Compliance UI Best Practices](https://cadabra.studio/blog/ui-ux-design-regulated-industries/)

---

### Pitfall 16: Learning System Scope Confusion

**What goes wrong:** Users don't understand if their feedback affects only this document, their templates, or the global system.

**Why it happens:**
- Three scopes (global, template, document) not clearly communicated
- Feedback UI doesn't indicate scope
- Users expect document-level overrides to "stick" globally

**Prevention:**
1. **Make scope explicit in UI:**
   ```
   [ ] Apply to this document only
   [ ] Apply to all "Annual Report" templates
   [ ] Suggest as global rule change (requires admin review)
   ```

2. **Show scope indicators on learned rules:**
   ```
   Rule: "Allow 0.5cm margin tolerance"
   Scope: Template (Annual Report 2024)
   Applied: 3 documents
   ```

3. **Confirmation dialogs for scope-changing actions.**

4. **Scope inheritance visualization:**
   - Show which rules come from global vs template vs document

**Phase:** Phase 4 (Learning System) - Critical for learning system usability.

---

### Pitfall 17: Feedback Loop Without Closure

**What goes wrong:** Users provide feedback but never see it reflected, leading to distrust.

**Why it happens:**
- Feedback stored but not processed
- Learning takes too long to be visible
- No notification when feedback is applied

**Prevention:**
1. **Immediate acknowledgment:**
   ```
   "Thanks! This override saved for future Annual Reports."
   ```

2. **Show learning in action:**
   ```
   "Based on your previous feedback, we're allowing 5mm margin
   variation on this template."
   ```

3. **Feedback audit trail** accessible to users.

**Phase:** Phase 4 (Learning System) - User trust mechanism.

---

### Pitfall 18: AI vs Programmatic Check Conflicts

**What goes wrong:** Programmatic check says "PASS" but AI check says "FAIL" (or vice versa), confusing users.

**Why it happens:**
- Different tolerance thresholds
- AI sees visual context that programmatic check doesn't
- Edge cases where both are partially right

**Prevention:**
1. **Define clear hierarchy:**
   - Programmatic checks are authoritative for measurable properties
   - AI checks are advisory for subjective/visual properties
   - When both run, programmatic result takes precedence for measurable items

2. **Show reasoning for both:**
   ```
   Programmatic check: PASS (margin = 25mm, required >= 20mm)
   AI assessment: WARNING (margin appears visually cramped)

   Final verdict: PASS with note
   ```

3. **Use AI to verify, not override:**
   - AI confirms programmatic results in edge cases
   - AI adds context, doesn't contradict measurements

**Phase:** Phase 2 (Rule Engine) - When combining check types.

---

## Phase Mapping Summary

| Pitfall | Severity | Phase to Address |
|---------|----------|------------------|
| Font Name Normalization | Critical | Phase 1 (Core Parsing) |
| Text Reading Order | Critical | Phase 1 (Core Parsing) |
| Rasterized PDF Detection | Critical | Phase 1 (Core Parsing) |
| Coordinate System Confusion | Critical | Phase 1 (Core Parsing) |
| AI Inconsistency | Critical | Phase 2 (AI Integration) |
| Color Matching Tolerance | Moderate | Phase 2 (Rule Engine) |
| Image Extraction Complexity | Moderate | Phase 1 (Core Parsing) |
| API Cost Explosion | Moderate | Phase 2 (AI Integration) |
| Rate Limit Handling | Moderate | Phase 2 (AI Integration) |
| Multi-Column Layout | Moderate | Phase 2 (Rule Engine) |
| Tagged PDF Parsing | Moderate | Phase 1 (Core Parsing) |
| Word Boundary Detection | Minor | Phase 1 (Core Parsing) |
| Missing Character Glyphs | Minor | Phase 1 (Core Parsing) |
| Encoding Detection | Minor | Phase 1 (Core Parsing) |
| Issue Overload | UX | Phase 3 (Review Interface) |
| Learning Scope Confusion | UX | Phase 4 (Learning System) |
| Feedback Loop Closure | UX | Phase 4 (Learning System) |
| AI vs Programmatic Conflicts | UX | Phase 2 (Rule Engine) |

---

## Research Gaps

Areas where pitfall detection was incomplete:

1. **Performance at scale** - How system behaves with 100+ page documents not fully researched
2. **Specific UNEP guidelines** - May have domain-specific pitfalls unique to their design system
3. **Print vs screen PDF differences** - CMYK/press-ready PDFs may have additional extraction challenges
4. **Annotation output pitfalls** - Creating annotated PDFs has its own set of issues not covered here

---

## Sources

### Primary (HIGH confidence)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [PyMuPDF Common Issues](https://pymupdf.readthedocs.io/en/latest/recipes-common-issues-and-their-solutions.html)
- [Claude API Rate Limits](https://docs.claude.com/en/api/rate-limits)
- [Delta-E Color Difference](https://www.researchgate.net/publication/236023905_Color_difference_Delta_E_-_A_survey)

### Secondary (MEDIUM confidence)
- [Python PDF Extractors Comparison 2025](https://dev.to/onlyoneaman/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-akm)
- [Structured Outputs for LLMs](https://generative-ai-newsroom.com/structured-outputs-making-llms-reliable-for-document-processing-c3b6b2baed36)
- [PDF Document Layout Analysis](https://github.com/huridocs/pdf-document-layout-analysis)
- [UX in Regulated Industries](https://cadabra.studio/blog/ui-ux-design-regulated-industries/)
