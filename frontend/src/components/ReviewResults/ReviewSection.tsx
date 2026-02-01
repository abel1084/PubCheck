import { useState } from 'react';
import { Card, Spin, Tag } from 'antd';
import { CaretRightOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';

interface ReviewSectionProps {
  title: string;
  content: string;
  variant: 'overview' | 'attention' | 'good' | 'suggestions';
  isStreaming?: boolean;
}

const variantConfig = {
  overview: { color: '#1890ff', tagColor: 'processing' as const },
  attention: { color: '#ff4d4f', tagColor: 'error' as const },
  good: { color: '#52c41a', tagColor: 'success' as const },
  suggestions: { color: '#faad14', tagColor: 'warning' as const },
};

export function ReviewSection({ title, content, variant, isStreaming }: ReviewSectionProps) {
  const [collapsed, setCollapsed] = useState(false);
  const config = variantConfig[variant];

  if (!content && !isStreaming) {
    return null;
  }

  return (
    <Card
      size="small"
      style={{ marginBottom: 12, borderLeft: `3px solid ${config.color}` }}
      title={
        <div
          style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => setCollapsed(!collapsed)}
        >
          <CaretRightOutlined
            style={{
              marginRight: 8,
              transform: collapsed ? 'rotate(0deg)' : 'rotate(90deg)',
              transition: 'transform 0.2s',
            }}
          />
          <span>{title}</span>
          {isStreaming && (
            <Tag color={config.tagColor} style={{ marginLeft: 8 }}>
              Streaming...
            </Tag>
          )}
        </div>
      }
    >
      {!collapsed && (
        <>
          {isStreaming && !content && (
            <div style={{ textAlign: 'center', padding: 16 }}>
              <Spin size="small" />
            </div>
          )}
          {content && (
            <div className="markdown-content">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
