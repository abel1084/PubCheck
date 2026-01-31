# Phase 2: Rule Configuration Engine - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can configure UNEP design rules via YAML templates and a settings UI. Users can enable/disable rules, set severity (Error/Warning), and edit expected values. 5 document types with independent settings derived from 3 base templates. Compliance checking uses these rules in Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Rule Organization
- Group rules by category (Cover, Margins, Typography, Images, Required Elements)
- Categories are collapsible — user can collapse to focus on what they're editing
- No search/filter — categories + collapsing is sufficient navigation
- Category headers show enabled count: "Typography (8/12 enabled)"

### Edit Experience
- Checkbox per rule for enable/disable (not toggle switch)
- Toggle button to switch severity between Error/Warning
- Explicit save button required (not auto-save)
- "Reset to defaults" button restores original YAML values
- No bulk actions — users toggle rules individually
- Warn before leaving with unsaved changes
- Save button shows "Saved ✓" briefly on success, then returns to "Save"
- Disabled rules show severity control grayed out but visible

### Template Mapping
- 5 document type tabs: Factsheet, Policy Brief, Issue Note, Working Paper, Report/Publication
- Each document type has independent settings — editing one does not affect others
- No visual indication of which types share base templates — user sees them as independent

### Rule Display
- Each rule row shows: name + expected value (e.g., "Body text size: 9-12pt")
- Values are editable — user can customize thresholds
- Click rule to expand row and show editable fields
- Type-appropriate validation with error messages when editing values

### Claude's Discretion
- Exact layout and spacing of rule rows
- Expand/collapse animation
- Validation error message wording
- How YAML templates are structured internally

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-rule-configuration-engine*
*Context gathered: 2026-01-31*
