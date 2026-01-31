# Phase 3: Design Compliance Checks - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Execute 21 configured rules against extracted PDF data and surface categorized compliance findings with severity levels. Users click "Check" and see issues grouped by category with expected vs actual values. This is the core value phase.

</domain>

<decisions>
## Implementation Decisions

### Results Presentation
- Group issues by category: Cover → Margins → Typography → Images → Required Elements (fixed order)
- Within each category, sort by severity first (Errors before Warnings)
- Show all categories including empty ones (with checkmark or "No issues")
- Pass/Fail badge for overall status: Pass (no errors), Fail (has errors), Warning-only
- Issues collapsed by default — summary line shows severity icon + message
- Click to expand for full details
- Red for errors, yellow/amber for warnings
- Category headers show count badge: "Typography (4)" or "Typography ✓"
- Categories are independently collapsible
- Categories with errors expanded by default, others collapsed
- Expand All / Collapse All toggle available
- Zero issues: Large green success banner with "All checks passed"
- Results appear in new "Check Results" tab alongside existing data tabs
- Issues are standalone (no navigation to source data tabs)
- Subtle "Re-check" button to run checks again

### Check Execution
- Spinner with category-specific status text: "Checking Cover..." → "Checking Margins..."
- "Check" button lives in header/toolbar area
- Checks require explicit click (no auto-run after upload)
- If a check fails unexpectedly (code error), show partial results with failed checks noted separately
- Disabled rules skipped silently (not shown in results)
- No cancel button needed (checks are fast)
- Check button disabled with tooltip until PDF uploaded

### Issue Details
- No rule ID shown to users (internal reference only)
- Two value formats:
  - UI (compact): "150 DPI (min 300)"
  - PDF comments (full context): "Image DPI below minimum. Found: 150 DPI, Required: 300 DPI"
- "How to fix" hints included for obvious fixes only
- Multi-page issues grouped in UI: "Top margin too small (10 pages)" with expand to see/select individual pages
- PDF output: Each occurrence commented separately

### Tolerance Handling
- Margins: Check minimum only — flag when content too close to edge, not when margins are larger
- Font names: Normalize subset prefixes ("ABCDEF+Roboto" matches "Roboto")
- Font sizes: ±0.5pt tolerance
- DPI: 2.5% tolerance below minimum (293 DPI passes for 300 minimum)
- Text matching: Case-insensitive
- Whitespace: Normalize (multiple spaces/newlines treated as single space)
- Color matching: Allow near-matches (small delta per channel)
- Logo size: ±1mm tolerance around minimum

### Claude's Discretion
- Exact color matching delta (±5 per channel or similar)
- Error message wording for edge cases
- Which issues get "how to fix" hints
- Loading state animations

</decisions>

<specifics>
## Specific Ideas

- Compact format in UI keeps the review interface scannable
- Full context in PDF comments ensures external reviewers understand without app access
- Margin checks focus on "too close to edge" not "too much margin" — practical for real-world tolerance

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-design-compliance-checks*
*Context gathered: 2026-01-31*
