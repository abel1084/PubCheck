import type { CheckResult, CategoryResult } from '../../types/checks';
import { StatusBadge } from './StatusBadge';
import { CategorySection } from './CategorySection';
import './CheckResults.css';

interface CheckResultsProps {
  result: CheckResult;
  onRecheck?: () => void;
}

// Fixed category order per CONTEXT.md
const CATEGORY_ORDER = ['cover', 'margins', 'typography', 'images', 'required_elements'];

/**
 * Main check results component.
 * Shows status badge, summary counts, and categorized issues.
 * Pass status shows green success banner.
 */
export function CheckResults({ result, onRecheck }: CheckResultsProps) {
  // Sort categories by fixed order
  const sortedCategories = [...result.categories].sort((a: CategoryResult, b: CategoryResult) => {
    const aIndex = CATEGORY_ORDER.indexOf(a.category_id);
    const bIndex = CATEGORY_ORDER.indexOf(b.category_id);
    // Unknown categories go to end
    const aOrder = aIndex === -1 ? CATEGORY_ORDER.length : aIndex;
    const bOrder = bIndex === -1 ? CATEGORY_ORDER.length : bIndex;
    return aOrder - bOrder;
  });

  const isAllPassed = result.status === 'pass';

  return (
    <div className="check-results">
      <div className="check-results__header">
        <div className="check-results__title-row">
          <h3 className="check-results__title">Compliance Check Results</h3>
          <StatusBadge status={result.status} />
        </div>
        <div className="check-results__summary">
          {result.total_errors > 0 && (
            <span className="check-results__count check-results__count--error">
              {result.total_errors} error{result.total_errors !== 1 ? 's' : ''}
            </span>
          )}
          {result.total_warnings > 0 && (
            <span className="check-results__count check-results__count--warning">
              {result.total_warnings} warning{result.total_warnings !== 1 ? 's' : ''}
            </span>
          )}
          {onRecheck && (
            <button
              type="button"
              className="check-results__recheck"
              onClick={onRecheck}
            >
              Re-check
            </button>
          )}
        </div>
      </div>

      {isAllPassed ? (
        <div className="check-results__success">
          <span className="check-results__success-icon">{'\u2713'}</span>
          <span className="check-results__success-text">All checks passed</span>
        </div>
      ) : (
        <div className="check-results__categories">
          {sortedCategories.map((category) => (
            <CategorySection key={category.category_id} category={category} />
          ))}
        </div>
      )}

      <div className="check-results__footer">
        <span className="check-results__duration">
          Check completed in {result.check_duration_ms}ms
        </span>
      </div>
    </div>
  );
}
