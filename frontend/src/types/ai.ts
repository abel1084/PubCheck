/**
 * TypeScript types for AI analysis results.
 * Mirrors backend/app/ai/schemas.py
 */

/**
 * A single finding from AI analysis.
 */
export interface AIFinding {
  check_name: string;
  passed: boolean;
  confidence: 'high' | 'medium' | 'low';
  message: string;
  reasoning?: string;
  location?: string;
  suggestion?: string;
}

/**
 * Analysis result for a single page.
 */
export interface PageAnalysisResult {
  page_number: number;
  findings: AIFinding[];
  error?: string;
}

/**
 * Complete document analysis result.
 */
export interface DocumentAnalysisResult {
  page_results: PageAnalysisResult[];
  document_summary?: string;
  total_findings: number;
  analysis_duration_ms: number;
}
