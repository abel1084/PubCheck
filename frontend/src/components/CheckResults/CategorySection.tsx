import type { CategoryResult, CheckIssue } from '../../types/checks';
import { IssueCard } from './IssueCard';

interface CategorySectionProps {
  category: CategoryResult;
}

/**
 * Collapsible category section using native details/summary.
 * Categories with errors expanded by default, others collapsed.
 * Issues sorted: errors first, then warnings.
 */
export function CategorySection({ category }: CategorySectionProps) {
  const hasIssues = category.issues.length > 0;
  const totalIssues = category.error_count + category.warning_count;

  // Sort issues: errors first, then warnings
  const sortedIssues = [...category.issues].sort((a: CheckIssue, b: CheckIssue) => {
    if (a.severity === 'error' && b.severity === 'warning') return -1;
    if (a.severity === 'warning' && b.severity === 'error') return 1;
    return 0;
  });

  // Expand by default if category has errors
  const defaultOpen = category.error_count > 0;

  return (
    <details
      className={`category-section ${hasIssues ? 'category-section--has-issues' : ''}`}
      open={defaultOpen}
    >
      <summary className="category-section__header">
        <span className="category-section__name">{category.category_name}</span>
        {hasIssues ? (
          <span className="category-section__count">
            {totalIssues}
          </span>
        ) : (
          <span className="category-section__check">{'\u2713'}</span>
        )}
      </summary>
      <div className="category-section__content">
        {hasIssues ? (
          <div className="category-section__issues">
            {sortedIssues.map((issue, index) => (
              <IssueCard key={`${issue.rule_id}-${index}`} issue={issue} />
            ))}
          </div>
        ) : (
          <div className="category-section__empty">No issues</div>
        )}
      </div>
    </details>
  );
}
