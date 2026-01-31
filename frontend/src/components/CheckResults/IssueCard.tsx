import type { CheckIssue } from '../../types/checks';

interface IssueCardProps {
  issue: CheckIssue;
  // Review mode props (all optional for backward compatibility)
  issueId?: string;
  isSelected?: boolean;
  note?: string;
  onToggleSelect?: () => void;
  onNoteChange?: (note: string) => void;
}

/**
 * Individual issue card showing severity, message, expected/actual, and pages.
 * Uses details/summary for expandable content per Phase 2 pattern.
 * Supports AI-specific fields: confidence indicator and reasoning section.
 */
export function IssueCard({
  issue,
  issueId,
  isSelected,
  note,
  onToggleSelect,
  onNoteChange
}: IssueCardProps) {
  // Determine if in review mode based on presence of review callbacks
  const isReviewMode = onToggleSelect !== undefined;

  const severityIcon = issue.severity === 'error' ? '\u2022' : '\u26A0';
  const severityClass = issue.severity === 'error' ? 'issue-card--error' : 'issue-card--warning';

  // Add low-confidence muted styling
  const confidenceClass = issue.ai_confidence === 'low' ? 'issue-card--low-confidence' : '';

  // Add selected styling in review mode
  const selectedClass = isReviewMode && isSelected ? 'issue-card--selected' : '';

  // Format page numbers: "Page 1" or "Pages 1, 3, 5"
  const formatPages = (pages: number[]): string => {
    if (pages.length === 0) return '';
    if (pages.length === 1) return `Page ${pages[0]}`;
    return `Pages ${pages.join(', ')}`;
  };

  // Format expected vs actual in compact format: "150 DPI (min 300)"
  const formatComparison = (): string | null => {
    if (!issue.actual && !issue.expected) return null;
    if (issue.actual && issue.expected) {
      return `${issue.actual} (${issue.expected})`;
    }
    return issue.actual || issue.expected || null;
  };

  const comparison = formatComparison();
  const pages = formatPages(issue.pages);
  // Include notes section in hasDetails check for review mode
  const hasDetails = comparison || issue.how_to_fix || issue.ai_reasoning || isReviewMode;

  // Show confidence indicator only for medium/low (high is assumed)
  const showConfidence = issue.ai_confidence && issue.ai_confidence !== 'high';

  return (
    <details className={`issue-card ${severityClass} ${confidenceClass} ${selectedClass}`.trim()}>
      <summary className="issue-card__summary">
        {isReviewMode && (
          <div className="issue-card__selection" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              id={`select-${issueId}`}
              checked={isSelected}
              onChange={onToggleSelect}
              className="issue-card__checkbox"
            />
          </div>
        )}
        <span className={`issue-card__severity issue-card__severity--${issue.severity}`}>
          {severityIcon}
        </span>
        <span className="issue-card__message">{issue.message}</span>
        {showConfidence && (
          <span
            className={`issue-card__confidence issue-card__confidence--${issue.ai_confidence}`}
            title={`${issue.ai_confidence} confidence`}
          >
            {'\u26A0'} {issue.ai_confidence}
          </span>
        )}
        {pages && <span className="issue-card__pages">{pages}</span>}
      </summary>
      {hasDetails && (
        <div className="issue-card__details">
          {comparison && (
            <div className="issue-card__comparison">
              <span className="issue-card__label">Value:</span> {comparison}
            </div>
          )}
          {issue.how_to_fix && (
            <div className="issue-card__fix">
              <span className="issue-card__label">How to fix:</span> {issue.how_to_fix}
            </div>
          )}
          {issue.ai_reasoning && (
            <div className="issue-card__reasoning">
              <span className="issue-card__label">AI reasoning:</span> {issue.ai_reasoning}
            </div>
          )}
          {isReviewMode && (
            <div className="issue-card__notes-section">
              <label htmlFor={`notes-${issueId}`} className="issue-card__notes-label">
                Reviewer Notes:
              </label>
              <textarea
                id={`notes-${issueId}`}
                className="issue-card__notes"
                placeholder="Add notes for report..."
                value={note || ''}
                onChange={(e) => onNoteChange?.(e.target.value)}
                maxLength={200}
                rows={2}
              />
              <span className="issue-card__notes-count">
                {(note || '').length}/200
              </span>
            </div>
          )}
        </div>
      )}
    </details>
  );
}
