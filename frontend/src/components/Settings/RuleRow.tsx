import type { Rule, Severity } from '../../types/rules';

interface RuleRowProps {
  ruleId: string;
  rule: Rule;
  categoryId: string;
  onToggle: (categoryId: string, ruleId: string) => void;
  onSeverityChange: (categoryId: string, ruleId: string, severity: Severity) => void;
}

/**
 * Format expected values as a readable summary.
 */
function formatExpected(expected: Record<string, unknown>): string {
  const parts: string[] = [];

  // Handle common patterns
  if ('min' in expected && 'max' in expected) {
    const unit = expected.unit || '';
    parts.push(`${expected.min}-${expected.max}${unit}`);
  } else if ('min' in expected) {
    const unit = expected.unit || '';
    parts.push(`min ${expected.min}${unit}`);
  } else if ('max' in expected) {
    const unit = expected.unit || '';
    parts.push(`max ${expected.max}${unit}`);
  }

  if ('position' in expected) {
    parts.push(String(expected.position));
  }

  if ('family' in expected) {
    parts.push(String(expected.family));
  }

  if ('required' in expected) {
    parts.push(expected.required ? 'required' : 'optional');
  }

  if ('pattern' in expected) {
    parts.push('regex pattern');
  }

  if ('hex' in expected) {
    parts.push(String(expected.hex));
  }

  // If nothing matched, show first value
  if (parts.length === 0) {
    const firstValue = Object.values(expected)[0];
    if (firstValue !== undefined) {
      parts.push(String(firstValue));
    }
  }

  return parts.join(', ');
}

/**
 * Individual rule display row with checkbox and severity toggle.
 */
export function RuleRow({
  ruleId,
  rule,
  categoryId,
  onToggle,
  onSeverityChange,
}: RuleRowProps) {
  const expectedSummary = formatExpected(rule.expected);

  const handleSeverityClick = () => {
    if (!rule.enabled) return;
    const newSeverity: Severity = rule.severity === 'error' ? 'warning' : 'error';
    onSeverityChange(categoryId, ruleId, newSeverity);
  };

  return (
    <div className={`rule-row ${!rule.enabled ? 'rule-row--disabled' : ''}`}>
      <label className="rule-row__checkbox-label">
        <input
          type="checkbox"
          className="rule-row__checkbox"
          checked={rule.enabled}
          onChange={() => onToggle(categoryId, ruleId)}
        />
        <span className="rule-row__name">{rule.name}</span>
        {expectedSummary && (
          <span className="rule-row__expected">: {expectedSummary}</span>
        )}
      </label>
      <button
        type="button"
        className={`rule-row__severity rule-row__severity--${rule.severity}`}
        onClick={handleSeverityClick}
        disabled={!rule.enabled}
        title={`Switch to ${rule.severity === 'error' ? 'warning' : 'error'}`}
      >
        {rule.severity === 'error' ? 'Error' : 'Warning'}
      </button>
    </div>
  );
}
