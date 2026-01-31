import { useState, useCallback, useEffect } from 'react';
import type { IgnoredRule } from '../types/learning';

interface UseIgnoredRulesReturn {
  ignoredRules: IgnoredRule[];
  ignoredRuleIds: Set<string>;  // For quick lookup by rule_id (doc-type scoped)
  loading: boolean;
  error: string | null;
  ignoreRule: (ruleId: string, documentType: string, reason?: string) => Promise<void>;
  unignoreRule: (ruleId: string, documentType: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useIgnoredRules(documentType: string | null): UseIgnoredRulesReturn {
  const [ignoredRules, setIgnoredRules] = useState<IgnoredRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Set of rule_ids ignored for current document type
  const ignoredRuleIds = new Set(
    ignoredRules
      .filter(r => r.document_type === documentType)
      .map(r => r.rule_id)
  );

  const fetchIgnoredRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ignored-rules');
      if (!response.ok) throw new Error('Failed to fetch ignored rules');
      const data = await response.json();
      setIgnoredRules(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const ignoreRule = useCallback(async (ruleId: string, docType: string, reason?: string) => {
    const response = await fetch('/api/ignored-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_id: ruleId, document_type: docType, reason }),
    });
    if (!response.ok) throw new Error('Failed to ignore rule');
    const newRule = await response.json();
    setIgnoredRules(prev => [...prev, newRule]);
  }, []);

  const unignoreRule = useCallback(async (ruleId: string, docType: string) => {
    const response = await fetch(`/api/ignored-rules/${encodeURIComponent(ruleId)}/${encodeURIComponent(docType)}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to unignore rule');
    setIgnoredRules(prev => prev.filter(r => !(r.rule_id === ruleId && r.document_type === docType)));
  }, []);

  useEffect(() => {
    fetchIgnoredRules();
  }, [fetchIgnoredRules]);

  return {
    ignoredRules,
    ignoredRuleIds,
    loading,
    error,
    ignoreRule,
    unignoreRule,
    refresh: fetchIgnoredRules,
  };
}
