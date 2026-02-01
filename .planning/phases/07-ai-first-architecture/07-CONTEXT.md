# Phase 7: AI-First Architecture Overhaul - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace programmatic compliance checking with AI-driven decisions. The extractor becomes measurement-only (no violation flagging), checker.py gets deleted, and AI receives original PDF + extracted JSON + rules markdown to make ALL compliance decisions. Output reads like a helpful colleague's review, not an audit checklist.

</domain>

<decisions>
## Implementation Decisions

### AI Input Format
- Original PDF file passed directly (Claude's native PDF support, not rendered images)
- Extracted measurements as structured JSON (current ExtractionResult format)
- Entire document processed in one AI call (full context for cross-page consistency)
- No token limits — allow all document sizes
- User rule overrides merged into rules context (AI sees final state, not separate override layer)
- No per-user ignored rules feature — universal rules, single config per document type
- Document type passed to AI: best guess + confidence score, AI validates
- Common pitfalls/false positives baked into system prompt (not per-request context)

### Output & Tone
- Collegial review style ("The logo looks a bit small at 18mm — spec asks for 20mm minimum")
- Priority-based organization:
  - Overview
  - Needs Attention (critical)
  - Looking Good
  - Suggestions (minor)
- Within "Needs Attention," AI naturally groups related issues (no rigid category enforcement)
- No formal confidence scores — honest hedging in prose when uncertain ("This might be intentional, but...")
- Measurements cited when relevant (size/margin issues), not for visual assessments

### Rules Context Design
- Type-specific rules files maintained:
  - `config/rules_context/working_paper.md`
  - `config/rules_context/publication.md`
  - `config/rules_context/brief.md`
  - `config/rules_context/factsheet.md`
- Detector picks which file to load based on document type
- Rules expressed as mix: prose explanation + key measurements ("The UNEP logo should appear in the top-right corner. Minimum width: 20mm, target: 27.5mm")
- Include rationale for non-obvious rules only
- Common mistakes in system prompt only (not per-rule examples)

### Frontend Adaptation
- Hybrid display: AI review as prose with expandable individual items
- Sectioned cards: Overview, Needs Attention, Looking Good, Suggestions
- PDF annotation output retained — wire to AI's issues array, remove colored sticky notes
- Settings UI removed entirely (no user rule configuration)
- Document type dropdown kept (show detected type + confidence, allow override)
- Extracted data tabs (Text, Images, Margins) collapsed/hidden by default
- "Check" button renamed to "Review"
- Streaming text display during AI processing
- Page thumbnails sidebar removed
- "Ignore this rule" feature removed

### Claude's Discretion
- Exact streaming implementation approach
- How to structure issues array for PDF annotation extraction
- Graceful handling of any edge cases in document processing

</decisions>

<specifics>
## Specific Ideas

- "Output reads like a helpful colleague's review, not an audit checklist"
- Real issues only — no false positives like full-bleed images as margin violations
- Decorative elements (thin lines, bullets, icons) not flagged as images requiring DPI checks
- Specific measurements cited when relevant ("logo is 18mm, spec requires 20mm minimum")

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-ai-first-architecture*
*Context gathered: 2026-02-01*
