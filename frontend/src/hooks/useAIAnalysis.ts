import { useState, useCallback } from 'react';
import type { DocumentAnalysisResult } from '../types/ai';
import type { ExtractionResult } from '../types/extraction';

interface UseAIAnalysisReturn {
  isAnalyzing: boolean;
  progress: string;  // "Analyzing page 3 of 12..."
  aiResult: DocumentAnalysisResult | null;
  aiError: string | null;
  analyze: (file: File, extraction: ExtractionResult, documentType: string) => Promise<void>;
  reset: () => void;
}

/**
 * Hook for running AI analysis and managing analysis state.
 * Calls the backend AI analysis API and tracks loading/error states.
 */
export function useAIAnalysis(): UseAIAnalysisReturn {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState('');
  const [aiResult, setAIResult] = useState<DocumentAnalysisResult | null>(null);
  const [aiError, setAIError] = useState<string | null>(null);

  const analyze = useCallback(async (
    file: File,
    extraction: ExtractionResult,
    documentType: string
  ) => {
    setIsAnalyzing(true);
    setProgress('Starting AI analysis...');
    setAIError(null);
    setAIResult(null);

    try {
      // Show progress based on page count
      const pageCount = extraction.metadata.page_count;
      setProgress(`Analyzing ${pageCount} page${pageCount !== 1 ? 's' : ''}...`);

      // Send extraction as a JSON file to avoid Form field size limits
      const extractionBlob = new Blob([JSON.stringify(extraction)], { type: 'application/json' });
      const extractionFile = new File([extractionBlob], 'extraction.json', { type: 'application/json' });

      const formData = new FormData();
      formData.append('file', file);
      formData.append('extraction_file', extractionFile);
      formData.append('document_type', documentType);

      const response = await fetch('/api/ai/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'AI analysis failed');
      }

      const result: DocumentAnalysisResult = await response.json();
      setAIResult(result);
      setProgress('');
    } catch (err) {
      setAIError(err instanceof Error ? err.message : 'AI analysis failed');
      setProgress('');
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsAnalyzing(false);
    setProgress('');
    setAIResult(null);
    setAIError(null);
  }, []);

  return { isAnalyzing, progress, aiResult, aiError, analyze, reset };
}
