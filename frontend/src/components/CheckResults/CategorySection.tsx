import type { CategoryResult, CheckIssue } from '../../types/checks';
import { IssueCard } from './IssueCard';

interface CategorySectionProps {
  category: CategoryResult;
  // Review mode props (all optional for backward compatibility)
  issueIds?: string[];  // IDs of issues in this category
  selectedIds?: Set<string>;  // Currently selected issue IDs
  notes?: Record<string, string>;  // Issue ID -> note text
  onToggleSelect?: (issueId: string) => void;
  onSelectCategory?: () => void;  // Select all in this category
  onDeselectCategory?: () => void;  // Deselect all in this category
  onNoteChange?: (issueId: string, note: string) => void;
  onIgnoreRule?: (ruleId: string) => void;  // Ignore rule callback
}

/**
 * Collapsible category section using native details/summary.
 * Categories with errors expanded by default, others collapsed.
 * Issues sorted: errors first, then warnings.
 */
export function CategorySection({
  category,
  issueIds,
  selectedIds,
  notes,
  onToggleSelect,
  onSelectCategory,
  onDeselectCategory,
  onNoteChange,
  onIgnoreRule
}: CategorySectionProps) {
  // Determine if in review mode based on presence of review callbacks
  const isReviewMode = onToggleSelect !== undefined;

  const hasIssues = category.issues.length > 0;
  const totalIssues = category.error_count + category.warning_count;

  // Calculate category selection state (for indeterminate checkbox)
  const selectedInCategory = issueIds?.filter(id => selectedIds?.has(id)).length ?? 0;
  const totalInCategory = issueIds?.length ?? 0;
  const isAllSelected = selectedInCategory === totalInCategory && totalInCategory > 0;
  const isPartiallySelected = selectedInCategory > 0 && selectedInCategory < totalInCategory;

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
        {isReviewMode && hasIssues && (
          <div className="category-section__selection" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={isAllSelected}
              ref={(el) => { if (el) el.indeterminate = isPartiallySelected; }}
              onChange={() => isAllSelected ? onDeselectCategory?.() : onSelectCategory?.()}
              className="category-section__checkbox"
              title={isAllSelected ? 'Deselect all in category' : 'Select all in category'}
            />
            <span className="category-section__selection-count">
              {selectedInCategory}/{totalInCategory}
            </span>
          </div>
        )}
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
            {sortedIssues.map((issue, index) => {
              const issueId = issueIds?.[index];
              return (
                <IssueCard
                  key={`${issue.rule_id}-${index}`}
                  issue={issue}
                  issueId={issueId}
                  isSelected={issueId ? selectedIds?.has(issueId) : false}
                  note={issueId ? notes?.[issueId] : undefined}
                  onToggleSelect={issueId && onToggleSelect ? () => onToggleSelect(issueId) : undefined}
                  onNoteChange={issueId && onNoteChange ? (note) => onNoteChange(issueId, note) : undefined}
                  onIgnoreRule={onIgnoreRule}
                />
              );
            })}
          </div>
        ) : (
          <div className="category-section__empty">No issues</div>
        )}
      </div>
    </details>
  );
}
