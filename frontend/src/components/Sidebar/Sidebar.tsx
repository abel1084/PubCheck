import { Button, Select, Tag, Typography, Space, Divider } from 'antd';
import { FileOutlined, ReloadOutlined } from '@ant-design/icons';
import type { DocumentMetadata, DocumentType, Confidence } from '../../types/extraction';

const { Text, Title } = Typography;

interface SidebarProps {
  filename: string;
  documentType: DocumentType;
  confidence: Confidence;
  metadata: DocumentMetadata;
  onDocumentTypeChange: (type: DocumentType) => void;
  onNewDocument: () => void;
}

const DOCUMENT_TYPES: DocumentType[] = [
  'Factsheet',
  'Policy Brief',
  'Working Paper',
  'Technical Report',
  'Publication',
];

const confidenceColors: Record<Confidence, string> = {
  high: 'success',
  medium: 'warning',
  low: 'error',
};

export function Sidebar({
  filename,
  documentType,
  confidence,
  metadata,
  onDocumentTypeChange,
  onNewDocument,
}: SidebarProps) {
  return (
    <aside style={{
      width: 280,
      padding: 16,
      background: '#fafafa',
      borderRight: '1px solid #f0f0f0',
      height: '100%',
      overflow: 'auto',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>Document Info</Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={onNewDocument}
          size="small"
        >
          New
        </Button>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
            Filename
          </Text>
          <Text strong ellipsis style={{ display: 'block' }}>
            <FileOutlined style={{ marginRight: 8 }} />
            {filename}
          </Text>
        </div>

        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
            Pages
          </Text>
          <Text>{metadata.page_count}</Text>
        </div>

        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
            Document Type
          </Text>
          <Select
            value={documentType}
            onChange={onDocumentTypeChange}
            style={{ width: '100%' }}
            options={DOCUMENT_TYPES.map(type => ({ value: type, label: type }))}
          />
          <div style={{ marginTop: 8 }}>
            <Tag color={confidenceColors[confidence]}>
              {confidence} confidence
            </Tag>
          </div>
        </div>

        {metadata.title && (
          <div>
            <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
              Title
            </Text>
            <Text style={{ display: 'block' }}>{metadata.title}</Text>
          </div>
        )}
      </Space>
    </aside>
  );
}
