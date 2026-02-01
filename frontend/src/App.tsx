import { useState, useEffect, useRef, useCallback } from 'react';
import { Layout, Button, Select, Tabs, Typography, Space, type TabsProps } from 'antd';
import { SettingOutlined, SyncOutlined } from '@ant-design/icons';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { Sidebar } from './components/Sidebar';
import { ReviewResults } from './components/ReviewResults/ReviewResults';
import { CommentList } from './components/CommentList/CommentList';
import { Settings } from './components/Settings/Settings';
import { useExtraction } from './hooks/useExtraction';
import { useAIReview } from './hooks/useAIReview';
import { useAntdApp } from './hooks/useAntdApp';
import type { DocumentType, Confidence } from './types/extraction';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

type ReviewTab = 'review' | 'comments';
type OutputFormat = 'print' | 'digital' | 'both';

const DOCUMENT_TYPE_MAP: Record<DocumentType, string> = {
  'Factsheet': 'factsheet',
  'Policy Brief': 'policy-brief',
  'Working Paper': 'working-paper',
  'Technical Report': 'issue-note',
  'Publication': 'publication',
};

const CONFIDENCE_MAP: Record<Confidence, number> = {
  'high': 0.95,
  'medium': 0.75,
  'low': 0.5,
};

function App() {
  const { message } = useAntdApp();
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
  const [showSettings, setShowSettings] = useState(false);
  const uploadedFileRef = useRef<File | null>(null);

  const handleToggleIssue = useCallback((id: string) => {
    setSelectedIssueIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  useEffect(() => {
    if (issues.length > 0) {
      setSelectedIssueIds(new Set(issues.map(i => i.id)));
    }
  }, [issues]);

  const handleGeneratePdf = useCallback(async () => {
    if (!uploadedFileRef.current || selectedIssueIds.size === 0) return;

    setIsGeneratingPdf(true);
    try {
      const selectedIssues = issues.filter(i => selectedIssueIds.has(i.id));
      const annotations = selectedIssues.flatMap(issue =>
        issue.pages.map(page => ({
          page,
          x: null,
          y: null,
          message: `${issue.title}\n\n${issue.description}`,
          severity: issue.category === 'needs_attention' ? 'error' : 'warning',
        }))
      );

      const formData = new FormData();
      formData.append('pdf', uploadedFileRef.current);
      formData.append('issues', JSON.stringify({ issues: annotations }));

      const response = await fetch('/api/output/annotate', { method: 'POST', body: formData });
      if (!response.ok) throw new Error(await response.text() || 'Failed to generate annotated PDF');

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition?.match(/filename="(.+)"/)?.[1] || 'annotated.pdf';

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      message.success('Annotated PDF downloaded');
    } catch (e) {
      message.error(`Failed to generate PDF: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setIsGeneratingPdf(false);
    }
  }, [issues, selectedIssueIds, message]);

  useEffect(() => {
    if (result && documentType === null) {
      setDocumentType(result.documentType);
    }
  }, [result, documentType]);

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

  const handleReview = () => {
    if (result && documentType && uploadedFileRef.current) {
      startReview(
        uploadedFileRef.current,
        result.extraction,
        DOCUMENT_TYPE_MAP[documentType],
        CONFIDENCE_MAP[result.confidence],
        outputFormat
      );
    }
  };

  // Upload view
  if (!result) {
    return (
      <Layout style={{ minHeight: '100vh', maxWidth: 1920, margin: '0 auto' }}>
        {showSettings && <Settings onClose={() => setShowSettings(false)} />}
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '100%' }}>
            <div>
              <Title level={4} style={{ margin: 0 }}>PubCheck</Title>
              <Text type="secondary">UNEP PDF Design Compliance Checker</Text>
            </div>
            <Button icon={<SettingOutlined />} onClick={() => setShowSettings(true)}>
              Settings
            </Button>
          </div>
        </Header>
        <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <DropZone onFileAccepted={handleUpload} isProcessing={isUploading} error={error} />
        </Content>
      </Layout>
    );
  }

  // Results view
  const tabItems: TabsProps['items'] = [
    {
      key: 'review',
      label: 'Design Review',
      children: (
        <ReviewResults
          sections={sections}
          isStreaming={isStreaming}
          isComplete={isComplete}
          error={reviewError}
          onRetry={handleReview}
        />
      ),
    },
    {
      key: 'comments',
      label: (
        <span>
          Comment List
          {issues.length > 0 && (
            <span style={{
              marginLeft: 8,
              padding: '0 8px',
              background: '#f0f0f0',
              borderRadius: 10,
              fontSize: 12,
            }}>
              {issues.length}
            </span>
          )}
        </span>
      ),
      disabled: issues.length === 0,
      children: (
        <CommentList
          issues={issues}
          selectedIds={selectedIssueIds}
          onToggleSelect={handleToggleIssue}
          onGeneratePdf={handleGeneratePdf}
          isGenerating={isGeneratingPdf}
        />
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', maxWidth: 1920, margin: '0 auto' }}>
      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
      <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>PubCheck</Title>
          <Space>
            <Button icon={<SettingOutlined />} onClick={() => setShowSettings(true)}>
              Settings
            </Button>
            <Select
              value={outputFormat}
              onChange={setOutputFormat}
              disabled={isStreaming}
              style={{ width: 150 }}
              options={[
                { value: 'digital', label: 'Digital (72 DPI)' },
                { value: 'print', label: 'Print (300 DPI)' },
                { value: 'both', label: 'Both (150 DPI)' },
              ]}
            />
            <Button
              type="primary"
              icon={isStreaming ? <SyncOutlined spin /> : undefined}
              onClick={handleReview}
              disabled={!result || isStreaming}
              loading={isStreaming}
            >
              {isStreaming ? 'Reviewing...' : 'Review'}
            </Button>
          </Space>
        </div>
      </Header>

      <Layout>
        <Sider width={280} style={{ background: '#fafafa', borderRight: '1px solid #f0f0f0' }}>
          <Sidebar
            filename={result.filename}
            documentType={documentType || result.documentType}
            confidence={result.confidence}
            metadata={result.extraction.metadata}
            onDocumentTypeChange={setDocumentType}
            onNewDocument={handleNewDocument}
          />
        </Sider>
        <Content style={{ padding: 16, overflow: 'auto' }}>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as ReviewTab)}
            items={tabItems}
          />
          <DataTabs extraction={result.extraction} defaultCollapsed={true} />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
