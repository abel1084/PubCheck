import { useState, useEffect, useRef, useCallback } from 'react';
import { Layout, Button, Select, Tabs, Typography, Space, Spin, type TabsProps } from 'antd';
import { SettingOutlined, SyncOutlined, PlusOutlined, LogoutOutlined } from '@ant-design/icons';
import { Login } from './components/Login';
import { DropZone } from './components/DropZone';
import { DataTabs } from './components/DataTabs';
import { ReviewResults } from './components/ReviewResults/ReviewResults';
import { CommentList, type EditedIssueData } from './components/CommentList/CommentList';
import { Settings } from './components/Settings/Settings';
import { useExtraction } from './hooks/useExtraction';
import { useAIReview } from './hooks/useAIReview';
import { useAntdApp } from './hooks/useAntdApp';
import type { DocumentType, Confidence } from './types/extraction';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const DOCUMENT_TYPES: DocumentType[] = [
  'Factsheet',
  'Policy Brief',
  'Working Paper',
  'Technical Report',
  'Publication',
];

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

  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('digital');
  const [activeTab, setActiveTab] = useState<ReviewTab>('review');
  const [selectedIssueIds, setSelectedIssueIds] = useState<Set<string>>(new Set());
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const uploadedFileRef = useRef<File | null>(null);

  // Check auth on mount
  useEffect(() => {
    fetch('/api/auth/check', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setIsAuthenticated(data.authenticated))
      .catch(() => setIsAuthenticated(false));
  }, []);

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    setIsAuthenticated(false);
  };

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

  const handleGeneratePdf = useCallback(async (editedData: Map<string, EditedIssueData>) => {
    if (!uploadedFileRef.current || selectedIssueIds.size === 0) return;

    setIsGeneratingPdf(true);
    try {
      const selectedIssues = issues.filter(i => selectedIssueIds.has(i.id));
      const annotations = selectedIssues.flatMap(issue => {
        const edited = editedData.get(issue.id);
        const title = edited?.title ?? issue.title;
        const description = edited?.description ?? issue.description;
        const allPages = edited?.allPages ?? true;

        // If allPages is false, only use the first page
        const pagesToAnnotate = allPages ? issue.pages : [issue.pages[0]];

        return pagesToAnnotate.map(page => ({
          page,
          x: null,
          y: null,
          message: `${title}\n\n${description}`,
          severity: issue.category === 'needs_attention' ? 'error' : 'warning',
        }));
      });

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

  // Loading auth state
  if (isAuthenticated === null) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Login screen
  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  // Upload view
  if (!result) {
    return (
      <Layout style={{ minHeight: '100vh', maxWidth: 1920, margin: '0 auto', background: '#fff' }}>
        {showSettings && <Settings onClose={() => setShowSettings(false)} />}
        <Content style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Title level={2} style={{ margin: 0 }}>PubCheck</Title>
          </div>
          <DropZone onFileAccepted={handleUpload} isProcessing={isUploading} error={error} />
          <Space style={{ marginTop: 16 }}>
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => setShowSettings(true)}
            >
              Settings
            </Button>
            <Button
              type="link"
              icon={<LogoutOutlined />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </Space>
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

  // Truncate filename for header display
  const truncatedFilename = result.filename.length > 30
    ? result.filename.substring(0, 27) + '...'
    : result.filename;

  return (
    <Layout style={{ minHeight: '100vh', maxWidth: 1920, margin: '0 auto', background: '#fff' }}>
      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
      <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #e8e8e8' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>PubCheck</Title>
          <Text type="secondary">
            {truncatedFilename} — {result.extraction.metadata.page_count} pages
          </Text>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleNewDocument}
              style={{ background: '#52c41a', borderColor: '#52c41a' }}
            />
            <Button
              type="primary"
              icon={<SettingOutlined />}
              onClick={() => setShowSettings(true)}
              style={{ background: '#1677ff', borderColor: '#1677ff' }}
            />
            <Button
              icon={<LogoutOutlined />}
              onClick={handleLogout}
            />
          </Space>
        </div>
      </Header>

      <Content style={{ padding: 16, overflow: 'auto', background: '#fff' }}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as ReviewTab)}
          items={tabItems}
          tabBarExtraContent={
            <Space>
              <Select
                value={documentType || result.documentType}
                onChange={setDocumentType}
                disabled={isStreaming}
                style={{ width: 140 }}
                options={DOCUMENT_TYPES.map(type => ({ value: type, label: type }))}
              />
              <Select
                value={outputFormat}
                onChange={setOutputFormat}
                disabled={isStreaming}
                style={{ width: 140 }}
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
          }
        />
        <DataTabs extraction={result.extraction} defaultCollapsed={true} />
      </Content>
    </Layout>
  );
}

export default App;
