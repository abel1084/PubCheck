# Roadmap: PubCheck

**Created:** 2026-01-31
**Phases:** 6
**Requirements:** 43 mapped

## Overview

PubCheck delivers automated UNEP PDF design compliance checking through a layered pipeline: PDF parsing and extraction (foundation), rule configuration (engine), design compliance checks (core value), AI verification (edge cases), interactive review (user experience), and learning with output generation (completeness). Each phase builds on the previous, delivering incremental value while maintaining a clear dependency chain.

---

## Phase 1: PDF Foundation & Extraction

**Goal:** Users can upload PDFs and see extracted content (text, images, metadata) with reliable coordinate and font information.

**Requirements:**
- UPLD-01: User can upload PDF via drag-and-drop or file browser
- UPLD-02: System auto-detects document type from page count, keywords, ISBN presence
- UPLD-03: System rejects flattened/rasterized PDFs with accessibility explanation
- EXTR-01: Extract text with x/y coordinates, font name, size, weight, color
- EXTR-02: Extract images with DPI, dimensions, color space
- EXTR-03: Calculate margins from content bounding boxes
- EXTR-04: Extract document metadata (title, author, ISBN, DOI, job number)

**Success Criteria:**
1. User can drag a PDF onto the application and see it accepted or rejected with clear feedback
2. User can see the detected document type (Factsheet, Policy Brief, etc.) with manual override option
3. User can view extracted text with font information displayed per text block
4. User can view extracted images with DPI and dimensions shown
5. User can see calculated margins for each page

**Dependencies:** None

**Research Notes:** PyMuPDF patterns well-established. Must implement font name normalization (strip subset prefixes), sorted text extraction for reading order, and rasterized detection early.

---

## Phase 2: Rule Configuration Engine

**Goal:** Users can configure UNEP design rules via YAML templates and a settings UI before running compliance checks.

**Requirements:**
- CONF-01: Rules stored in YAML template files (3 templates covering 5 document types)
- CONF-02: Settings UI with tabbed interface to edit template rules
- CONF-03: User can enable/disable individual rules
- CONF-04: User can set severity per rule (Error/Warning)

**Success Criteria:**
1. User can open Settings and see three template tabs (Factsheet, Brief/Paper, Publication)
2. User can toggle any rule on/off and see the change reflected immediately
3. User can change rule severity between Error and Warning
4. User can see rule changes persist after closing and reopening the application

**Dependencies:** Phase 1 (needs working application scaffold)

**Research Notes:** YAML configuration pattern standard. Rule engine must support conditional logic and multiple check types (font size, color matching, margin measurement, regex patterns).

---

## Phase 3: Design Compliance Checks

**Goal:** Users can run compliance checks against uploaded PDFs and see categorized findings with severity levels.

**Requirements:**
- COVR-01: Validate UNEP logo position (top-right) and size (min 20mm, target 27.5mm)
- COVR-02: Validate title typography (font, size range 28-34pt)
- COVR-03: Validate subtitle typography (font, size range 12-14pt)
- COVR-04: Validate partner logo placement (smaller than UNEP, correct position)
- MRGN-01: Validate top margin within range (20-25mm)
- MRGN-02: Validate bottom margin within range (20mm min)
- MRGN-03: Validate inside margin within range (20-30mm)
- MRGN-04: Validate outside margin within range (20-25mm)
- TYPO-01: Validate body text font matches template (Roboto Flex)
- TYPO-02: Validate body text size within range (9-12pt)
- TYPO-03: Validate heading hierarchy (H1-H4 fonts, sizes, weights)
- TYPO-04: Validate caption font and size (7pt Roboto)
- TYPO-05: Validate chart text font (8pt Roboto Condensed)
- IMAG-01: Validate image DPI meets minimum (300 DPI)
- IMAG-02: Validate image color space (RGB or CMYK as specified)
- REQD-01: Check presence of ISBN (for Publications)
- REQD-02: Check presence of DOI
- REQD-03: Check presence of job number
- REQD-04: Check presence of disclaimer text (exact match)
- REQD-05: Check presence of copyright notice
- REQD-06: Check SDG icons count (1-3 required)

**Success Criteria:**
1. User can click "Check" and see compliance results within 30 seconds for typical documents
2. User can see issues grouped by category (Cover, Margins, Typography, Images, Required Elements)
3. User can see each issue marked as Error or Warning based on configured severity
4. User can see expected vs actual values for each failing check (e.g., "Expected: 300 DPI, Actual: 150 DPI")
5. User can see which page each issue occurs on

**Dependencies:** Phase 1 (extraction), Phase 2 (rule configuration)

**Research Notes:** This is the core value phase. Must handle font name normalization for typography checks, coordinate system conversions for margin checks, and color space detection for image checks.

---

## Phase 4: AI Verification

**Goal:** Users receive AI-augmented verification for visual checks that programmatic rules struggle with.

**Requirements:**
- AIVR-01: Detect UNEP logo and verify position/size via Claude vision
- AIVR-02: Assess image quality beyond DPI (blur, artifacts, visual issues)
- AIVR-03: Check layout balance and element alignment

**Success Criteria:**
1. User can see AI verification results alongside programmatic check results
2. User can see confidence scores for AI-verified issues (High/Medium/Low)
3. User can see AI reasoning explaining why an issue was flagged
4. User can see AI verification complete within reasonable time (under 60 seconds for typical documents)

**Dependencies:** Phase 1 (extraction), Phase 3 (checking infrastructure)

**Research Notes:** Must implement temperature=0 for deterministic results, structured outputs via Pydantic, and cost controls (selective verification, caching by content hash). AI should verify failed programmatic checks and handle visual-only assessments.

---

## Phase 5: Review Interface

**Goal:** Users can review all compliance issues in an interactive interface with filtering, notes, and issue selection.

**Requirements:**
- REVW-01: Display issues list with checkboxes for selection
- REVW-02: Issue cards show page, category, message, expected vs actual, severity
- REVW-03: User can add reviewer notes per issue
- REVW-04: User can filter issues by severity (All/Errors/Warnings)
- REVW-05: Summary bar shows total issues, selected count, error/warning counts

**Success Criteria:**
1. User can see all issues in a scrollable list with selection checkboxes
2. User can click an issue and see full details including page number and evidence
3. User can type notes on any issue and see notes persist
4. User can filter to show only Errors or only Warnings
5. User can see a summary bar showing "12 issues (8 selected) - 5 Errors, 7 Warnings"

**Dependencies:** Phase 3 (compliance checks), Phase 4 (AI verification)

**Research Notes:** UX is critical here. Must implement progressive disclosure to avoid issue overload, clear severity indicators, and responsive filtering. HTMX + Alpine.js for lightweight reactivity.

---

## Phase 6: Learning System & Output Generation

**Goal:** Users can mark exceptions to learn from, and generate professional review outputs (annotated PDF and Word document).

**Requirements:**
- LERN-01: User can mark issue to ignore in future reviews
- LERN-02: User must provide reason when ignoring a rule
- LERN-03: Ignored rules persisted to JSON file
- OUTP-01: Generate annotated PDF with sticky notes at issue locations
- OUTP-02: Generate Word document with review summary table
- OUTP-03: Include only user-selected issues in outputs

**Success Criteria:**
1. User can click "Ignore in Future" on an issue and provide a reason
2. User can see ignored issues no longer appear in subsequent reviews of the same document type
3. User can generate an annotated PDF with sticky notes at each selected issue location
4. User can generate a Word document containing a summary table of all selected issues
5. User can download both outputs with a single "Generate Reports" action

**Dependencies:** Phase 5 (review interface complete)

**Research Notes:** Learning system starts simple (exact rule_id matching). PyMuPDF handles PDF annotations natively. python-docx for Word generation. Must track learning scope for future v2 enhancement.

---

## Progress

| Phase | Name | Status | Requirements |
|-------|------|--------|--------------|
| 1 | PDF Foundation & Extraction | Pending | 7 |
| 2 | Rule Configuration Engine | Pending | 4 |
| 3 | Design Compliance Checks | Pending | 21 |
| 4 | AI Verification | Pending | 3 |
| 5 | Review Interface | Pending | 5 |
| 6 | Learning System & Output Generation | Pending | 6 |

**Total:** 46 requirement mappings (43 unique, some phases share extraction foundation)

---

## Dependency Graph

```
Phase 1: PDF Foundation & Extraction
    |
    v
Phase 2: Rule Configuration Engine
    |
    v
Phase 3: Design Compliance Checks <-- Phase 1 (extraction data)
    |
    v
Phase 4: AI Verification <-- Phase 1 (extraction), Phase 3 (check infrastructure)
    |
    v
Phase 5: Review Interface <-- Phase 3 + Phase 4 (all issues)
    |
    v
Phase 6: Learning & Output <-- Phase 5 (issue selection)
```

---
*Roadmap created: 2026-01-31*
*Depth: standard (5-8 phases)*
