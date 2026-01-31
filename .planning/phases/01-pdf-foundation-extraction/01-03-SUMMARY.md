---
phase: 01-pdf-foundation-extraction
plan: 03
subsystem: ui
tags: [react, react-dropzone, tanstack-table, typescript, frontend-components]

# Dependency graph
requires:
  - phase: 01-01
    provides: Frontend project scaffolding with Vite, React, TypeScript
provides:
  - DropZone component for PDF drag-and-drop upload
  - SortableTable component for data display with column sorting
affects: [01-04, 05-review-interface]

# Tech tracking
tech-stack:
  added: [react-dropzone, @tanstack/react-table]
  patterns: [Hook-based components, CSS BEM naming, Headless UI pattern]

key-files:
  created:
    - frontend/src/components/DropZone/DropZone.tsx
    - frontend/src/components/DropZone/DropZone.css
    - frontend/src/components/SortableTable/SortableTable.tsx
    - frontend/src/components/SortableTable/SortableTable.css
  modified:
    - .gitignore

key-decisions:
  - "Use ColumnDef<T, any> for generic table columns to avoid TypeScript variance issues"
  - "BEM CSS naming convention for component styles"
  - "Inline states (idle, active, accept, reject, processing, error) in DropZone"

patterns-established:
  - "Component structure: ComponentName/ComponentName.tsx + ComponentName.css + index.ts"
  - "react-dropzone useDropzone hook pattern for file uploads"
  - "TanStack Table with getSortedRowModel for sortable tables"

# Metrics
duration: 12min
completed: 2026-01-31
---

# Phase 1 Plan 3: UI Components Summary

**DropZone and SortableTable reusable React components with react-dropzone and TanStack Table**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-01-31T09:55:00Z
- **Completed:** 2026-01-31T10:07:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- DropZone component with drag-and-drop, visual states, PDF-only validation
- SortableTable component with clickable headers and sort indicators
- .gitignore for common excludes (node_modules, dist, __pycache__)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DropZone component** - `cc08817` (feat)
2. **Task 2: Create SortableTable component** - `9ffb679` (feat)

## Files Created/Modified
- `frontend/src/components/DropZone/DropZone.tsx` - Drag-and-drop file upload with react-dropzone
- `frontend/src/components/DropZone/DropZone.css` - Dashed border, hover/drag states, error styling
- `frontend/src/components/DropZone/index.ts` - Component export
- `frontend/src/components/SortableTable/SortableTable.tsx` - Generic sortable table with TanStack Table
- `frontend/src/components/SortableTable/SortableTable.css` - Header styling, row hover, sort indicators
- `frontend/src/components/SortableTable/index.ts` - Component export
- `.gitignore` - Exclude node_modules, dist, __pycache__, IDE files

## Decisions Made
- Used `ColumnDef<T, any>` instead of `ColumnDef<T, unknown>` - TanStack Table's type variance causes issues with strict TypeScript when columns have typed accessors
- BEM CSS naming (drop-zone__content, sortable-table__header) for clear component scoping
- Visual feedback via CSS classes rather than inline styles for maintainability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript optional chaining for rejection errors**
- **Found during:** Task 1 (DropZone implementation)
- **Issue:** TypeScript strict mode flagged potential undefined access on `rejectedFiles[0].errors[0]`
- **Fix:** Added optional chaining `rejection?.errors?.[0]` and fallback message
- **Files modified:** frontend/src/components/DropZone/DropZone.tsx
- **Verification:** `npm run build` passes
- **Committed in:** cc08817 (part of Task 1 commit)

**2. [Rule 3 - Blocking] Fixed DataTabs type errors blocking build**
- **Found during:** Task 2 verification (build step)
- **Issue:** Parallel task (01-04) created DataTabs that imports SortableTable but had ColumnDef type mismatches
- **Fix:** Updated DataTabs files to use `ColumnDef<T, any>[]` type annotation
- **Files modified:** frontend/src/components/DataTabs/TextTab.tsx, ImagesTab.tsx, MarginsTab.tsx
- **Verification:** `npm run build` passes with all components
- **Impact:** Fix not committed as part of 01-03 (files belong to 01-04 scope)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Bug fix essential for TypeScript correctness. Blocking fix enabled verification but files belong to parallel task scope.

## Quick Rules Applied

No Quick Rules applied during this plan.

## Issues Encountered

- Parallel task (01-04) created DataTabs component that depends on SortableTable but was not yet type-compatible. Fixed type annotations to unblock build verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- DropZone ready for integration with upload API hook
- SortableTable ready for use in data tabs (Text, Images, Margins)
- Components follow established patterns for consistency

---
*Phase: 01-pdf-foundation-extraction*
*Plan: 03*
*Completed: 2026-01-31*
