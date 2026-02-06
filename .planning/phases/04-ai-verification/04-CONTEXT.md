# Phase 4: AI Verification - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

AI-powered analysis as the **primary judgment layer** for design compliance. Programmatic extraction (Phase 1) provides data; AI generates all findings using extracted data + page images. This replaces the "AI verifies programmatic checks" model with "AI is the analysis engine."

Requirements covered:
- AIVR-01: Detect UNEP logo and verify position/size via Claude vision
- AIVR-02: Assess image quality beyond DPI (blur, artifacts, visual issues)
- AIVR-03: Check layout balance and element alignment

</domain>

<decisions>
## Implementation Decisions

### AI Architecture
- AI is the **primary analysis layer**, not a verification layer
- Programmatic extraction feeds AI with data; AI generates findings
- No "verification of programmatic checks" — AI makes all judgments

### AI Inputs
- Page images at 72 DPI (screen resolution) + extracted data (text, fonts, images, margins)
- Simplified checklist derived from YAML rules at runtime (auto-generated)
- Checklist covers required elements only (logo, margins, fonts, ISBN, etc.) — no stylistic guidance

### Analysis Scope
- **Hybrid approach:** Per-page analysis for most checks, whole-document summary for cross-page consistency
- Per-page: AI sees individual page image + extracted data
- Whole-document: AI receives per-page summaries (not images) for consistency assessment
- 3-5 pages analyzed concurrently (balanced parallelism)

### Failure Handling
- Retry automatically 2-3 times on failure, then show error
- 30-second timeout per page
- If page times out: show "Page X timed out" in results (visible to user)
- No caching — always fresh analysis

### Re-analysis
- "Re-analyze" button available to trigger fresh AI analysis without re-uploading

### Confidence Display
- Show confidence only for Medium/Low confidence findings (High is assumed)
- Display: Icon + tooltip (warning icon, hover reveals confidence level)
- Low-confidence findings have muted/faded styling
- No filtering by confidence — all findings shown together

### Reasoning Format
- Include reasoning only for non-obvious findings (skip for clear violations like "No ISBN")
- Display: Expandable section (click to see reasoning)
- Verbosity: One sentence
- Location references: Descriptive only ("The logo in the header appears undersized")
- Certainty: Use confidence indicator, not language like "possible issue"
- Include fix suggestions in reasoning section

### Rule References
- Compare against specific rule values only when useful (measurable items)
- General guidance for subjective assessments

### Performance & Progress
- Show extraction data immediately, AI results appear when ready
- Progress indicator: Page counter ("Analyzing page 3 of 12...")
- Placement: Inside results panel, above findings

### Claude's Discretion
- Exact prompt structure for AI analysis
- How to handle pages with no findings (show "No issues" or omit)
- Retry logic implementation details

</decisions>

<specifics>
## Specific Ideas

- "AI is the primary judgment layer" — fundamental architecture shift from verification model
- Whole-doc analysis uses per-page summaries, not images (efficiency + consistency)
- Fix suggestions are part of the reasoning, not a separate field

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-ai-verification*
*Context gathered: 2026-01-31*
