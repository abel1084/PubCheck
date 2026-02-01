import { useState } from 'react';
import { Card, Checkbox, Button, Typography, Empty, Tag, Affix } from 'antd';
import { FilePdfOutlined, CaretRightOutlined } from '@ant-design/icons';
import type { ReviewIssue } from '../../types/review';

const { Text, Title } = Typography;

interface CommentListProps {
  issues: ReviewIssue[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onGeneratePdf?: () => void;
  isGenerating?: boolean;
}

const variantConfig = {
  error: { color: '#ff4d4f', bgColor: '#fff2f0' },
  warning: { color: '#faad14', bgColor: '#fffbe6' },
};

export function CommentList({
  issues,
  selectedIds,
  onToggleSelect,
  onGeneratePdf,
  isGenerating = false,
}: CommentListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

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

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Render individual issue card (matching ReviewSection style)
  const renderIssueCard = (issue: ReviewIssue, variant: 'error' | 'warning') => {
    const config = variantConfig[variant];
    const isExpanded = expandedIds.has(issue.id);

    return (
      <Card
        key={issue.id}
        size="small"
        style={{ marginBottom: 12, borderLeft: `3px solid ${config.color}` }}
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Checkbox
              checked={selectedIds.has(issue.id)}
              onChange={() => onToggleSelect(issue.id)}
              onClick={e => e.stopPropagation()}
              style={{ marginRight: 8 }}
            />
            <div
              style={{ display: 'flex', alignItems: 'center', flex: 1, cursor: 'pointer' }}
              onClick={() => toggleExpanded(issue.id)}
            >
              <CaretRightOutlined
                style={{
                  marginRight: 8,
                  transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s',
                }}
              />
              <span style={{ flex: 1 }}>{issue.title}</span>
              <Tag>
                {issue.pages.length === 1
                  ? `p. ${issue.pages[0]}`
                  : `pp. ${issue.pages.join(', ')}`}
              </Tag>
            </div>
          </div>
        }
      >
        {isExpanded && (
          <Text type="secondary">{issue.description}</Text>
        )}
      </Card>
    );
  };

  // Create section with checkbox header
  const renderSection = (
    title: string,
    sectionIssues: ReviewIssue[],
    variant: 'error' | 'warning'
  ) => {
    if (sectionIssues.length === 0) return null;

    const config = variantConfig[variant];
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

    return (
      <div style={{ marginBottom: 16 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          background: config.bgColor,
          borderLeft: `3px solid ${config.color}`,
          marginBottom: 12,
          borderRadius: 4,
        }}>
          <Checkbox
            checked={allSelected}
            indeterminate={someSelected}
            onChange={handleSectionToggle}
          />
          <Text strong style={{ marginLeft: 8, flex: 1 }}>{title}</Text>
          <Text type="secondary">{selectedInSection}/{sectionIssues.length}</Text>
        </div>
        {sectionIssues.map(issue => renderIssueCard(issue, variant))}
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
