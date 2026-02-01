import { useState, useRef, useEffect } from 'react';
import { Card, Checkbox, Button, Typography, Empty, Tag, Affix, Row, Col, Switch } from 'antd';
import { FilePdfOutlined, CheckOutlined } from '@ant-design/icons';
import type { ReviewIssue } from '../../types/review';

const { Text, Title } = Typography;

export interface EditedIssueData {
  title: string;
  description: string;
  allPages: boolean;
}

interface CommentListProps {
  issues: ReviewIssue[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onGeneratePdf?: (editedData: Map<string, EditedIssueData>) => void;
  isGenerating?: boolean;
}

const variantConfig = {
  error: { color: '#ff4d4f', bgColor: '#fff2f0' },
  warning: { color: '#faad14', bgColor: '#fffbe6' },
};

// Inline editable text component
function EditableText({
  value,
  onChange,
  isTitle = false,
}: {
  value: string;
  onChange: (newValue: string) => void;
  isTitle?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      // Position cursor at end
      inputRef.current.setSelectionRange(editValue.length, editValue.length);
    }
  }, [isEditing]);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
    setEditValue(value);
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (editValue.trim() !== value) {
      onChange(editValue.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setEditValue(value);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <textarea
        ref={inputRef}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          border: '1px solid #1677ff',
          borderRadius: 4,
          padding: '4px 8px',
          fontSize: isTitle ? 14 : 12,
          fontWeight: isTitle ? 500 : 400,
          color: 'rgba(0, 0, 0, 0.85)',
          resize: 'none',
          minHeight: isTitle ? 28 : 60,
          fontFamily: 'inherit',
          outline: 'none',
        }}
        rows={isTitle ? 1 : 3}
      />
    );
  }

  return (
    <div
      onClick={handleClick}
      style={{
        cursor: 'text',
        padding: '4px 8px',
        margin: '-4px -8px',
        borderRadius: 4,
        transition: 'background 0.2s',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
    >
      {isTitle ? (
        <div style={{ fontWeight: 500, color: 'rgba(0, 0, 0, 0.85)', paddingRight: 20 }}>
          {value}
        </div>
      ) : (
        <Text style={{ fontSize: 12, color: 'rgba(0, 0, 0, 0.65)' }}>
          {value}
        </Text>
      )}
    </div>
  );
}

export function CommentList({
  issues,
  selectedIds,
  onToggleSelect,
  onGeneratePdf,
  isGenerating = false,
}: CommentListProps) {
  // Track edited titles and descriptions
  const [editedData, setEditedData] = useState<Map<string, { title?: string; description?: string }>>(new Map());
  // Track "all pages" toggle state (default true)
  const [allPagesMap, setAllPagesMap] = useState<Map<string, boolean>>(new Map());

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

  const handleEditTitle = (issueId: string, newTitle: string) => {
    setEditedData(prev => {
      const next = new Map(prev);
      const existing = next.get(issueId) || {};
      next.set(issueId, { ...existing, title: newTitle });
      return next;
    });
  };

  const handleEditDescription = (issueId: string, newDescription: string) => {
    setEditedData(prev => {
      const next = new Map(prev);
      const existing = next.get(issueId) || {};
      next.set(issueId, { ...existing, description: newDescription });
      return next;
    });
  };

  const handleToggleAllPages = (issueId: string, checked: boolean) => {
    setAllPagesMap(prev => {
      const next = new Map(prev);
      next.set(issueId, checked);
      return next;
    });
  };

  const getEditedIssueData = (): Map<string, EditedIssueData> => {
    const result = new Map<string, EditedIssueData>();
    issues.forEach(issue => {
      const edited = editedData.get(issue.id);
      result.set(issue.id, {
        title: edited?.title ?? issue.title,
        description: edited?.description ?? issue.description,
        allPages: allPagesMap.get(issue.id) ?? true,
      });
    });
    return result;
  };

  const handleGeneratePdf = () => {
    if (onGeneratePdf) {
      onGeneratePdf(getEditedIssueData());
    }
  };

  // Render individual issue card as grid item
  const renderIssueCard = (issue: ReviewIssue, variant: 'error' | 'warning') => {
    const config = variantConfig[variant];
    const isSelected = selectedIds.has(issue.id);
    const edited = editedData.get(issue.id);
    const currentTitle = edited?.title ?? issue.title;
    const currentDescription = edited?.description ?? issue.description;
    const allPages = allPagesMap.get(issue.id) ?? true;
    const hasMultiplePages = issue.pages.length > 1;

    return (
      <Col xs={24} sm={12} lg={6} key={issue.id}>
        <Card
          size="small"
          hoverable
          onClick={() => onToggleSelect(issue.id)}
          style={{
            marginBottom: 12,
            borderTop: `3px solid ${config.color}`,
            cursor: 'pointer',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
          }}
          styles={{ body: { padding: 20, display: 'flex', flexDirection: 'column', flex: 1 } }}
        >
          <div style={{ position: 'relative', flex: 1 }}>
            <div style={{
              position: 'absolute',
              top: -4,
              right: -4,
              width: 20,
              height: 20,
              borderRadius: 4,
              background: isSelected ? '#1677ff' : '#f0f0f0',
              border: isSelected ? 'none' : '1px solid #d9d9d9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {isSelected && <CheckOutlined style={{ color: '#fff', fontSize: 12 }} />}
            </div>
            <Tag style={{ marginBottom: 16 }}>
              {issue.pages.length === 1
                ? `p. ${issue.pages[0]}`
                : `pp. ${issue.pages.join(', ')}`}
            </Tag>
            <div style={{ marginBottom: 8 }}>
              <EditableText
                value={currentTitle}
                onChange={(newTitle) => handleEditTitle(issue.id, newTitle)}
                isTitle
              />
            </div>
            <EditableText
              value={currentDescription}
              onChange={(newDesc) => handleEditDescription(issue.id, newDesc)}
            />
          </div>
          {hasMultiplePages && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                marginTop: 16,
                paddingTop: 12,
                borderTop: '1px solid #f0f0f0',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <Text style={{ fontSize: 12, color: 'rgba(0, 0, 0, 0.45)', marginRight: 8 }}>
                All pages
              </Text>
              <Switch
                size="small"
                checked={allPages}
                onChange={(checked) => handleToggleAllPages(issue.id, checked)}
              />
            </div>
          )}
        </Card>
      </Col>
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

    const handleSectionToggle = (e: React.MouseEvent) => {
      e.stopPropagation();
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
      <div style={{ marginBottom: 24 }}>
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
            onClick={handleSectionToggle}
          />
          <Text strong style={{ marginLeft: 8, flex: 1, color: 'rgba(0, 0, 0, 0.85)' }}>{title}</Text>
          <Text style={{ color: 'rgba(0, 0, 0, 0.65)' }}>{selectedInSection}/{sectionIssues.length}</Text>
        </div>
        <Row gutter={[12, 12]}>
          {sectionIssues.map(issue => renderIssueCard(issue, variant))}
        </Row>
      </div>
    );
  };

  const totalSelected = selectedIds.size;

  return (
    <div style={{ padding: 16, paddingBottom: 80 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0, color: 'rgba(0, 0, 0, 0.85)' }}>Comments for PDF</Title>
        <Text style={{ color: 'rgba(0, 0, 0, 0.65)' }}>{totalSelected} of {issues.length} selected</Text>
      </div>

      {renderSection('Needs Attention', needsAttention, 'error')}
      {renderSection('Suggestions', suggestions, 'warning')}

      {onGeneratePdf && (
        <Affix offsetBottom={0}>
          <div style={{
            background: '#fff',
            padding: 16,
            borderTop: '1px solid #e8e8e8',
            display: 'flex',
            justifyContent: 'flex-end',
          }}>
            <Button
              type="primary"
              icon={<FilePdfOutlined />}
              onClick={handleGeneratePdf}
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
