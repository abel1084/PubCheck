import type { CheckResult } from '../../types/checks';

interface StatusBadgeProps {
  status: CheckResult['status'];
}

/**
 * Status badge showing pass/fail/warning state.
 * Pass: Green with checkmark
 * Fail: Red with X
 * Warning: Yellow/amber with warning icon
 */
export function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    pass: { label: 'Pass', icon: '\u2713', className: 'status-badge--pass' },
    fail: { label: 'Fail', icon: '\u2717', className: 'status-badge--fail' },
    warning: { label: 'Warning', icon: '\u26A0', className: 'status-badge--warning' },
  };

  const { label, icon, className } = config[status];

  return (
    <span className={`status-badge ${className}`}>
      <span className="status-badge__icon">{icon}</span>
      <span className="status-badge__label">{label}</span>
    </span>
  );
}
