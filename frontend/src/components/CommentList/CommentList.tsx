import { useState } from 'react';
import { Collapse, Checkbox, Button, Typography, Empty, Tag, Affix, type CollapseProps } from 'antd';
import { FilePdfOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';
import type { ReviewIssue } from '../../types/review';

const { Text, Title } = Typography;

interface CommentListProps {
  issues: ReviewIssue[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onGeneratePdf?: () => void;
  isGenerating?: boolean;
}

export function CommentList({
  issues,
  selectedIds,
  onToggleSelect,
  onGeneratePdf,
  isGenerating = false,
}: CommentListProps) {
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  // Group issues by category
  const needsAttention = issues.filter(i => i.category === 'needs_attention');
  const suggestions = issues.filter(i => i.category === 'suggestion');

  if (issues.length === 0) {
    return (
      <Empty
        description="No issues found. Run a review to see selectable comments."
        style={{ padding: 40 }}
      />
    );
  }

  // Create section with checkbox header
  const renderSection = (
    title: string,
    sectionIssues: ReviewIssue[],
    variant: 'error' | 'warning'
  ) => {
    if (sectionIssues.length === 0) return null;

    const selectedInSection = sectionIssues.filter(i => selectedIds.has(i.id)).length;
    const allSelected = selectedInSection === sectionIssues.length;
    const someSelected = selectedInSection > 0 && !allSelected;

    const handleSectionToggle = () => {
      if (allSelected) {
        sectionIssues.forEach(i => {
          if (selectedIds.has(i.id)) onToggleSelect(i.id);
        });
      } else {
        sectionIssues.forEach(i => {
          if (!selectedIds.has(i.id)) onToggleSelect(i.id);
        });
      }
    };

    const collapseItems: CollapseProps['items'] = sectionIssues.map(issue => ({
      key: issue.id,
      label: (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }} onClick={e => e.stopPropagation()}>
          <Checkbox
            checked={selectedIds.has(issue.id)}
            onChange={() => onToggleSelect(issue.id)}
          />
          <Text strong style={{ flex: 1 }}>{issue.title}</Text>
          <Tag>
            {issue.pages.length === 1
              ? `p. ${issue.pages[0]}`
              : `pp. ${issue.pages.join(', ')}`}
          </Tag>
        </div>
      ),
      children: <Text type="secondary">{issue.description}</Text>,
    }));

    return (
      <div style={{ marginBottom: 16 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          background: variant === 'error' ? '#fff2f0' : '#fffbe6',
          borderLeft: `3px solid ${variant === 'error' ? '#ff4d4f' : '#faad14'}`,
          marginBottom: 8,
        }}>
          <Checkbox
            checked={allSelected}
            indeterminate={someSelected}
            onChange={handleSectionToggle}
          />
          <Text strong style={{ marginLeft: 8, flex: 1 }}>{title}</Text>
          <Text type="secondary">{selectedInSection}/{sectionIssues.length}</Text>
        </div>
        <Collapse
          activeKey={expandedIds}
          onChange={(keys) => setExpandedIds(keys as string[])}
          items={collapseItems}
          ghost
          expandIcon={({ isActive }) => isActive ? <UpOutlined /> : <DownOutlined />}
        />
      </div>
    );
  };

  const totalSelected = selectedIds.size;

  return (
    <div style={{ padding: 16, paddingBottom: 80 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0 }}>Comments for PDF</Title>
        <Text type="secondary">{totalSelected} of {issues.length} selected</Text>
      </div>

      {renderSection('Needs Attention', needsAttention, 'error')}
      {renderSection('Suggestions', suggestions, 'warning')}

      {onGeneratePdf && (
        <Affix offsetBottom={0}>
          <div style={{
            background: '#fff',
            padding: 16,
            borderTop: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'flex-end',
          }}>
            <Button
              type="primary"
              icon={<FilePdfOutlined />}
              onClick={onGeneratePdf}
              disabled={totalSelected === 0}
              loading={isGenerating}
            >
              Generate PDF ({totalSelected} comments)
            </Button>
          </div>
        </Affix>
      )}
    </div>
  );
}
