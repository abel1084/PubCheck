# Phase 5: Review Interface - Research

**Researched:** 2026-01-31
**Domain:** React issue review UI with filtering, selection, and notes
**Confidence:** HIGH

## Summary

This phase builds an interactive review interface for compliance issues. The existing codebase already has strong foundations: `CheckIssue` type, `CategorySection` component, `IssueCard` component, and established patterns for `useReducer` state management with BEM CSS styling.

The key additions are: (1) selection state with checkboxes for each issue, (2) severity filtering (All/Errors/Warnings), (3) per-issue reviewer notes with persistence, and (4) a summary bar showing counts. The architecture should extend existing components rather than replace them, using the established `useReducer` pattern for complex review state.

**Primary recommendation:** Build a `useReviewState` hook using `useReducer` to manage selection, notes, and filter state in one place, then enhance existing `IssueCard` component with selection checkbox and notes textarea.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | ^18.3.1 | UI framework | Already in use |
| TypeScript | ~5.6.2 | Type safety | Already in use |
| @tanstack/react-table | ^8.21.2 | Table features if needed | Already installed, row selection APIs available |

### Supporting (No New Dependencies Needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| React useReducer | Built-in | Complex state management | Selection + notes + filter state |
| Native checkbox | Built-in | Issue selection | Simpler than table row selection for cards |
| Native textarea | Built-in | Reviewer notes | Standard form element |
| Native details/summary | Built-in | Collapsible sections | Already used in CategorySection |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native checkboxes | TanStack Table row selection | Overkill for card-based UI, table row selection better for tabular data |
| useReducer | useState + multiple hooks | useState leads to prop drilling and scattered state |
| Native form persistence | react-hook-form-persist | Unnecessary complexity for simple notes |
| localStorage for notes | In-memory state | Phase 6 handles export; notes don't need persistence between sessions |

**Installation:**
```bash
# No new dependencies required - all tools already available
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  hooks/
    useReviewState.ts         # NEW: Reducer for selection, notes, filter
  components/
    CheckResults/
      CheckResults.tsx        # MODIFY: Add ReviewProvider wrapper
      CategorySection.tsx     # MODIFY: Pass selection/notes handlers
      IssueCard.tsx           # MODIFY: Add checkbox + notes textarea
      ReviewSummaryBar.tsx    # NEW: Summary counts component
      ReviewFilterBar.tsx     # NEW: Severity filter buttons
      ReviewableIssue.tsx     # NEW (optional): Wrapper for IssueCard with review state
  types/
    review.ts                 # NEW: ReviewState, ReviewAction types
```

### Pattern 1: useReducer for Review State
**What:** Centralized state management for all review-related state
**When to use:** Multiple related state pieces (selection, notes, filter) that update together
**Example:**
```typescript
// Source: https://react.dev/reference/react/useReducer
interface ReviewState {
  selectedIssues: Set<string>;  // issue IDs
  notes: Record<string, string>; // issueId -> note text
  severityFilter: 'all' | 'error' | 'warning';
}

type ReviewAction =
  | { type: 'TOGGLE_SELECTION'; issueId: string }
  | { type: 'SELECT_ALL'; issueIds: string[] }
  | { type: 'DESELECT_ALL' }
  | { type: 'SET_NOTE'; issueId: string; note: string }
  | { type: 'SET_FILTER'; filter: 'all' | 'error' | 'warning' };

function reviewReducer(state: ReviewState, action: ReviewAction): ReviewState {
  switch (action.type) {
    case 'TOGGLE_SELECTION': {
      const newSelected = new Set(state.selectedIssues);
      if (newSelected.has(action.issueId)) {
        newSelected.delete(action.issueId);
      } else {
        newSelected.add(action.issueId);
      }
      return { ...state, selectedIssues: newSelected };
    }
    case 'SELECT_ALL':
      return { ...state, selectedIssues: new Set(action.issueIds) };
    case 'DESELECT_ALL':
      return { ...state, selectedIssues: new Set() };
    case 'SET_NOTE':
      return {
        ...state,
        notes: { ...state.notes, [action.issueId]: action.note }
      };
    case 'SET_FILTER':
      return { ...state, severityFilter: action.filter };
    default:
      return state;
  }
}
```

### Pattern 2: Unique Issue IDs
**What:** Generate stable, unique IDs for issues to enable selection tracking
**When to use:** Issues don't have natural IDs; need synthetic keys
**Example:**
```typescript
// Generate unique ID from issue properties
function getIssueId(issue: CheckIssue, categoryId: string, index: number): string {
  return `${categoryId}-${issue.rule_id}-${issue.pages.join(',')}-${index}`;
}

// Alternative: Use Map with object identity during the session
```

### Pattern 3: Filter-then-Count
**What:** Apply filter first, then compute counts from filtered list
**When to use:** Summary bar needs to show counts matching current filter
**Example:**
```typescript
// Apply filter
const filteredIssues = allIssues.filter(issue => {
  if (severityFilter === 'all') return true;
  return issue.severity === severityFilter;
});

// Count selected among filtered
const selectedCount = filteredIssues.filter(issue =>
  selectedIssues.has(getIssueId(issue))
).length;
```

### Pattern 4: Controlled Textarea for Notes
**What:** Store note value in reducer state, update on change
**When to use:** Per-issue notes that may be exported later
**Example:**
```typescript
<textarea
  className="issue-card__notes"
  placeholder="Add reviewer notes..."
  value={notes[issueId] || ''}
  onChange={(e) => dispatch({ type: 'SET_NOTE', issueId, note: e.target.value })}
  rows={2}
/>
```

### Anti-Patterns to Avoid
- **Separate useState for each concern:** Leads to inconsistent state and complex synchronization
- **Filtering in render without memoization:** Recalculates on every render; use useMemo
- **Checkbox onClick instead of onChange:** May miss keyboard interactions
- **Storing selection as array:** O(n) lookups; use Set for O(1) performance
- **Controlled inputs without debounce for notes:** Consider debounce if saving to backend

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Indeterminate checkbox | Manual DOM manipulation | `ref.current.indeterminate = true` | Native browser support |
| Complex state updates | Multiple useState calls | useReducer | Coordinated state, testable reducer |
| Issue uniqueness | Random IDs | Deterministic hash of properties | Stable across re-renders |
| Select-all logic | Loop through and setState | Single reducer action | Atomic update, no race conditions |
| Filter state persistence | localStorage | URL params or in-memory | Session-only is sufficient |

**Key insight:** The existing `useRuleSettings.ts` hook demonstrates the exact reducer pattern to follow. Copy its structure for the review state hook.

## Common Pitfalls

### Pitfall 1: State Lost on Re-check
**What goes wrong:** User selects issues and adds notes, runs re-check, all state disappears
**Why it happens:** New check results create new issue objects, breaking ID references
**How to avoid:** Either preserve review state across re-checks (by matching issues on content) or warn user before re-check that it will clear selections
**Warning signs:** User complains about losing work after re-check

### Pitfall 2: Filter Hides Selected Issues
**What goes wrong:** User selects an error, switches to "Warnings only" filter, error disappears but stays selected
**Why it happens:** Selection count shows issues not visible in current filter
**How to avoid:** Show "X selected (Y visible)" in summary bar, or clear selection when filter changes
**Warning signs:** Selection count doesn't match visible checkboxes

### Pitfall 3: Performance with Many Issues
**What goes wrong:** UI lags when there are 50+ issues
**Why it happens:** Re-rendering all issues on every state change
**How to avoid:**
  1. Use `React.memo` on IssueCard
  2. Pass stable handler references (useCallback)
  3. Use useMemo for filtered lists
**Warning signs:** Noticeable delay when clicking checkboxes

### Pitfall 4: Checkbox Click Doesn't Toggle
**What goes wrong:** Clicking checkbox does nothing
**Why it happens:** Using `checked` without `onChange`, or `onClick` on parent eating the event
**How to avoid:** Always pair `checked` with `onChange`, use `stopPropagation` if needed
**Warning signs:** Checkbox visually stuck, console shows no errors

### Pitfall 5: Notes Textarea Loses Focus
**What goes wrong:** After typing one character, textarea loses focus
**Why it happens:** Parent component re-renders and recreates textarea
**How to avoid:** Ensure stable keys, use React.memo, don't create new functions in render
**Warning signs:** Cursor jumps out of textarea mid-typing

## Code Examples

Verified patterns from official sources and existing codebase:

### Review Summary Bar Component
```typescript
// Source: Existing CheckResults pattern + requirements
interface ReviewSummaryBarProps {
  totalIssues: number;
  selectedCount: number;
  errorCount: number;
  warningCount: number;
  filter: 'all' | 'error' | 'warning';
  onFilterChange: (filter: 'all' | 'error' | 'warning') => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

export function ReviewSummaryBar({
  totalIssues,
  selectedCount,
  errorCount,
  warningCount,
  filter,
  onFilterChange,
  onSelectAll,
  onDeselectAll,
}: ReviewSummaryBarProps) {
  return (
    <div className="review-summary-bar">
      <div className="review-summary-bar__counts">
        <span className="review-summary-bar__total">
          {totalIssues} issues
        </span>
        <span className="review-summary-bar__selected">
          ({selectedCount} selected)
        </span>
        <span className="review-summary-bar__breakdown">
          - {errorCount} Errors, {warningCount} Warnings
        </span>
      </div>
      <div className="review-summary-bar__actions">
        <button onClick={onSelectAll}>Select All</button>
        <button onClick={onDeselectAll}>Deselect All</button>
      </div>
      <div className="review-summary-bar__filters">
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => onFilterChange('all')}
        >
          All
        </button>
        <button
          className={filter === 'error' ? 'active' : ''}
          onClick={() => onFilterChange('error')}
        >
          Errors
        </button>
        <button
          className={filter === 'warning' ? 'active' : ''}
          onClick={() => onFilterChange('warning')}
        >
          Warnings
        </button>
      </div>
    </div>
  );
}
```

### Enhanced IssueCard with Selection and Notes
```typescript
// Source: Existing IssueCard.tsx + requirements
interface ReviewableIssueCardProps {
  issue: CheckIssue;
  issueId: string;
  isSelected: boolean;
  note: string;
  onToggleSelect: () => void;
  onNoteChange: (note: string) => void;
}

export function ReviewableIssueCard({
  issue,
  issueId,
  isSelected,
  note,
  onToggleSelect,
  onNoteChange,
}: ReviewableIssueCardProps) {
  return (
    <div className="issue-card issue-card--reviewable">
      <div className="issue-card__selection">
        <input
          type="checkbox"
          id={`select-${issueId}`}
          checked={isSelected}
          onChange={onToggleSelect}
          className="issue-card__checkbox"
        />
      </div>
      {/* Existing issue content */}
      <details className="issue-card__content">
        <summary className="issue-card__summary">
          {/* severity icon, message, pages */}
        </summary>
        <div className="issue-card__details">
          {/* expected/actual, how to fix */}
          <div className="issue-card__notes-section">
            <label htmlFor={`notes-${issueId}`} className="issue-card__notes-label">
              Reviewer Notes:
            </label>
            <textarea
              id={`notes-${issueId}`}
              className="issue-card__notes"
              placeholder="Add notes..."
              value={note}
              onChange={(e) => onNoteChange(e.target.value)}
              rows={2}
            />
          </div>
        </div>
      </details>
    </div>
  );
}
```

### useReviewState Hook
```typescript
// Source: Pattern from useRuleSettings.ts + useReducer docs
import { useReducer, useCallback, useMemo } from 'react';
import type { CheckIssue, CategoryResult } from '../types/checks';

export interface ReviewState {
  selectedIssues: Set<string>;
  notes: Record<string, string>;
  severityFilter: 'all' | 'error' | 'warning';
}

// ... reducer as shown above ...

export function useReviewState(categories: CategoryResult[]) {
  const [state, dispatch] = useReducer(reviewReducer, {
    selectedIssues: new Set(),
    notes: {},
    severityFilter: 'all',
  });

  // Generate all issue IDs
  const allIssueIds = useMemo(() => {
    const ids: string[] = [];
    for (const category of categories) {
      category.issues.forEach((issue, index) => {
        ids.push(getIssueId(issue, category.category_id, index));
      });
    }
    return ids;
  }, [categories]);

  // Filter issues by severity
  const filteredCategories = useMemo(() => {
    if (state.severityFilter === 'all') return categories;
    return categories.map(cat => ({
      ...cat,
      issues: cat.issues.filter(i => i.severity === state.severityFilter),
    })).filter(cat => cat.issues.length > 0);
  }, [categories, state.severityFilter]);

  // Compute counts
  const counts = useMemo(() => {
    let total = 0, errors = 0, warnings = 0;
    for (const cat of categories) {
      for (const issue of cat.issues) {
        total++;
        if (issue.severity === 'error') errors++;
        else warnings++;
      }
    }
    return {
      total,
      errors,
      warnings,
      selected: state.selectedIssues.size,
    };
  }, [categories, state.selectedIssues.size]);

  const toggleSelection = useCallback((issueId: string) => {
    dispatch({ type: 'TOGGLE_SELECTION', issueId });
  }, []);

  const selectAll = useCallback(() => {
    dispatch({ type: 'SELECT_ALL', issueIds: allIssueIds });
  }, [allIssueIds]);

  const deselectAll = useCallback(() => {
    dispatch({ type: 'DESELECT_ALL' });
  }, []);

  const setNote = useCallback((issueId: string, note: string) => {
    dispatch({ type: 'SET_NOTE', issueId, note });
  }, []);

  const setFilter = useCallback((filter: 'all' | 'error' | 'warning') => {
    dispatch({ type: 'SET_FILTER', filter });
  }, []);

  return {
    selectedIssues: state.selectedIssues,
    notes: state.notes,
    severityFilter: state.severityFilter,
    filteredCategories,
    counts,
    toggleSelection,
    selectAll,
    deselectAll,
    setNote,
    setFilter,
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Redux for local state | useReducer + Context | React 16.8 (2019) | Simpler, no external deps |
| Class component state | Hooks | React 16.8 (2019) | Functional components standard |
| Prop drilling | Context for cross-cutting | React 16.3 (2018) | Cleaner component hierarchy |
| Array.includes for sets | Set data structure | ES6 (2015) | O(1) vs O(n) lookups |

**Deprecated/outdated:**
- HTMX + Alpine.js (mentioned in roadmap): Project uses React, ignore this
- Separate filter dropdowns: Toggle buttons provide clearer UX for 2-3 options

## Open Questions

Things that couldn't be fully resolved:

1. **Should selection persist across re-check?**
   - What we know: Re-check generates new issue objects
   - What's unclear: User expectation - start fresh or preserve selections?
   - Recommendation: Clear selections on re-check with a warning, or match issues by content hash

2. **Notes persistence strategy**
   - What we know: Phase 6 handles export/output generation
   - What's unclear: Whether notes should persist to localStorage between sessions
   - Recommendation: Keep in-memory only for now; Phase 6 can revisit if needed

3. **Select-all scope**
   - What we know: REVW-05 mentions selected count
   - What's unclear: Should "Select All" select filtered items only or all items?
   - Recommendation: Select visible (filtered) items only for intuitive UX

## Sources

### Primary (HIGH confidence)
- [React useReducer](https://react.dev/reference/react/useReducer) - reducer patterns, action structure
- [TanStack Table Row Selection](https://tanstack.com/table/v8/docs/guide/row-selection) - checkbox patterns, selection state
- Existing codebase: `useRuleSettings.ts`, `IssueCard.tsx`, `CategorySection.tsx`

### Secondary (MEDIUM confidence)
- [TanStack Table Column Filtering](https://tanstack.com/table/v8/docs/guide/column-filtering) - filter state patterns
- [React Preserving State](https://react.dev/learn/preserving-and-resetting-state) - state persistence concepts
- [Filter UX Patterns](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-filtering) - filter bar UX

### Tertiary (LOW confidence)
- WebSearch results for checkbox patterns - multiple sources agree on basic patterns
- Community discussions on TanStack Table - edge cases and gotchas

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, using established React patterns
- Architecture: HIGH - Following existing useReducer pattern from useRuleSettings.ts
- Pitfalls: MEDIUM - Based on common React patterns, may have project-specific nuances

**Research date:** 2026-01-31
**Valid until:** 60 days (stable React patterns, no fast-moving dependencies)
