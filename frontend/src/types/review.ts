/**
 * TypeScript types for the review interface.
 * Selection, notes, and filtering state for compliance issue review.
 */

/**
 * Severity filter options for filtering issues in the review interface.
 * - 'all': Show all issues regardless of severity
 * - 'error': Show only error-level issues
 * - 'warning': Show only warning-level issues
 */
export type SeverityFilter = 'all' | 'error' | 'warning';

/**
 * Category filter for filtering issues by category.
 * - 'all': Show issues from all categories
 * - string: Show only issues from the specified category_id
 */
export type CategoryFilter = 'all' | string;

/**
 * Review state managed by useReviewState reducer.
 * Tracks selection, notes, and filter preferences for the review session.
 */
export interface ReviewState {
  /**
   * Set of selected issue IDs (for report inclusion).
   * Issues are selected by their unique ID generated from getIssueId().
   */
  selectedIssues: Set<string>;

  /**
   * Map of issue ID to reviewer note text.
   * Notes are optional annotations that will appear in the PDF report.
   */
  notes: Record<string, string>;

  /**
   * Current severity filter for issue visibility.
   */
  severityFilter: SeverityFilter;

  /**
   * Current category filter for issue visibility.
   */
  categoryFilter: CategoryFilter;
}

/**
 * Computed counts from review state.
 * Derived values calculated from the current state and issue list.
 */
export interface ReviewCounts {
  /** Total number of issues across all categories */
  total: number;

  /** Number of currently selected issues */
  selected: number;

  /** Number of error-level issues */
  errors: number;

  /** Number of warning-level issues */
  warnings: number;

  /** Number of selected issues among currently visible (filtered) issues */
  visibleSelected: number;
}

/**
 * Actions for the review state reducer.
 * Each action type represents a specific state mutation.
 */
export type ReviewAction =
  /** Toggle selection state of a single issue */
  | { type: 'TOGGLE_SELECTION'; issueId: string }

  /** Select all issues within a specific category */
  | { type: 'SELECT_CATEGORY'; categoryId: string; issueIds: string[] }

  /** Deselect all issues within a specific category */
  | { type: 'DESELECT_CATEGORY'; categoryId: string; issueIds: string[] }

  /** Select all currently visible (filtered) issues */
  | { type: 'SELECT_ALL_VISIBLE'; issueIds: string[] }

  /** Deselect all issues */
  | { type: 'DESELECT_ALL' }

  /** Set or update the note for a specific issue */
  | { type: 'SET_NOTE'; issueId: string; note: string }

  /** Change the severity filter */
  | { type: 'SET_SEVERITY_FILTER'; filter: SeverityFilter }

  /** Change the category filter */
  | { type: 'SET_CATEGORY_FILTER'; filter: CategoryFilter }

  /** Initialize selection with all error issues (called once on mount) */
  | { type: 'INITIALIZE_SELECTION'; errorIds: string[] }

  /** Reset all review state to initial values */
  | { type: 'RESET' };
