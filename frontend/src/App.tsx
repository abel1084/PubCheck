import { useState, useEffect, useRef } from 'react';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { Settings } from './components/Settings';
import { ToastProvider } from './components/Toast/ToastProvider';
import { useExtraction } from './hooks/useExtraction';
import { useComplianceCheck } from './hooks/useComplianceCheck';
import { useAIAnalysis } from './hooks/useAIAnalysis';
import type { DocumentType } from './types/extraction';
import './App.css';

// Map frontend DocumentType to backend document_type IDs
// Backend expects: factsheet, policy-brief, issue-note, working-paper, publication
const DOCUMENT_TYPE_MAP: Record<DocumentType, string> = {
  'Factsheet': 'factsheet',
  'Policy Brief': 'policy-brief',
  'Working Paper': 'working-paper',
  'Technical Report': 'issue-note',  // Technical Report maps to issue-note template
  'Publication': 'publication',
};

function App() {
  const { isUploading, error, result, upload, reset } = useExtraction();
  const { isChecking, checkResult, checkError, runCheck, clearResult } = useComplianceCheck();
  const { isAnalyzing, progress, aiResult, aiError, analyze, reset: resetAI } = useAIAnalysis();
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Store the uploaded file for AI analysis
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
    clearResult();
    resetAI();
    setDocumentType(null);
    uploadedFileRef.current = null;
  };

  // Handle check button click
  const handleCheck = () => {
    if (result && documentType) {
      // Use mapping to convert DocumentType to backend document_type ID
      const docTypeId = DOCUMENT_TYPE_MAP[documentType];
      runCheck(docTypeId, result.extraction);
    }
  };

  // Handle AI analyze button click
  const handleAIAnalyze = () => {
    if (result && documentType && uploadedFileRef.current) {
      // Use mapping to convert DocumentType to backend document_type ID
      const docTypeId = DOCUMENT_TYPE_MAP[documentType];
      analyze(uploadedFileRef.current, result.extraction, docTypeId);
    }
  };

  // Show settings view
  if (showSettings) {
    return (
      <div className="app app--settings">
        <ToastProvider />
        <header className="app__header app__header--compact">
          <h1>PubCheck</h1>
          <button
            type="button"
            className="app__settings-button"
            onClick={() => setShowSettings(false)}
          >
            Back
          </button>
        </header>
        <main className="app__settings-content">
          <Settings onClose={() => setShowSettings(false)} />
        </main>
      </div>
    );
  }

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
            <button
              type="button"
              className="app__settings-button"
              onClick={() => setShowSettings(true)}
            >
              Settings
            </button>
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
          <button
            type="button"
            className={`app__check-button ${isChecking ? 'app__check-button--loading' : ''}`}
            onClick={handleCheck}
            disabled={!result || isChecking}
            title={!result ? 'Upload a PDF first' : 'Run compliance check'}
          >
            {isChecking ? (
              <>
                <span className="app__spinner"></span>
                Checking...
              </>
            ) : (
              'Check'
            )}
          </button>
          <button
            type="button"
            className={`app__ai-button ${isAnalyzing ? 'app__ai-button--loading' : ''}`}
            onClick={handleAIAnalyze}
            disabled={!result || isAnalyzing}
            title={!result ? 'Upload a PDF first' : 'Run AI analysis'}
          >
            {isAnalyzing ? (
              <>
                <span className="app__spinner"></span>
                Analyzing...
              </>
            ) : (
              'Analyze with AI'
            )}
          </button>
          <button
            type="button"
            className="app__settings-button"
            onClick={() => setShowSettings(true)}
          >
            Settings
          </button>
        </div>
      </header>
      {checkError && (
        <div className="app__check-error">
          Check failed: {checkError}
        </div>
      )}
      {aiError && (
        <div className="app__check-error">
          AI analysis failed: {aiError}
        </div>
      )}
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
          <DataTabs
            extraction={result.extraction}
            checkResult={checkResult}
            isChecking={isChecking}
            onRecheck={handleCheck}
            aiResult={aiResult}
            isAnalyzing={isAnalyzing}
            aiProgress={progress}
            onReanalyze={handleAIAnalyze}
            documentType={documentType ? DOCUMENT_TYPE_MAP[documentType] : undefined}
            pdfFile={uploadedFileRef.current}
          />
        </main>
      </div>
    </div>
  );
}

export default App
