import type { IgnoredRule } from '../../types/learning';

interface IgnoredRulesTabProps {
  ignoredRules: IgnoredRule[];
  onDelete: (ruleId: string, documentType: string) => void;
  loading: boolean;
}

/**
 * Settings tab displaying list of ignored rules with delete capability.
 */
export function IgnoredRulesTab({ ignoredRules, onDelete, loading }: IgnoredRulesTabProps) {
  if (loading) {
    return <div className="ignored-rules-tab__loading">Loading...</div>;
  }

  if (ignoredRules.length === 0) {
    return (
      <div className="ignored-rules-tab__empty">
        <p>No rules are currently ignored.</p>
        <p className="ignored-rules-tab__hint">
          When reviewing issues, click the X button on an issue to ignore that rule
          for the document type.
        </p>
      </div>
    );
  }

  return (
    <div className="ignored-rules-tab">
      <table className="ignored-rules-tab__table">
        <thead>
          <tr>
            <th>Rule ID</th>
            <th>Document Type</th>
            <th>Reason</th>
            <th>Date Added</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {ignoredRules.map((rule) => (
            <tr key={`${rule.rule_id}-${rule.document_type}`}>
              <td className="ignored-rules-tab__rule-id">{rule.rule_id}</td>
              <td>{rule.document_type}</td>
              <td className="ignored-rules-tab__reason">{rule.reason || '-'}</td>
              <td>{new Date(rule.added_date).toLocaleDateString()}</td>
              <td>
                <button
                  type="button"
                  className="ignored-rules-tab__delete-btn"
                  onClick={() => onDelete(rule.rule_id, rule.document_type)}
                  title="Remove from ignored rules"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
