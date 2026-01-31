# Phase 1: PDF Foundation & Extraction - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Enable users to upload PDFs and view extracted content — text with font/coordinate data, images with quality metrics, calculated margins, and document metadata. Users can see detected document type with manual override. Creating compliance checks or running rules are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Upload Experience
- Prominent drop zone with large dashed border area, icon, and "Drop PDF here" text — upload is the clear first action
- Border highlight on drag-over: dashed border becomes solid/colored with subtle background change
- Rejection (flattened/rasterized PDFs) shown as inline message in drop zone — red message explaining why, with link to accessibility info
- Secondary "or click to browse" text link below main message for file browser fallback

### Content Display
- Tabbed panels for organization: Text, Images, Margins, Metadata — one category at a time
- Text tab: Summary table of all fonts found with counts/locations — text blocks listed separately
- Images tab: List view with small preview, DPI, dimensions, color space as columns — sortable by DPI to spot low-res images instantly
- Margins tab: Table per page showing Page | Top | Bottom | Inside | Outside values
- All pages shown by default with option to filter to single page
- Metadata tab: Key fields only (Title, Author, ISBN, DOI, Job number, Creation date, Producer) with "Show all metadata" expandable link for debugging
- Tables are sortable by column headers (no filtering)
- Empty tabs shown as disabled with count: "Images (0)" — grayed out

### Document Type Detection
- Shown in sidebar field alongside filename, page count, and other document info
- Override via dropdown — click to open dropdown with all 5 document types
- Confidence level always shown: "Factsheet (High confidence)" or similar indicator
- 5 UNEP document types: Factsheet, Policy Brief, Working Paper, Technical Report, Publication

### Feedback & Errors
- Progress shown as spinner with status text updates: "Extracting images..."
- Partial extraction failures: Show what was extracted with warning about failed pages
- Corrupt/unreadable PDFs: Inline error shown in drop zone, zone remains usable for another drop
- New document upload via "New Document" button in header (returns to upload view)

### Claude's Discretion
- Exact drop zone dimensions and styling details
- Spinner implementation and animation
- Table column widths and responsive behavior
- Font summary grouping logic
- Error message copy and formatting

</decisions>

<specifics>
## Specific Ideas

- Data-first approach: tables over visuals, sortable to surface compliance issues quickly
- Images sortable by DPI — reviewer's mental model is "find the problems fast"
- Producer metadata included because it helps detect source application (InDesign vs Word, etc.)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-pdf-foundation-extraction*
*Context gathered: 2026-01-31*
