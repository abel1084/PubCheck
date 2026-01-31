import type { CheckIssue } from '../../types/checks';

interface IssueCardProps {
  issue: CheckIssue;
}

/**
 * Individual issue card showing severity, message, expected/actual, and pages.
 * Uses details/summary for expandable content per Phase 2 pattern.
 */
export function IssueCard({ issue }: IssueCardProps) {
  const severityIcon = issue.severity === 'error' ? '\u2022' : '\u26A0';
  const severityClass = issue.severity === 'error' ? 'issue-card--error' : 'issue-card--warning';

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
  const hasDetails = comparison || issue.how_to_fix;

  return (
    <details className={`issue-card ${severityClass}`}>
      <summary className="issue-card__summary">
        <span className={`issue-card__severity issue-card__severity--${issue.severity}`}>
          {severityIcon}
        </span>
        <span className="issue-card__message">{issue.message}</span>
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
        </div>
      )}
    </details>
  );
}
