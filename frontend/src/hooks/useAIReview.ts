import { useState, useCallback, useRef } from 'react';
import type { ExtractionResult } from '../types/extraction';
import {
  AIReviewState,
  INITIAL_AI_REVIEW_STATE,
  parseReviewSections
} from '../types/review';

/**
 * Hook for streaming AI document review.
 *
 * Sends PDF + extraction to /api/ai/review endpoint,
 * receives SSE stream, and accumulates content progressively.
 */
export function useAIReview() {
  const [state, setState] = useState<AIReviewState>(INITIAL_AI_REVIEW_STATE);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startReview = useCallback(async (
    file: File,
    extraction: ExtractionResult,
    documentType: string,
    confidence: string,
  ) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Reset state
    setState({
      ...INITIAL_AI_REVIEW_STATE,
      isStreaming: true,
    });

    // Build form data
    const formData = new FormData();
    formData.append('file', file);

    // Send extraction as file (not Form field) to avoid size limits
    const extractionBlob = new Blob([JSON.stringify(extraction)], { type: 'application/json' });
    const extractionFile = new File([extractionBlob], 'extraction.json', { type: 'application/json' });
    formData.append('extraction_file', extractionFile);

    formData.append('document_type', documentType);
    formData.append('confidence', confidence.toString());

    try {
      const response = await fetch('/api/ai/review', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Review failed: ${response.status} - ${errorText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Parse SSE format: lines starting with "data: "
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.text) {
                accumulatedContent += data.text;
                setState(prev => ({
                  ...prev,
                  content: accumulatedContent,
                  sections: parseReviewSections(accumulatedContent),
                }));
              }
            } catch {
              // Skip malformed JSON (partial lines)
            }
          }

          // Handle complete event
          if (line.startsWith('event: complete')) {
            // Stream finished - will be handled when reader.done is true
          }
        }
      }

      // Mark as complete
      setState(prev => ({
        ...prev,
        isStreaming: false,
        isComplete: true,
      }));

    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        // Request was cancelled, don't update state
        return;
      }

      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Review failed',
      }));
    }
  }, []);

  const cancelReview = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  const reset = useCallback(() => {
    cancelReview();
    setState(INITIAL_AI_REVIEW_STATE);
  }, [cancelReview]);

  return {
    ...state,
    startReview,
    cancelReview,
    reset,
  };
}
