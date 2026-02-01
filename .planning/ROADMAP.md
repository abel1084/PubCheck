# Roadmap: PubCheck

**Created:** 2026-01-31
**Phases:** 7
**Requirements:** 52 mapped

## Overview

PubCheck delivers automated UNEP PDF design compliance checking through a layered pipeline: PDF parsing and extraction (foundation), rule configuration (engine), design compliance checks (core value), AI verification (edge cases), interactive review (user experience), and learning with output generation (completeness). Each phase builds on the previous, delivering incremental value while maintaining a clear dependency chain.

---

## Phase 1: PDF Foundation & Extraction

**Goal:** Users can upload PDFs and see extracted content (text, images, metadata) with reliable coordinate and font information.

**Plans:** 5 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffolding and PDF extraction service
- [x] 01-02-PLAN.md — Rasterized detection, document type detection, upload API
- [x] 01-03-PLAN.md — Frontend DropZone and SortableTable components
- [x] 01-04-PLAN.md — Frontend integration and data tabs
- [x] 01-05-PLAN.md — User verification checkpoint

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

**Plans:** 4 plans

Plans:
- [x] 02-01-PLAN.md — YAML templates and Pydantic models
- [x] 02-02-PLAN.md — Rules service and REST API endpoints
- [x] 02-03-PLAN.md — Frontend Settings UI with tabs and rule editing
- [x] 02-04-PLAN.md — User verification checkpoint

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

**Plans:** 5 plans

Plans:
- [x] 03-01-PLAN.md — Check models, tolerance utilities, executor foundation
- [x] 03-02-PLAN.md — Check handlers (position, range, font, regex, presence, color)
- [x] 03-03-PLAN.md — Check API endpoint and integration
- [x] 03-04-PLAN.md — Frontend Check Results UI
- [x] 03-05-PLAN.md — User verification checkpoint

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

**Plans:** 4 plans

Plans:
- [x] 04-01-PLAN.md — AI infrastructure (client, schemas, prompts, renderer)
- [x] 04-02-PLAN.md — Document analyzer and REST API endpoint
- [x] 04-03-PLAN.md — Frontend AI integration with progress and confidence display
- [x] 04-04-PLAN.md — User verification checkpoint

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

**Plans:** 4 plans

Plans:
- [x] 05-01-PLAN.md — Review types, useReviewState hook, ReviewSummaryBar component
- [x] 05-02-PLAN.md — IssueCard checkbox/notes, CategorySection review props
- [x] 05-03-PLAN.md — CheckResults integration, CSS styling
- [x] 05-04-PLAN.md — User verification checkpoint

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

**Goal:** Users can mark issues to ignore in future reviews (persisted by document type), and generate an annotated PDF with sticky notes at issue locations.

**Plans:** 6 plans

Plans:
- [x] 06-01-PLAN.md — Backend learning module (models, service, API)
- [x] 06-02-PLAN.md — Backend PDF annotation (annotator, API)
- [x] 06-03-PLAN.md — Frontend learning integration (hook, toast, ignore button)
- [x] 06-04-PLAN.md — Frontend PDF generation (progress modal, download)
- [x] 06-05-PLAN.md — Settings tab and final integration
- [x] 06-06-PLAN.md — User verification checkpoint

**Requirements:**
- LERN-01: User can mark issue to ignore in future reviews
- LERN-02: User must provide reason when ignoring a rule (OPTIONAL per user decision)
- LERN-03: Ignored rules persisted to JSON file
- OUTP-01: Generate annotated PDF with sticky notes at issue locations
- OUTP-02: Generate Word document with review summary table (DESCOPED)
- OUTP-03: Include only user-selected issues in outputs

**Success Criteria:**
1. User can click "Ignore" on an issue with optional reason
2. User can see ignored issues no longer appear in subsequent reviews of the same document type
3. User can generate an annotated PDF with sticky notes at each selected issue location
4. User can download PDF with a single "Generate Report" action

**Dependencies:** Phase 5 (review interface complete)

**Research Notes:** Learning system scoped to document type (not global). PyMuPDF handles PDF annotations natively. Word generation descoped per user direction. Sonner for toast notifications with undo.

---

## Phase 7: AI-First Architecture Overhaul

**Goal:** Replace programmatic compliance checking with AI-driven decisions. Extractor becomes measurement-only, AI receives original PDF + extracted JSON + rules markdown, makes ALL compliance decisions with collegial review style.

**Plans:** 8 plans

Plans:
- [x] 07-01-PLAN.md — Delete checks module, create rules context markdown files
- [x] 07-02-PLAN.md — Rewrite AI client for Claude with PDF and streaming support
- [x] 07-03-PLAN.md — Create useAIReview hook with SSE streaming
- [x] 07-04-PLAN.md — Create AI reviewer module with collegial prompts
- [x] 07-05-PLAN.md — Create ReviewResults component with sectioned cards
- [x] 07-06-PLAN.md — Create streaming SSE review endpoint
- [x] 07-07-PLAN.md — Update App.tsx, remove Settings, integrate review
- [ ] 07-08-PLAN.md — User verification checkpoint

**Requirements:**
- ARCH-01: Extractor outputs measurements only (ZERO compliance judgments)
- ARCH-02: Delete checker.py and all programmatic compliance logic
- ARCH-03: AI receives original PDF file (not rendered screenshots)
- ARCH-04: AI receives extracted JSON with measurements
- ARCH-05: AI receives rules context as markdown files
- ARCH-06: AI makes ALL compliance decisions with design intent awareness
- ARCH-07: Frontend UI updated for new review format

**Success Criteria:**
1. Extractor produces clean JSON with measurements, no violations flagged
2. AI identifies real issues only (not false positives like full-bleed images as margin violations)
3. Decorative elements (thin lines, bullets, icons) not flagged as images requiring DPI checks
4. Output reads like a helpful colleague's review, not an audit checklist
5. Specific measurements cited ("logo is 18mm, spec requires 20mm minimum")

**Dependencies:** Phase 6 (current codebase as starting point)

**Research Notes:**
- Current architecture: PDF -> PyMuPDF extracts -> checker.py flags violations -> AI reformats
- New architecture: PDF -> Extractor (measurements only) -> AI (PDF + JSON + rules) -> decisions
- Key insight: Programmatic checking lacks context (can't understand design intent, full-bleed images, decorative elements)
- Claude has native PDF support - pass original PDF, not rendered images
- Rules context converted from YAML to human-readable markdown per document type
- Streaming via SSE for real-time UI updates

---

## Phase 7.1: AI Review Fixes

**Goal:** Fix AI review issues identified during testing: logo measurements, DPI thresholds, UI improvements.

**Plans:** 4 plans

Plans:
- [x] 07.1-01-PLAN.md — Logo detection: mm dimensions + uncertainty hedging
- [x] 07.1-02-PLAN.md — Print/Digital/Both dropdown for DPI rules
- [x] 07.1-03-PLAN.md — Collapsible review section cards
- [x] 07.1-04-PLAN.md — Comment List tab with JSON issues for PDF annotation

**Requirements:**
- Fix logo measurements to use mm dimensions
- Add uncertainty hedging for implausible logo sizes
- Allow user to select output format (Print/Digital/Both) for DPI checks
- Make review sections collapsible for better UX
- Add Comment List tab with selectable issues for PDF annotation

**Success Criteria:**
1. Logo measurements shown in mm with uncertainty for implausible sizes
2. User can select Print/Digital/Both and see appropriate DPI thresholds applied
3. Review sections can be collapsed/expanded
4. User can select specific issues from Comment List tab for PDF annotation

**Dependencies:** Phase 7 (AI-First Architecture)

---

## Progress

| Phase | Name | Status | Requirements |
|-------|------|--------|--------------|
| 1 | PDF Foundation & Extraction | Complete | 7 |
| 2 | Rule Configuration Engine | Complete | 4 |
| 3 | Design Compliance Checks | Complete | 21 |
| 4 | AI Verification | Complete | 3 |
| 5 | Review Interface | Complete | 5 |
| 6 | Learning System & Output Generation | Complete | 5 |
| 7 | AI-First Architecture Overhaul | In Progress | 7 |
| 7.1 | AI Review Fixes | Complete | 5 |

**Total:** 57 requirement mappings (OUTP-02 descoped)

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
    |
    v
Phase 7: AI-First Architecture <-- Phase 6 (codebase refactor)
```

---
*Roadmap created: 2026-01-31*
*Depth: standard (5-8 phases)*
