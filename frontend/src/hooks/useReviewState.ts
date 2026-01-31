import { useReducer, useCallback, useEffect, useMemo } from 'react';
import type { CheckIssue, CategoryResult } from '../types/checks';
import type {
  ReviewState,
  ReviewAction,
  SeverityFilter,
  CategoryFilter,
  ReviewCounts,
} from '../types/review';

/**
 * Generate a stable unique ID for an issue.
 * Uses category, rule_id, pages, and index to create a deterministic key.
 */
export function getIssueId(issue: CheckIssue, categoryId: string, index: number): string {
  return `${categoryId}-${issue.rule_id}-${issue.pages.join(',')}-${index}`;
}

/**
 * Initial state for the review reducer.
 */
const initialState: ReviewState = {
  selectedIssues: new Set(),
  notes: {},
  severityFilter: 'all',
  categoryFilter: 'all',
};

/**
 * Reducer for review state management.
 * Handles selection, notes, and filter updates.
 */
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

    case 'SELECT_CATEGORY': {
      const newSelected = new Set(state.selectedIssues);
      for (const issueId of action.issueIds) {
        newSelected.add(issueId);
      }
      return { ...state, selectedIssues: newSelected };
    }

    case 'DESELECT_CATEGORY': {
      const newSelected = new Set(state.selectedIssues);
      for (const issueId of action.issueIds) {
        newSelected.delete(issueId);
      }
      return { ...state, selectedIssues: newSelected };
    }

    case 'SELECT_ALL_VISIBLE': {
      const newSelected = new Set(state.selectedIssues);
      for (const issueId of action.issueIds) {
        newSelected.add(issueId);
      }
      return { ...state, selectedIssues: newSelected };
    }

    case 'DESELECT_ALL':
      return { ...state, selectedIssues: new Set() };

    case 'SET_NOTE':
      return {
        ...state,
        notes: { ...state.notes, [action.issueId]: action.note },
      };

    case 'SET_SEVERITY_FILTER':
      return { ...state, severityFilter: action.filter };

    case 'SET_CATEGORY_FILTER':
      return { ...state, categoryFilter: action.filter };

    case 'INITIALIZE_SELECTION':
      return { ...state, selectedIssues: new Set(action.errorIds) };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

/**
 * Hook result interface for useReviewState.
 */
export interface UseReviewStateResult {
  /** Set of selected issue IDs */
  selectedIssues: Set<string>;
  /** Map of issue ID to note text */
  notes: Record<string, string>;
  /** Current severity filter */
  severityFilter: SeverityFilter;
  /** Current category filter */
  categoryFilter: CategoryFilter;
  /** Categories after applying current filters */
  filteredCategories: CategoryResult[];
  /** Computed count values */
  counts: ReviewCounts;
  /** Toggle selection of a single issue */
  toggleSelection: (issueId: string) => void;
  /** Select all issues in a category */
  selectCategory: (categoryId: string, issueIds: string[]) => void;
  /** Deselect all issues in a category */
  deselectCategory: (categoryId: string, issueIds: string[]) => void;
  /** Select all currently visible (filtered) issues */
  selectAllVisible: () => void;
  /** Deselect all issues */
  deselectAll: () => void;
  /** Set note for an issue */
  setNote: (issueId: string, note: string) => void;
  /** Set severity filter */
  setSeverityFilter: (filter: SeverityFilter) => void;
  /** Set category filter */
  setCategoryFilter: (filter: CategoryFilter) => void;
  /** Reset all review state */
  reset: () => void;
}

/**
 * Hook for managing review state with reducer pattern.
 * Provides selection, notes, and filtering for compliance issue review.
 *
 * @param categories - Array of CategoryResult from check results
 * @returns Review state and action callbacks
 */
export function useReviewState(categories: CategoryResult[]): UseReviewStateResult {
  const [state, dispatch] = useReducer(reviewReducer, initialState);

  // Initialize selection with all error issues when categories change
  useEffect(() => {
    const errorIds: string[] = [];
    for (const category of categories) {
      category.issues.forEach((issue, index) => {
        if (issue.severity === 'error') {
          errorIds.push(getIssueId(issue, category.category_id, index));
        }
      });
    }
    if (errorIds.length > 0) {
      dispatch({ type: 'INITIALIZE_SELECTION', errorIds });
    }
  }, [categories]);

  // Filter categories by severity and category filters
  const filteredCategories = useMemo(() => {
    let result = categories;

    // Apply category filter
    if (state.categoryFilter !== 'all') {
      result = result.filter((cat) => cat.category_id === state.categoryFilter);
    }

    // Apply severity filter
    if (state.severityFilter !== 'all') {
      result = result
        .map((cat) => ({
          ...cat,
          issues: cat.issues.filter((issue) => issue.severity === state.severityFilter),
          error_count:
            state.severityFilter === 'error'
              ? cat.issues.filter((i) => i.severity === 'error').length
              : 0,
          warning_count:
            state.severityFilter === 'warning'
              ? cat.issues.filter((i) => i.severity === 'warning').length
              : 0,
        }))
        .filter((cat) => cat.issues.length > 0);
    }

    return result;
  }, [categories, state.severityFilter, state.categoryFilter]);

  // Get all visible issue IDs (for select all visible)
  const visibleIssueIds = useMemo(() => {
    const ids: string[] = [];
    for (const category of filteredCategories) {
      category.issues.forEach((issue, index) => {
        ids.push(getIssueId(issue, category.category_id, index));
      });
    }
    return ids;
  }, [filteredCategories]);

  // Compute counts
  const counts = useMemo<ReviewCounts>(() => {
    let total = 0;
    let errors = 0;
    let warnings = 0;

    for (const category of categories) {
      for (const issue of category.issues) {
        total++;
        if (issue.severity === 'error') {
          errors++;
        } else {
          warnings++;
        }
      }
    }

    // Count selected among visible issues
    let visibleSelected = 0;
    for (const issueId of visibleIssueIds) {
      if (state.selectedIssues.has(issueId)) {
        visibleSelected++;
      }
    }

    return {
      total,
      selected: state.selectedIssues.size,
      errors,
      warnings,
      visibleSelected,
    };
  }, [categories, state.selectedIssues, visibleIssueIds]);

  // Action callbacks with useCallback for stable references
  const toggleSelection = useCallback((issueId: string) => {
    dispatch({ type: 'TOGGLE_SELECTION', issueId });
  }, []);

  const selectCategory = useCallback((categoryId: string, issueIds: string[]) => {
    dispatch({ type: 'SELECT_CATEGORY', categoryId, issueIds });
  }, []);

  const deselectCategory = useCallback((categoryId: string, issueIds: string[]) => {
    dispatch({ type: 'DESELECT_CATEGORY', categoryId, issueIds });
  }, []);

  const selectAllVisible = useCallback(() => {
    dispatch({ type: 'SELECT_ALL_VISIBLE', issueIds: visibleIssueIds });
  }, [visibleIssueIds]);

  const deselectAll = useCallback(() => {
    dispatch({ type: 'DESELECT_ALL' });
  }, []);

  const setNote = useCallback((issueId: string, note: string) => {
    dispatch({ type: 'SET_NOTE', issueId, note });
  }, []);

  const setSeverityFilter = useCallback((filter: SeverityFilter) => {
    dispatch({ type: 'SET_SEVERITY_FILTER', filter });
  }, []);

  const setCategoryFilter = useCallback((filter: CategoryFilter) => {
    dispatch({ type: 'SET_CATEGORY_FILTER', filter });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    selectedIssues: state.selectedIssues,
    notes: state.notes,
    severityFilter: state.severityFilter,
    categoryFilter: state.categoryFilter,
    filteredCategories,
    counts,
    toggleSelection,
    selectCategory,
    deselectCategory,
    selectAllVisible,
    deselectAll,
    setNote,
    setSeverityFilter,
    setCategoryFilter,
    reset,
  };
}
