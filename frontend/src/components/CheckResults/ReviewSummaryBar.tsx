import type { SeverityFilter, ReviewCounts } from '../../types/review';

/**
 * Props for the ReviewSummaryBar component.
 */
interface ReviewSummaryBarProps {
  /** Computed count values from review state */
  counts: ReviewCounts;
  /** Current severity filter selection */
  severityFilter: SeverityFilter;
  /** Callback when filter selection changes */
  onFilterChange: (filter: SeverityFilter) => void;
  /** Callback to select all currently visible issues */
  onSelectAllVisible: () => void;
  /** Callback to deselect all issues */
  onDeselectAll: () => void;
  /** Whether the Generate Report button should be enabled */
  canGenerateReport: boolean;
  /** Whether report generation is in progress */
  isGenerating: boolean;
  /** Callback when Generate Report is clicked */
  onGenerateReport?: () => void;
}

/**
 * Summary bar component for the review interface.
 * Displays issue counts, severity filter buttons, selection actions,
 * and the Generate Report button.
 *
 * Fixed position at the bottom of the viewport per CONTEXT.md.
 * CSS styling will be added in plan 03.
 */
export function ReviewSummaryBar({
  counts,
  severityFilter,
  onFilterChange,
  onSelectAllVisible,
  onDeselectAll,
  canGenerateReport,
  isGenerating,
  onGenerateReport,
}: ReviewSummaryBarProps) {
  // Show visible selected vs total selected when filter hides selected items
  const selectionText =
    counts.visibleSelected !== counts.selected
      ? `${counts.selected} selected (${counts.visibleSelected} visible)`
      : `${counts.selected} selected`;

  return (
    <div className="review-summary-bar">
      {/* Counts section */}
      <div className="review-summary-bar__counts">
        <span className="review-summary-bar__total">{counts.total} issues</span>
        <span className="review-summary-bar__selected">({selectionText})</span>
        <span className="review-summary-bar__breakdown">
          - {counts.errors} Errors, {counts.warnings} Warnings
        </span>
      </div>

      {/* Filter toggle buttons */}
      <div className="review-summary-bar__filters">
        <button
          type="button"
          className={`review-summary-bar__filter-btn ${
            severityFilter === 'all' ? 'review-summary-bar__filter-btn--active' : ''
          }`}
          onClick={() => onFilterChange('all')}
          aria-pressed={severityFilter === 'all'}
        >
          All
        </button>
        <button
          type="button"
          className={`review-summary-bar__filter-btn ${
            severityFilter === 'error' ? 'review-summary-bar__filter-btn--active' : ''
          }`}
          onClick={() => onFilterChange('error')}
          aria-pressed={severityFilter === 'error'}
        >
          Errors
        </button>
        <button
          type="button"
          className={`review-summary-bar__filter-btn ${
            severityFilter === 'warning' ? 'review-summary-bar__filter-btn--active' : ''
          }`}
          onClick={() => onFilterChange('warning')}
          aria-pressed={severityFilter === 'warning'}
        >
          Warnings
        </button>
      </div>

      {/* Selection actions */}
      <div className="review-summary-bar__actions">
        <button
          type="button"
          className="review-summary-bar__action-btn"
          onClick={onSelectAllVisible}
        >
          Select All Visible
        </button>
        <button
          type="button"
          className="review-summary-bar__action-btn"
          onClick={onDeselectAll}
        >
          Deselect All
        </button>
      </div>

      {/* Generate Report button */}
      <div className="review-summary-bar__report">
        <button
          type="button"
          className="review-summary-bar__report-btn"
          disabled={!canGenerateReport || isGenerating}
          onClick={onGenerateReport}
          title={
            isGenerating
              ? 'Generating report...'
              : canGenerateReport
                ? 'Generate PDF report'
                : 'Select at least one issue'
          }
        >
          {isGenerating ? 'Generating...' : 'Generate Report'}
        </button>
      </div>
    </div>
  );
}
