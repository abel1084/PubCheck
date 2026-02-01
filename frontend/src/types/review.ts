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

// ============================================================================
// AI-First Architecture Types (Phase 7)
// ============================================================================

/**
 * Structured issue from AI review JSON output.
 * Used for Comment List selection and PDF annotation.
 */
export interface ReviewIssue {
  /** Unique ID: "issue-1", "issue-2", etc. */
  id: string;
  /** Category: needs_attention for required fixes, suggestion for optional */
  category: 'needs_attention' | 'suggestion';
  /** Brief issue title */
  title: string;
  /** Full description with measurements */
  description: string;
  /** Page numbers where issue appears */
  pages: number[];
}

/**
 * Parsed review sections from AI response.
 * AI produces prose review organized by these sections.
 */
export interface AIReviewSections {
  overview: string;
  needsAttention: string;
  lookingGood: string;
  suggestions: string;
}

/**
 * State of AI review process.
 * Tracks streaming progress and accumulated content.
 */
export interface AIReviewState {
  /** Accumulated raw markdown content */
  content: string;
  /** Parsed sections (updated as content streams) */
  sections: AIReviewSections;
  /** Structured issues parsed from JSON block (populated after streaming completes) */
  issues: ReviewIssue[];
  /** Currently streaming */
  isStreaming: boolean;
  /** Stream completed successfully */
  isComplete: boolean;
  /** Error message if failed */
  error: string | null;
}

/** Initial empty AI review state */
export const INITIAL_AI_REVIEW_STATE: AIReviewState = {
  content: '',
  sections: {
    overview: '',
    needsAttention: '',
    lookingGood: '',
    suggestions: '',
  },
  issues: [],
  isStreaming: false,
  isComplete: false,
  error: null,
};

/**
 * Parse JSON issues block from AI response content.
 * Extracts issues array from the ```json block at end of content.
 */
export function parseReviewIssues(content: string): ReviewIssue[] {
  // Look for JSON code block - could be ```json or just ```
  const jsonBlockPattern = /```(?:json)?\s*\n(\{[\s\S]*?\})\s*\n```/;
  const match = content.match(jsonBlockPattern);

  if (!match || !match[1]) {
    return [];
  }

  try {
    const parsed = JSON.parse(match[1]);
    if (parsed.issues && Array.isArray(parsed.issues)) {
      // Validate and clean each issue
      return parsed.issues.map((issue: unknown, index: number) => {
        const i = issue as Record<string, unknown>;
        return {
          id: typeof i.id === 'string' ? i.id : `issue-${index + 1}`,
          category: i.category === 'suggestion' ? 'suggestion' : 'needs_attention',
          title: typeof i.title === 'string' ? i.title : 'Untitled Issue',
          description: typeof i.description === 'string' ? i.description : '',
          pages: Array.isArray(i.pages) ? i.pages.filter((p): p is number => typeof p === 'number') : [1],
        } as ReviewIssue;
      });
    }
  } catch {
    // JSON parse failed - return empty array
    console.warn('Failed to parse review issues JSON');
  }

  return [];
}

/**
 * Parse markdown content into sections.
 * Handles partial content during streaming.
 */
export function parseReviewSections(content: string): AIReviewSections {
  const sections: AIReviewSections = {
    overview: '',
    needsAttention: '',
    lookingGood: '',
    suggestions: '',
  };

  // Section patterns - case insensitive, flexible header matching
  const patterns = [
    { key: 'overview' as const, pattern: /###?\s*Overview\n([\s\S]*?)(?=###|$)/i },
    { key: 'needsAttention' as const, pattern: /###?\s*Needs\s*Attention\n([\s\S]*?)(?=###|$)/i },
    { key: 'lookingGood' as const, pattern: /###?\s*Looking\s*Good\n([\s\S]*?)(?=###|$)/i },
    { key: 'suggestions' as const, pattern: /###?\s*Suggestions\n([\s\S]*?)(?=###|$)/i },
  ];

  for (const { key, pattern } of patterns) {
    const match = content.match(pattern);
    if (match && match[1]) {
      sections[key] = match[1].trim();
    }
  }

  return sections;
}
