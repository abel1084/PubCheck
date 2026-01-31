import type { Category, Severity } from '../../types/rules';
import { RuleRow } from './RuleRow';

interface RuleCategoryProps {
  categoryId: string;
  category: Category;
  onToggle: (categoryId: string, ruleId: string) => void;
  onSeverityChange: (categoryId: string, ruleId: string, severity: Severity) => void;
}

/**
 * Collapsible category section containing rules.
 * Uses native HTML details/summary for expand/collapse.
 */
export function RuleCategory({
  categoryId,
  category,
  onToggle,
  onSeverityChange,
}: RuleCategoryProps) {
  const ruleEntries = Object.entries(category.rules);
  const totalCount = ruleEntries.length;
  const enabledCount = ruleEntries.filter(([, rule]) => rule.enabled).length;

  return (
    <details className="rule-category" open>
      <summary className="rule-category__header">
        <span className="rule-category__name">{category.name}</span>
        <span className="rule-category__count">
          ({enabledCount}/{totalCount} enabled)
        </span>
      </summary>
      <div className="rule-category__content">
        {ruleEntries.map(([ruleId, rule]) => (
          <RuleRow
            key={ruleId}
            ruleId={ruleId}
            rule={rule}
            categoryId={categoryId}
            onToggle={onToggle}
            onSeverityChange={onSeverityChange}
          />
        ))}
      </div>
    </details>
  );
}
