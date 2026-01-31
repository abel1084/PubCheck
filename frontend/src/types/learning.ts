/**
 * TypeScript types for the learning system (ignored rules).
 */

export interface IgnoredRule {
  rule_id: string;
  document_type: string;
  reason?: string;
  added_date: string;
}

export interface IgnoredRulesConfig {
  version: string;
  ignored: IgnoredRule[];
}
