/**
 * TypeScript types for output generation.
 */

/**
 * A single issue annotation to be placed in the PDF.
 */
export interface IssueAnnotation {
  page: number;
  x: number | null;
  y: number | null;
  message: string;
  severity: 'error' | 'warning';
  reviewer_note?: string;
}

/**
 * State for the report generation process.
 */
export interface GenerateReportState {
  isGenerating: boolean;
  error: string | null;
}
