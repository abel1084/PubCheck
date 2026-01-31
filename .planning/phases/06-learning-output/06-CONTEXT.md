# Phase 6: Learning System & Output Generation - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

User can mark issues to ignore in future reviews (persisted by document type), and generate an annotated PDF with sticky notes at issue locations. Word document generation is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Ignore workflow
- Scope: Document type only (ignore rule for all Factsheets, not globally)
- Match precision: Rule ID only (ignores all issues from rule regardless of specific message)
- Button placement: On each issue card (small button/icon)
- Display of ignored issues: Hidden completely from results
- Undo: Toast notification with Undo button (~5 seconds)
- Reason field: Optional (can be left blank)
- Management: Settings section with "Ignored Rules" tab
- Settings display: Simple list (Rule ID, document type, reason if provided, date added, delete button)

### PDF annotations
- Sticky note colors: Severity-based (red for errors, yellow for warnings)
- Note content: Message only (not full details or rule ID)
- Positioning: At issue location when coordinates available, default to margin when not
- Overlapping issues: Stack vertically (offset each note down)
- Reviewer notes: Included in sticky note if present
- Summary: Page 1 summary annotation with issue count breakdown (X errors, Y warnings)
- AI distinction: Same treatment as programmatic issues (no visual difference)
- Filename: Append suffix (original-name_annotated.pdf)

### Download experience
- Button location: Already in summary bar (sticky bottom)
- Empty state: Button disabled when no issues selected
- Progress feedback: Modal dialog showing generation progress
- Download trigger: Click to download (show success message with download link)

### Claude's Discretion
- Exact toast styling and timing
- Modal progress indicator design
- Sticky note icon/styling
- Vertical offset amount for stacked notes
- Error handling for annotation failures

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Word document generation — removed from scope per user direction
- Global ignore scope (across all document types) — keep it simple for v1

</deferred>

---

*Phase: 06-learning-output*
*Context gathered: 2026-01-31*
