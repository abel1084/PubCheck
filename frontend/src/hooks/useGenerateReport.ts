import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import type { CheckIssue, CategoryResult } from '../types/checks';
import type { IssueAnnotation } from '../types/output';

interface UseGenerateReportReturn {
  isGenerating: boolean;
  error: string | null;
  generateReport: (
    pdfFile: File,
    categories: CategoryResult[],
    selectedIds: Set<string>,
    notes: Record<string, string>,
    getIssueId: (issue: CheckIssue, categoryId: string, index: number) => string
  ) => Promise<void>;
}

/**
 * Hook for generating annotated PDF reports.
 * Handles building annotations from selected issues and downloading the result.
 */
export function useGenerateReport(): UseGenerateReportReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = useCallback(async (
    pdfFile: File,
    categories: CategoryResult[],
    selectedIds: Set<string>,
    notes: Record<string, string>,
    getIssueId: (issue: CheckIssue, categoryId: string, index: number) => string
  ) => {
    setIsGenerating(true);
    setError(null);

    try {
      // Build annotations from selected issues
      const annotations: IssueAnnotation[] = [];

      for (const category of categories) {
        category.issues.forEach((issue, index) => {
          const issueId = getIssueId(issue, category.category_id, index);
          if (selectedIds.has(issueId)) {
            // For each page the issue occurs on
            for (const page of issue.pages) {
              annotations.push({
                page,
                x: null,  // No coordinates available from CheckIssue
                y: null,
                message: issue.message,
                severity: issue.severity,
                reviewer_note: notes[issueId] || undefined,
              });
            }
          }
        });
      }

      if (annotations.length === 0) {
        throw new Error('No issues selected');
      }

      // Create form data
      const formData = new FormData();
      formData.append('pdf', pdfFile);
      formData.append('issues', JSON.stringify({ issues: annotations }));

      // Call API using relative URL (per LEARNINGS.md)
      const response = await fetch('/api/output/annotate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to generate annotated PDF');
      }

      // Get blob and trigger download
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
      const filename = filenameMatch?.[1] || 'annotated.pdf';

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Annotated PDF downloaded');
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Unknown error';
      setError(message);
      toast.error(`Failed to generate report: ${message}`);
    } finally {
      setIsGenerating(false);
    }
  }, []);

  return { isGenerating, error, generateReport };
}
