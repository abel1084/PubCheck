# PubCheck — UNEP PDF Design Compliance Checker

## What This Is

A local-first application that validates UNEP PDF publications against official design guidelines, provides an interactive review interface, and outputs annotated PDFs with comments at issue locations plus Word documents for formal records. Built for a small editorial/design team reviewing 5-20 publications monthly.

## Core Value

**Catch 95%+ of design compliance issues automatically**, producing professional, shareable review outputs that reduce back-and-forth with partners, editors, and external designers.

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### Upload & Detection
- [ ] Accept PDF files via drag-and-drop or file browser
- [ ] Auto-detect document type (Factsheet, Policy Brief, Issue Note, Working Paper, Publication)
- [ ] Show detection confidence with reasoning
- [ ] Allow manual override of detected type
- [ ] Detect and reject flattened/rasterized PDFs with accessibility explanation

#### Rule Configuration
- [ ] Three YAML template files covering all five document types
- [ ] Edit templates via Settings UI (tabbed/accordion by category)
- [ ] Per-rule enable/disable toggle
- [ ] Per-rule severity (Error/Warning)
- [ ] Per-rule notes field
- [ ] Import/export YAML templates

#### PDF Extraction
- [ ] Extract text with coordinates, font, size, weight, color
- [ ] Extract images with DPI, dimensions, color space
- [ ] Calculate margins from content bounding boxes
- [ ] Extract document metadata (title, author, ISBN, DOI, etc.)
- [ ] Parse tagged PDF structure (headings, tables, lists, alt text, links)

#### Rule Checking
- [ ] Cover rules: logo position/size, title/subtitle typography, partner logo placement
- [ ] Margin rules: top/bottom/inside/outside within specified ranges
- [ ] Typography rules: fonts, sizes, weights, alignment per element type
- [ ] Image rules: minimum DPI, color space, alt text presence
- [ ] Required elements: ISBN, DOI, job number, disclaimers, copyright, SDG icons
- [ ] Figure/table rules: width, stroke weight, number format, source citations
- [ ] Box/callout rules: padding, approved styles
- [ ] Structural rules: executive summary length, foreword requirements, TOC linking

#### AI Verification
- [ ] Verify programmatic check results
- [ ] Logo detection and position verification
- [ ] Image quality assessment beyond DPI (blur, artifacts)
- [ ] Layout balance and alignment checks
- [ ] Color accessibility (contrast ratios)
- [ ] Provide additional design/style/QA feedback
- [ ] Add confidence scores to issues

#### Review Interface
- [ ] PDF viewer with thumbnail navigation and zoom
- [ ] Highlight issue location when selected
- [ ] Issues list with selection checkboxes
- [ ] Issue cards showing: page, category, message, expected vs actual, severity
- [ ] Reviewer notes field per issue
- [ ] "Ignore in future" option with scope (All/Template/Document) and reason
- [ ] Filter by severity (All/Errors/Warnings)
- [ ] Sort by page/severity/category
- [ ] Search issues by keyword
- [ ] Summary bar: total issues, selected count, error/warning counts

#### Learnings System
- [ ] Persist ignored rules to JSON file
- [ ] Scope ignored rules: global, per-template, per-document
- [ ] Manage learnings via Settings UI (view, filter, edit, delete)

#### Output Generation
- [ ] Annotated PDF with sticky notes at issue locations
- [ ] Highlight boxes around problem areas
- [ ] Word document with review summary table
- [ ] Include only selected issues in outputs

### Out of Scope

- Multi-user collaboration features — single-user local app for now
- Cloud storage of documents — local filesystem only
- Real-time collaborative review — async output sharing is sufficient
- Custom rule creation via UI — edit YAML directly for advanced rules
- Mobile/tablet support — desktop browser only

## Context

**Current workflow pain points:**
- Manual review takes too long (multiple hours per document)
- Different reviewers catch different things (inconsistency)
- Extensive back-and-forth with partners, editors, external/internal designers
- No standardized way to communicate issues

**Design guidelines coverage:**
- `Rules/A4_Main_Publication_Guidelines.md` — Full publications (20+ pages)
- `Rules/Policy_Brief_Working_Paper_Guidelines.md` — Briefs and papers (4-30 pages)
- `Rules/Factsheet_Design_Rules.md` — Compact factsheets (1-4 pages)

**Document type characteristics:**
| Type | Pages | Key identifiers |
|------|-------|-----------------|
| Factsheet | 1-4 | Short, no ISBN, often A3 folded |
| Policy Brief | 4-8 | "Policy Brief" on cover, no chapters |
| Issue Note | 2-6 | "Issue Note" on cover, brief format |
| Working Paper | 10-30 | "Working Paper" on cover, may have TOC |
| Publication | 20+ | ISBN, DOI, TOC, Foreword, chapters |

## Constraints

- **Tech stack**: Python 3.10+ backend, vanilla HTML/CSS/JS frontend
- **PDF libraries**: PyMuPDF (extraction + annotation), pdfplumber (secondary parsing)
- **Word generation**: python-docx
- **AI integration**: Claude API via existing subscription
- **Deployment**: Local-first (localhost:5000), no cloud infrastructure
- **Data persistence**: YAML (templates), JSON (learnings), filesystem (uploads/outputs)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local-first architecture | Simple deployment, no infrastructure, data stays on machine | — Pending |
| Three YAML templates (not five) | Group similar document types to reduce maintenance | — Pending |
| AI verification as verification layer | Catch edge cases and provide design feedback beyond rules | — Pending |
| Dual output (PDF + Word) | Annotated PDF for detailed review, Word for formal records | — Pending |

---
*Last updated: 2026-01-31 after initialization*
