import { useState, useCallback } from 'react';
import type { ExtractionResult } from '../types/extraction';
import type { CheckResult } from '../types/checks';

interface UseComplianceCheckResult {
  isChecking: boolean;
  checkResult: CheckResult | null;
  checkError: string | null;
  runCheck: (documentType: string, extraction: ExtractionResult) => Promise<void>;
  clearResult: () => void;
}

/**
 * Hook for running compliance checks and managing check state.
 * Calls the backend check API and tracks loading/error states.
 */
export function useComplianceCheck(): UseComplianceCheckResult {
  const [isChecking, setIsChecking] = useState(false);
  const [checkResult, setCheckResult] = useState<CheckResult | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);

  const runCheck = useCallback(async (
    documentType: string,
    extraction: ExtractionResult
  ) => {
    setIsChecking(true);
    setCheckError(null);

    try {
      const response = await fetch(`http://localhost:8002/api/check/${documentType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extraction),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Check failed: ${response.statusText}`);
      }

      const result: CheckResult = await response.json();
      setCheckResult(result);
    } catch (error) {
      setCheckError(error instanceof Error ? error.message : 'Check failed');
    } finally {
      setIsChecking(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setCheckResult(null);
    setCheckError(null);
  }, []);

  return { isChecking, checkResult, checkError, runCheck, clearResult };
}
