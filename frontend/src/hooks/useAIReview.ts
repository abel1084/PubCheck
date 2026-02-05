import { useState, useCallback, useRef } from 'react';
import type { ExtractionResult } from '../types/extraction';
import {
  AIReviewState,
  INITIAL_AI_REVIEW_STATE,
  parseReviewSections,
  parseReviewIssues,
  ChunkProgress,
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
    confidence: number,
    outputFormat: string = 'digital',
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

    // Send extraction as file to bypass form field size limits for large documents
    const extractionBlob = new Blob([JSON.stringify(extraction)], { type: 'application/json' });
    formData.append('extraction_file', extractionBlob, 'extraction.json');

    formData.append('document_type', documentType);
    formData.append('confidence', confidence.toString());
    formData.append('output_format', outputFormat);

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
      let currentEventType = 'text';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Parse SSE format: event type lines and data lines
        const lines = chunk.split('\n');
        for (const line of lines) {
          // Handle event type lines
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim();
            continue;
          }

          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (currentEventType) {
                case 'review_start':
                  // Large document - chunked review starting
                  setState(prev => ({
                    ...prev,
                    isChunked: true,
                    totalChunks: data.total_chunks || 0,
                    completedChunks: 0,
                    chunkProgress: [],
                  }));
                  break;

                case 'chunk_progress': {
                  // Chunk completed or failed
                  const pages = data.pages?.split('-') || ['1', '1'];
                  const progress: ChunkProgress = {
                    chunk: data.chunk,
                    total: data.total,
                    startPage: parseInt(pages[0] || '1', 10),
                    endPage: parseInt(pages[1] || '1', 10),
                    success: data.status === 'complete',
                    error: data.error,
                  };
                  setState(prev => ({
                    ...prev,
                    completedChunks: prev.completedChunks + 1,
                    chunkProgress: [...prev.chunkProgress, progress],
                  }));
                  break;
                }

                case 'text':
                  if (data.text) {
                    accumulatedContent += data.text;
                    setState(prev => ({
                      ...prev,
                      content: accumulatedContent,
                      sections: parseReviewSections(accumulatedContent),
                    }));
                  }
                  break;

                case 'complete':
                  // Review finished
                  setState(prev => ({
                    ...prev,
                    isStreaming: false,
                    isComplete: true,
                    issues: parseReviewIssues(prev.content),
                  }));
                  break;

                case 'error':
                  setState(prev => ({
                    ...prev,
                    isStreaming: false,
                    error: data.error || 'Unknown error',
                  }));
                  break;

                default:
                  // Legacy text event (backwards compatibility)
                  if (data.text) {
                    accumulatedContent += data.text;
                    setState(prev => ({
                      ...prev,
                      content: accumulatedContent,
                      sections: parseReviewSections(accumulatedContent),
                    }));
                  }
              }

              currentEventType = 'text'; // Reset to default after processing
            } catch {
              // Skip malformed JSON (partial lines)
            }
          }
        }
      }

      // Mark as complete if not already (fallback for non-event completion)
      setState(prev => {
        if (prev.isComplete) return prev;
        return {
          ...prev,
          isStreaming: false,
          isComplete: true,
          issues: parseReviewIssues(prev.content),
        };
      });

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
