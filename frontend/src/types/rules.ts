/**
 * TypeScript types for rule configuration.
 * These types mirror the Pydantic models in backend/app/config/models.py
 */

/**
 * Document type identifier for API endpoints.
 */
export type DocumentTypeId =
  | 'factsheet'
  | 'policy-brief'
  | 'issue-note'
  | 'working-paper'
  | 'publication';

/**
 * Rule severity level.
 */
export type Severity = 'error' | 'warning';

/**
 * Type-specific expected values for a rule.
 * Uses Record<string, unknown> for flexibility with different check types.
 *
 * Examples:
 * - position check: { position: "top-right", min_size_mm: 20 }
 * - range check: { min: 9, max: 12, unit: "pt" }
 * - font check: { family: "Roboto Flex", weights: ["Regular", "Bold"] }
 */
export type RuleExpected = Record<string, unknown>;

/**
 * A single compliance rule definition.
 */
export interface Rule {
  name: string;
  description: string;
  enabled: boolean;
  severity: Severity;
  check_type: string;
  expected: RuleExpected;
}

/**
 * A category grouping related rules.
 */
export interface Category {
  name: string;
  rules: Record<string, Rule>;
}

/**
 * Complete rule template for a document type.
 */
export interface Template {
  version: string;
  document_type: string;
  categories: Record<string, Category>;
}

/**
 * User override for a rule - partial fields for customizations.
 */
export interface RuleOverride {
  enabled?: boolean;
  severity?: Severity;
  expected?: Record<string, unknown>;
}

/**
 * User customizations for a document type.
 * Structure: { category_id: { rule_id: RuleOverride } }
 */
export interface UserOverrides {
  version: string;
  overrides: Record<string, Record<string, RuleOverride>>;
}

/**
 * Display labels for document types in the UI.
 */
export const DOCUMENT_TYPE_LABELS: Record<DocumentTypeId, string> = {
  'factsheet': 'Factsheet',
  'policy-brief': 'Policy Brief',
  'issue-note': 'Issue Note',
  'working-paper': 'Working Paper',
  'publication': 'Report/Publication',
};

/**
 * All document type IDs in display order.
 */
export const DOCUMENT_TYPE_IDS: DocumentTypeId[] = [
  'factsheet',
  'policy-brief',
  'issue-note',
  'working-paper',
  'publication',
];
