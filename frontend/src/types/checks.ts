/**
 * TypeScript types for compliance check results.
 * These types mirror the Pydantic models in backend/app/checks/models.py
 */

/**
 * A single compliance issue found during checking.
 */
export interface CheckIssue {
  rule_id: string;
  rule_name: string;
  severity: 'error' | 'warning';
  message: string;
  expected: string | null;
  actual: string | null;
  pages: number[];
  how_to_fix?: string;

  // AI analysis fields
  ai_verified?: boolean;
  ai_confidence?: 'high' | 'medium' | 'low';
  ai_reasoning?: string;
}

/**
 * Results for a single category of checks.
 */
export interface CategoryResult {
  category_id: string;
  category_name: string;
  issues: CheckIssue[];
  error_count: number;
  warning_count: number;
}

/**
 * Complete compliance check result.
 */
export interface CheckResult {
  document_type: string;
  categories: CategoryResult[];
  total_errors: number;
  total_warnings: number;
  status: 'pass' | 'fail' | 'warning';
  check_duration_ms: number;
}
