import { useState, useEffect, useRef } from 'react';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { ReviewResults } from './components/ReviewResults/ReviewResults';
import { ToastProvider } from './components/Toast/ToastProvider';
import { useExtraction } from './hooks/useExtraction';
import { useAIReview } from './hooks/useAIReview';
import type { DocumentType, Confidence } from './types/extraction';
import './App.css';

// Output format types for DPI requirements
type OutputFormat = 'print' | 'digital' | 'both';

// Map frontend DocumentType to backend document_type IDs
const DOCUMENT_TYPE_MAP: Record<DocumentType, string> = {
  'Factsheet': 'factsheet',
  'Policy Brief': 'policy-brief',
  'Working Paper': 'working-paper',
  'Technical Report': 'issue-note',
  'Publication': 'publication',
};

// Map confidence strings to numeric values for AI review
const CONFIDENCE_MAP: Record<Confidence, number> = {
  'high': 0.95,
  'medium': 0.75,
  'low': 0.5,
};

function App() {
  const { isUploading, error, result, upload, reset } = useExtraction();
  const {
    sections,
    isStreaming,
    isComplete,
    error: reviewError,
    startReview,
    reset: resetReview
  } = useAIReview();

  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('digital');
  const uploadedFileRef = useRef<File | null>(null);

  // Sync document type from result when it changes
  useEffect(() => {
    if (result && documentType === null) {
      setDocumentType(result.documentType);
    }
  }, [result, documentType]);

  // Custom upload handler that stores the file
  const handleUpload = (file: File) => {
    uploadedFileRef.current = file;
    upload(file);
  };

  const handleNewDocument = () => {
    reset();
    resetReview();
    setDocumentType(null);
    setOutputFormat('digital');
    uploadedFileRef.current = null;
  };

  // Handle review button click
  const handleReview = () => {
    if (result && documentType && uploadedFileRef.current) {
      const docTypeId = DOCUMENT_TYPE_MAP[documentType];
      const confidenceNum = CONFIDENCE_MAP[result.confidence];
      startReview(
        uploadedFileRef.current,
        result.extraction,
        docTypeId,
        confidenceNum,
        outputFormat
      );
    }
  };

  // Show upload view if no result
  if (!result) {
    return (
      <div className="app app--upload">
        <ToastProvider />
        <header className="app__header">
          <div className="app__header-content">
            <div>
              <h1>PubCheck</h1>
              <p>UNEP PDF Design Compliance Checker</p>
            </div>
          </div>
        </header>
        <main className="app__upload-area">
          <DropZone
            onFileAccepted={handleUpload}
            isProcessing={isUploading}
            error={error}
          />
        </main>
      </div>
    );
  }

  // Show results view
  return (
    <div className="app app--results">
      <ToastProvider />
      <header className="app__header app__header--compact">
        <h1>PubCheck</h1>
        <div className="app__header-buttons">
          <label className="app__output-format">
            <span className="app__output-format-label">Output:</span>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
              disabled={isStreaming}
              className="app__output-format-select"
            >
              <option value="digital">Digital (72 DPI)</option>
              <option value="print">Print (300 DPI)</option>
              <option value="both">Both (150 DPI)</option>
            </select>
          </label>
          <button
            type="button"
            className={`app__review-button ${isStreaming ? 'app__review-button--loading' : ''}`}
            onClick={handleReview}
            disabled={!result || isStreaming}
            title={!result ? 'Upload a PDF first' : 'Run design review'}
          >
            {isStreaming ? (
              <>
                <span className="app__spinner"></span>
                Reviewing...
              </>
            ) : (
              'Review'
            )}
          </button>
        </div>
      </header>

      <div className="app__content">
        <Sidebar
          filename={result.filename}
          documentType={documentType || result.documentType}
          confidence={result.confidence}
          metadata={result.extraction.metadata}
          onDocumentTypeChange={setDocumentType}
          onNewDocument={handleNewDocument}
        />
        <main className="app__main">
          <ReviewResults
            sections={sections}
            isStreaming={isStreaming}
            isComplete={isComplete}
            error={reviewError}
            onRetry={handleReview}
          />
          <DataTabs
            extraction={result.extraction}
            defaultCollapsed={true}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
