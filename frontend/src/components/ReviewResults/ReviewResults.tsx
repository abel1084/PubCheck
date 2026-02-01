import { Alert, Button, Spin, Typography, Space, Result, Row, Col } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import type { AIReviewSections } from '../../types/review';
import { ReviewSection } from './ReviewSection';

const { Title, Text } = Typography;

interface ReviewResultsProps {
  sections: AIReviewSections;
  isStreaming: boolean;
  isComplete: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function ReviewResults({
  sections,
  isStreaming,
  isComplete,
  error,
  onRetry,
}: ReviewResultsProps) {
  // Error state
  if (error) {
    return (
      <Alert
        message="Review Failed"
        description={error}
        type="error"
        showIcon
        action={
          onRetry && (
            <Button size="small" onClick={onRetry}>
              Try Again
            </Button>
          )
        }
        style={{ margin: 16 }}
      />
    );
  }

  // Empty state before review
  const hasContent = Object.values(sections).some(s => s.length > 0);
  if (!hasContent && !isStreaming) {
    return (
      <Result
        status="info"
        title="No Review Yet"
        subTitle="Click 'Review' to analyze the document for design compliance."
        style={{ padding: 40 }}
      />
    );
  }

  // Loading state
  if (isStreaming && !hasContent) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin size="large" />
        <Text style={{ display: 'block', marginTop: 16 }}>
          Analyzing document...
        </Text>
      </div>
    );
  }

  return (
    <div style={{ padding: 16, maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Design Review</Title>
        <Space>
          {isComplete && <Text type="success">Review Complete</Text>}
          {isStreaming && <Text type="secondary"><SyncOutlined spin /> Reviewing...</Text>}
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <ReviewSection
            title="Overview"
            content={sections.overview}
            variant="overview"
            isStreaming={isStreaming && !sections.needsAttention}
          />
        </Col>
        <Col xs={24} lg={12}>
          <ReviewSection
            title="Looking Good"
            content={sections.lookingGood}
            variant="good"
            isStreaming={isStreaming && !!sections.needsAttention && !sections.suggestions}
          />
        </Col>
        <Col xs={24} lg={12}>
          <ReviewSection
            title="Needs Attention"
            content={sections.needsAttention}
            variant="attention"
            isStreaming={isStreaming && !!sections.overview && !sections.lookingGood}
          />
        </Col>
        <Col xs={24} lg={12}>
          <ReviewSection
            title="Suggestions"
            content={sections.suggestions}
            variant="suggestions"
            isStreaming={isStreaming && !!sections.lookingGood}
          />
        </Col>
      </Row>

      {onRetry && isComplete && (
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Button onClick={onRetry} icon={<SyncOutlined />}>
            Re-review
          </Button>
        </div>
      )}
    </div>
  );
}

export { ReviewSection } from './ReviewSection';
