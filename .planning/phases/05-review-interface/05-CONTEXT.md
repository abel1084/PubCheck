# Phase 5: Review Interface - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Interactive review of all compliance issues with selection checkboxes, reviewer notes, and filtering. Users can select which issues to include in the annotated PDF report. Creating the report itself is Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Selection behavior
- Selection means "include in annotated PDF report" (no Word doc output)
- Errors pre-selected by default, warnings start unselected
- Per-category bulk selection (select/deselect all within a category)
- Selection persists across filter changes
- No global select-all needed

### Notes interaction
- Notes text area visible inline below issue details (always shown)
- Notes appear in PDF annotations at issue's page and estimated coordinates
- ~200 character limit to keep annotations concise
- Auto-save on blur (no explicit save button)

### Filtering & sorting
- Filter by severity: toggle buttons (All / Errors / Warnings)
- Filter by category: dropdown menu
- Keep current sort order (grouped by category)
- Hide empty categories when filtering (don't show "0 issues")

### Summary bar
- Sticky bottom position (fixed at viewport bottom)
- Show: "12 issues (8 selected) — 5 Errors, 7 Warnings"
- Generate Report button lives in summary bar
- Button disabled when nothing selected, with hint text

### Claude's Discretion
- Exact styling and spacing of issue cards
- Animation/transition when filtering
- Keyboard navigation between issues
- Mobile responsiveness details

</decisions>

<specifics>
## Specific Ideas

- Notes should export to PDF annotations with the issue text — placed at the page and coordinates where the issue was found
- Errors-only pre-selection means reviewer focuses on confirming real problems, optionally adding warnings

</specifics>

<deferred>
## Deferred Ideas

- Word document output — removed from scope (PDF only)

</deferred>

---

*Phase: 05-review-interface*
*Context gathered: 2026-01-31*
