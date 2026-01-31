import { useState, useEffect } from 'react';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { useExtraction } from './hooks/useExtraction';
import type { DocumentType } from './types/extraction';
import './App.css';

function App() {
  const { isUploading, error, result, upload, reset } = useExtraction();
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);

  // Sync document type from result when it changes
  useEffect(() => {
    if (result && documentType === null) {
      setDocumentType(result.documentType);
    }
  }, [result, documentType]);

  const handleNewDocument = () => {
    reset();
    setDocumentType(null);
  };

  // Show upload view if no result
  if (!result) {
    return (
      <div className="app app--upload">
        <header className="app__header">
          <h1>PubCheck</h1>
          <p>UNEP PDF Design Compliance Checker</p>
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
          <DataTabs extraction={result.extraction} />
        </main>
      </div>
    </div>
  );
}

export default App
