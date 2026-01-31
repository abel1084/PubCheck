# Requirements: PubCheck

**Defined:** 2026-01-31
**Core Value:** Catch 95%+ of design compliance issues automatically, producing professional review outputs

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Upload & Detection

- [ ] **UPLD-01**: User can upload PDF via drag-and-drop or file browser
- [ ] **UPLD-02**: System auto-detects document type from page count, keywords, ISBN presence
- [ ] **UPLD-03**: System rejects flattened/rasterized PDFs with accessibility explanation

### Rule Configuration

- [ ] **CONF-01**: Rules stored in YAML template files (3 templates covering 5 document types)
- [ ] **CONF-02**: Settings UI with tabbed interface to edit template rules
- [ ] **CONF-03**: User can enable/disable individual rules
- [ ] **CONF-04**: User can set severity per rule (Error/Warning)

### PDF Extraction

- [ ] **EXTR-01**: Extract text with x/y coordinates, font name, size, weight, color
- [ ] **EXTR-02**: Extract images with DPI, dimensions, color space
- [ ] **EXTR-03**: Calculate margins from content bounding boxes
- [ ] **EXTR-04**: Extract document metadata (title, author, ISBN, DOI, job number)

### Cover Checks

- [ ] **COVR-01**: Validate UNEP logo position (top-right) and size (min 20mm, target 27.5mm)
- [ ] **COVR-02**: Validate title typography (font, size range 28-34pt)
- [ ] **COVR-03**: Validate subtitle typography (font, size range 12-14pt)
- [ ] **COVR-04**: Validate partner logo placement (smaller than UNEP, correct position)

### Margin Checks

- [ ] **MRGN-01**: Validate top margin within range (20-25mm)
- [ ] **MRGN-02**: Validate bottom margin within range (20mm min)
- [ ] **MRGN-03**: Validate inside margin within range (20-30mm)
- [ ] **MRGN-04**: Validate outside margin within range (20-25mm)

### Typography Checks

- [ ] **TYPO-01**: Validate body text font matches template (Roboto Flex)
- [ ] **TYPO-02**: Validate body text size within range (9-12pt)
- [ ] **TYPO-03**: Validate heading hierarchy (H1-H4 fonts, sizes, weights)
- [ ] **TYPO-04**: Validate caption font and size (7pt Roboto)
- [ ] **TYPO-05**: Validate chart text font (8pt Roboto Condensed)

### Image Checks

- [ ] **IMAG-01**: Validate image DPI meets minimum (300 DPI)
- [ ] **IMAG-02**: Validate image color space (RGB or CMYK as specified)

### Required Elements

- [ ] **REQD-01**: Check presence of ISBN (for Publications)
- [ ] **REQD-02**: Check presence of DOI
- [ ] **REQD-03**: Check presence of job number
- [ ] **REQD-04**: Check presence of disclaimer text (exact match)
- [ ] **REQD-05**: Check presence of copyright notice
- [ ] **REQD-06**: Check SDG icons count (1-3 required)

### AI Verification

- [ ] **AIVR-01**: Detect UNEP logo and verify position/size via Claude vision
- [ ] **AIVR-02**: Assess image quality beyond DPI (blur, artifacts, visual issues)
- [ ] **AIVR-03**: Check layout balance and element alignment

### Review Interface

- [ ] **REVW-01**: Display issues list with checkboxes for selection
- [ ] **REVW-02**: Issue cards show page, category, message, expected vs actual, severity
- [ ] **REVW-03**: User can add reviewer notes per issue
- [ ] **REVW-04**: User can filter issues by severity (All/Errors/Warnings)
- [ ] **REVW-05**: Summary bar shows total issues, selected count, error/warning counts

### Learning System

- [ ] **LERN-01**: User can mark issue to ignore in future reviews
- [ ] **LERN-02**: User must provide reason when ignoring a rule
- [ ] **LERN-03**: Ignored rules persisted to JSON file

### Output Generation

- [ ] **OUTP-01**: Generate annotated PDF with sticky notes at issue locations
- [ ] **OUTP-02**: Generate Word document with review summary table
- [ ] **OUTP-03**: Include only user-selected issues in outputs

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Detection

- **UPLD-04**: Show detection confidence score with reasoning

### Advanced Checks

- **FIGU-01**: Validate figure/table maximum width (160mm)
- **FIGU-02**: Validate stroke weight (0.35pt)
- **FIGU-03**: Validate number format (space separator: 10 000)
- **FIGU-04**: Validate source citation presence
- **BOXS-01**: Validate box/callout padding (10mm top/bottom, 5mm left/right)
- **STRC-01**: Validate executive summary length (max 5 pages)
- **STRC-02**: Validate foreword has signature and photo
- **STRC-03**: Validate TOC is linked to chapters

### Enhanced AI

- **AIVR-04**: Provide open-ended design/style feedback

### Enhanced Review

- **REVW-06**: PDF viewer with thumbnail navigation and zoom
- **REVW-07**: Sort issues by page/severity/category
- **REVW-08**: Search/filter issues by keyword

### Enhanced Learning

- **LERN-04**: Scope selection for ignored rules (Global/Template/Document)
- **LERN-05**: Learnings management UI (view, edit, delete)

### Enhanced Output

- **OUTP-04**: Highlight boxes around problem areas in annotated PDF

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| PDF editing/remediation | Report issues only; let users fix in InDesign/Acrobat |
| Full PDF/UA accessibility | PAC and veraPDF do this well; defer to specialized tools |
| AI-generated fixes | Unpredictable output quality; AI for detection only |
| Real-time preview | Batch processing focus; preview is InDesign's job |
| Multi-user collaboration | Single-user local app; async output sharing sufficient |
| Cloud storage | Local filesystem only for v1 |
| Mobile support | Desktop browser only |
| OCR for scanned PDFs | Expect text-based PDFs; would add complexity |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| UPLD-01 | TBD | Pending |
| UPLD-02 | TBD | Pending |
| UPLD-03 | TBD | Pending |
| CONF-01 | TBD | Pending |
| CONF-02 | TBD | Pending |
| CONF-03 | TBD | Pending |
| CONF-04 | TBD | Pending |
| EXTR-01 | TBD | Pending |
| EXTR-02 | TBD | Pending |
| EXTR-03 | TBD | Pending |
| EXTR-04 | TBD | Pending |
| COVR-01 | TBD | Pending |
| COVR-02 | TBD | Pending |
| COVR-03 | TBD | Pending |
| COVR-04 | TBD | Pending |
| MRGN-01 | TBD | Pending |
| MRGN-02 | TBD | Pending |
| MRGN-03 | TBD | Pending |
| MRGN-04 | TBD | Pending |
| TYPO-01 | TBD | Pending |
| TYPO-02 | TBD | Pending |
| TYPO-03 | TBD | Pending |
| TYPO-04 | TBD | Pending |
| TYPO-05 | TBD | Pending |
| IMAG-01 | TBD | Pending |
| IMAG-02 | TBD | Pending |
| REQD-01 | TBD | Pending |
| REQD-02 | TBD | Pending |
| REQD-03 | TBD | Pending |
| REQD-04 | TBD | Pending |
| REQD-05 | TBD | Pending |
| REQD-06 | TBD | Pending |
| AIVR-01 | TBD | Pending |
| AIVR-02 | TBD | Pending |
| AIVR-03 | TBD | Pending |
| REVW-01 | TBD | Pending |
| REVW-02 | TBD | Pending |
| REVW-03 | TBD | Pending |
| REVW-04 | TBD | Pending |
| REVW-05 | TBD | Pending |
| LERN-01 | TBD | Pending |
| LERN-02 | TBD | Pending |
| LERN-03 | TBD | Pending |
| OUTP-01 | TBD | Pending |
| OUTP-02 | TBD | Pending |
| OUTP-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 0
- Unmapped: 43

---
*Requirements defined: 2026-01-31*
*Last updated: 2026-01-31 after initial definition*
