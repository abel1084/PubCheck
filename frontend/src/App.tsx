import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { ReviewResults } from './components/ReviewResults/ReviewResults';
import { CommentList } from './components/CommentList/CommentList';
import { ToastProvider } from './components/Toast/ToastProvider';
import { useExtraction } from './hooks/useExtraction';
import { useAIReview } from './hooks/useAIReview';
import type { DocumentType, Confidence } from './types/extraction';
import './App.css';

// Tab types for review views
type ReviewTab = 'review' | 'comments';

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
    issues,
    isStreaming,
    isComplete,
    error: reviewError,
    startReview,
    reset: resetReview
  } = useAIReview();

  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('digital');
  const [activeTab, setActiveTab] = useState<ReviewTab>('review');
  const [selectedIssueIds, setSelectedIssueIds] = useState<Set<string>>(new Set());
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const uploadedFileRef = useRef<File | null>(null);

  // Toggle issue selection
  const handleToggleIssue = useCallback((id: string) => {
    setSelectedIssueIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // Initialize selection when issues change (select all by default)
  useEffect(() => {
    if (issues.length > 0) {
      setSelectedIssueIds(new Set(issues.map(i => i.id)));
    }
  }, [issues]);

  // Generate annotated PDF from selected issues
  const handleGeneratePdf = useCallback(async () => {
    if (!uploadedFileRef.current || selectedIssueIds.size === 0) {
      return;
    }

    setIsGeneratingPdf(true);

    try {
      // Convert selected ReviewIssues to IssueAnnotation format
      const selectedIssues = issues.filter(i => selectedIssueIds.has(i.id));

      // Build annotations array - one annotation per page per issue
      const annotations: Array<{
        page: number;
        x: number | null;
        y: number | null;
        message: string;
        severity: 'error' | 'warning';
        reviewer_note?: string;
      }> = [];

      for (const issue of selectedIssues) {
        // Map category to severity
        const severity = issue.category === 'needs_attention' ? 'error' : 'warning';

        // Create annotation for each page
        for (const page of issue.pages) {
          annotations.push({
            page,
            x: null,  // No coordinates from AI review
            y: null,
            message: `${issue.title}\n\n${issue.description}`,
            severity,
          });
        }
      }

      // Create form data
      const formData = new FormData();
      formData.append('pdf', uploadedFileRef.current);
      formData.append('issues', JSON.stringify({ issues: annotations }));

      // Call annotation endpoint (relative URL per LEARNINGS.md)
      const response = await fetch('/api/output/annotate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to generate annotated PDF');
      }

      // Download the result
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
      toast.error(`Failed to generate PDF: ${message}`);
    } finally {
      setIsGeneratingPdf(false);
    }
  }, [issues, selectedIssueIds]);

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
    setActiveTab('review');
    setSelectedIssueIds(new Set());
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
          {/* Review tabs */}
          <div className="app__review-tabs">
            <button
              type="button"
              className={`app__review-tab ${activeTab === 'review' ? 'app__review-tab--active' : ''}`}
              onClick={() => setActiveTab('review')}
            >
              Design Review
            </button>
            <button
              type="button"
              className={`app__review-tab ${activeTab === 'comments' ? 'app__review-tab--active' : ''}`}
              onClick={() => setActiveTab('comments')}
              disabled={issues.length === 0}
              title={issues.length === 0 ? 'Run a review to see comments' : ''}
            >
              Comment List
              {issues.length > 0 && (
                <span className="app__review-tab-count">{issues.length}</span>
              )}
            </button>
          </div>

          {/* Tab content */}
          {activeTab === 'review' ? (
            <ReviewResults
              sections={sections}
              isStreaming={isStreaming}
              isComplete={isComplete}
              error={reviewError}
              onRetry={handleReview}
            />
          ) : (
            <CommentList
              issues={issues}
              selectedIds={selectedIssueIds}
              onToggleSelect={handleToggleIssue}
              onGeneratePdf={handleGeneratePdf}
              isGenerating={isGeneratingPdf}
            />
          )}

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
