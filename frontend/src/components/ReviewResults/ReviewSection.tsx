import { useState } from 'react';
import { Card, Spin, Tag, Typography } from 'antd';
import { CaretRightOutlined, CheckCircleOutlined, ExclamationCircleOutlined, BulbOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

interface ReviewSectionProps {
  title: string;
  content: string;
  variant: 'overview' | 'attention' | 'good' | 'suggestions';
  isStreaming?: boolean;
}

const variantConfig = {
  overview: {
    color: '#1890ff',
    tagColor: 'processing' as const,
    icon: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
  },
  attention: {
    color: '#ff4d4f',
    tagColor: 'error' as const,
    icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
  },
  good: {
    color: '#52c41a',
    tagColor: 'success' as const,
    icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  },
  suggestions: {
    color: '#faad14',
    tagColor: 'warning' as const,
    icon: <BulbOutlined style={{ color: '#faad14' }} />,
  },
};

function parseContentToItems(content: string): string[] {
  // Split by markdown list items (-, *, or numbered)
  const lines = content.split('\n');
  const items: string[] = [];
  let currentItem = '';

  for (const line of lines) {
    const trimmed = line.trim();
    // Check if it's a list item start
    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      if (currentItem) {
        items.push(currentItem.trim());
      }
      // Remove the bullet/number prefix
      currentItem = trimmed.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '');
    } else if (trimmed && currentItem) {
      // Continuation of previous item
      currentItem += ' ' + trimmed;
    } else if (trimmed && !currentItem) {
      // Standalone paragraph
      items.push(trimmed);
    }
  }
  if (currentItem) {
    items.push(currentItem.trim());
  }

  return items.filter(item => item.length > 0);
}

export function ReviewSection({ title, content, variant, isStreaming }: ReviewSectionProps) {
  const [collapsed, setCollapsed] = useState(false);
  const config = variantConfig[variant];

  if (!content && !isStreaming) {
    return null;
  }

  const items = content ? parseContentToItems(content) : [];

  return (
    <Card
      size="small"
      style={{
        marginBottom: 0,
        borderLeft: `3px solid ${config.color}`,
        height: '100%',
      }}
      styles={{
        body: {
          padding: collapsed ? 0 : 12,
          maxHeight: collapsed ? 0 : 400,
          overflow: 'auto',
        }
      }}
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
          {items.length > 0 && (
            <div>
              {items.map((item, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    padding: '10px 0',
                    borderBottom: index < items.length - 1 ? '1px solid #f0f0f0' : 'none',
                  }}
                >
                  <span style={{ flexShrink: 0, marginTop: 2 }}>{config.icon}</span>
                  <Paragraph style={{ margin: 0, flex: 1 }}>
                    {item}
                  </Paragraph>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Card>
  );
}
