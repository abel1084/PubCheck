import { useState, useCallback } from 'react';
import type { ExtractionResult, DocumentType, Confidence } from '../types/extraction';

interface UploadState {
  isUploading: boolean;
  error: string | null;
  result: {
    filename: string;
    documentType: DocumentType;
    confidence: Confidence;
    extraction: ExtractionResult;
  } | null;
}

export function useExtraction() {
  const [state, setState] = useState<UploadState>({
    isUploading: false,
    error: null,
    result: null,
  });

  const upload = useCallback(async (file: File) => {
    setState({ isUploading: true, error: null, result: null });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8001/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle rejection (rasterized PDF)
        if (data.error === 'rasterized_pdf') {
          setState({
            isUploading: false,
            error: `${data.message} ${data.details}`,
            result: null,
          });
          return;
        }
        throw new Error(data.detail || 'Upload failed');
      }

      setState({
        isUploading: false,
        error: null,
        result: {
          filename: data.filename,
          documentType: data.document_type,
          confidence: data.confidence,
          extraction: data.extraction,
        },
      });
    } catch (err) {
      setState({
        isUploading: false,
        error: err instanceof Error ? err.message : 'Upload failed',
        result: null,
      });
    }
  }, []);

  const reset = useCallback(() => {
    setState({ isUploading: false, error: null, result: null });
  }, []);

  return { ...state, upload, reset };
}
