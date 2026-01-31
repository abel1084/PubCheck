import { useState, useEffect } from 'react';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { Settings } from './components/Settings';
import { useExtraction } from './hooks/useExtraction';
import { useComplianceCheck } from './hooks/useComplianceCheck';
import type { DocumentType } from './types/extraction';
import './App.css';

function App() {
  const { isUploading, error, result, upload, reset } = useExtraction();
  const { isChecking, checkResult, checkError, runCheck, clearResult } = useComplianceCheck();
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Sync document type from result when it changes
  useEffect(() => {
    if (result && documentType === null) {
      setDocumentType(result.documentType);
    }
  }, [result, documentType]);

  const handleNewDocument = () => {
    reset();
    clearResult();
    setDocumentType(null);
  };

  // Handle check button click
  const handleCheck = () => {
    if (result && documentType) {
      // Convert DocumentType to lowercase for API endpoint
      const docTypeId = documentType.toLowerCase().replace(/\s+/g, '_');
      runCheck(docTypeId, result.extraction);
    }
  };

  // Show settings view
  if (showSettings) {
    return (
      <div className="app app--settings">
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
            onFileAccepted={upload}
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
          />
        </main>
      </div>
    </div>
  );
}

export default App
