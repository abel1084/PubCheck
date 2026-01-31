---
phase: 05
plan: 01
subsystem: review-interface
tags:
  - typescript
  - react-hooks
  - state-management

dependency-graph:
  requires:
    - 03-04 (CheckResult types, CategorySection, IssueCard)
    - 02-03 (useReducer pattern from useRuleSettings)
  provides:
    - Review state types (ReviewState, ReviewAction, ReviewCounts)
    - useReviewState hook with selection/notes/filter management
    - ReviewSummaryBar component
  affects:
    - 05-02 (component enhancements will consume these types/hooks)
    - 05-03 (CSS styling for ReviewSummaryBar)
    - 05-04 (integration will wire up all components)

tech-stack:
  added: []
  patterns:
    - useReducer for complex state (selection, notes, filters)
    - Set<string> for O(1) selection lookups
    - useMemo for derived state (filtered categories, counts)
    - useCallback for stable action callbacks

key-files:
  created:
    - frontend/src/types/review.ts
    - frontend/src/hooks/useReviewState.ts
    - frontend/src/components/CheckResults/ReviewSummaryBar.tsx
  modified: []

decisions:
  - decision: "Errors pre-selected by default"
    rationale: "Per CONTEXT.md - focus on confirming real problems first"
  - decision: "Selection persists across filter changes"
    rationale: "Per CONTEXT.md - user shouldn't lose selections when filtering"
  - decision: "visibleSelected count in ReviewCounts"
    rationale: "Shows 'X selected (Y visible)' when filter hides selected items"
  - decision: "getIssueId uses category-rule-pages-index format"
    rationale: "Stable unique IDs without requiring backend-assigned IDs"

metrics:
  duration: 4 min
  completed: 2026-01-31
---

# Phase 5 Plan 01: Review State Foundation Summary

Review state management types, hook, and summary bar component for the compliance review interface.

## What Was Built

Created the foundation for review interface state management:

1. **Review Types** (`frontend/src/types/review.ts`)
   - `SeverityFilter` and `CategoryFilter` types for filtering
   - `ReviewState` interface with selectedIssues (Set), notes (Record), and filter state
   - `ReviewCounts` interface for derived count values including visibleSelected
   - `ReviewAction` union type covering all reducer actions

2. **useReviewState Hook** (`frontend/src/hooks/useReviewState.ts`)
   - Follows the established useReducer pattern from useRuleSettings.ts
   - `getIssueId()` function for stable unique issue identification
   - Auto-initializes with all error issues selected (per CONTEXT.md)
   - Memoized `filteredCategories` and `counts` for performance
   - Stable callbacks via useCallback for all actions

3. **ReviewSummaryBar Component** (`frontend/src/components/CheckResults/ReviewSummaryBar.tsx`)
   - Displays total/selected/error/warning counts
   - Shows "X selected (Y visible)" when filter hides selected items
   - Severity filter toggle buttons (All/Errors/Warnings)
   - Select All Visible / Deselect All action buttons
   - Generate Report button with disabled state and tooltip
   - BEM CSS class naming ready for styling in plan 03

## Key Implementation Details

### Issue ID Generation
```typescript
export function getIssueId(issue: CheckIssue, categoryId: string, index: number): string {
  return `${categoryId}-${issue.rule_id}-${issue.pages.join(',')}-${index}`;
}
```

### Reducer Actions
- `TOGGLE_SELECTION` - Single issue toggle
- `SELECT_CATEGORY` / `DESELECT_CATEGORY` - Bulk per-category
- `SELECT_ALL_VISIBLE` - All filtered issues
- `DESELECT_ALL` - Clear selection
- `SET_NOTE` - Update issue note
- `SET_SEVERITY_FILTER` / `SET_CATEGORY_FILTER` - Update filters
- `INITIALIZE_SELECTION` - Pre-select errors on mount
- `RESET` - Clear all state

### Derived State
- `filteredCategories`: Categories after applying severity and category filters, empty categories removed
- `counts`: Total, selected, errors, warnings, visibleSelected

## Commits

| Hash | Description |
|------|-------------|
| 86c08f8 | feat(05-01): create review interface TypeScript types |
| 10008b9 | feat(05-01): create useReviewState hook with reducer pattern |
| f1dd882 | feat(05-01): create ReviewSummaryBar component |

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- [x] All three files exist and export their types/functions/components
- [x] TypeScript compiles: `cd frontend && npx tsc --noEmit`
- [x] useReviewState hook matches the pattern established in useRuleSettings.ts
- [x] getIssueId generates deterministic unique IDs
- [x] ReviewSummaryBar accepts all required props for integration

## Next Phase Readiness

Ready for plan 05-02 which will enhance CategorySection and IssueCard to consume the review state hook. The types and hook are fully compatible with the existing component interfaces that already have optional review mode props.
