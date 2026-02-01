import ReactMarkdown from 'react-markdown';

interface ReviewSectionProps {
  title: string;
  content: string;
  variant: 'overview' | 'attention' | 'good' | 'suggestions';
  isStreaming?: boolean;
}

/**
 * Individual review section card.
 * Renders markdown content with variant-specific styling.
 */
export function ReviewSection({
  title,
  content,
  variant,
  isStreaming = false,
}: ReviewSectionProps) {
  // Don't render empty sections (unless streaming and might fill)
  if (!content && !isStreaming) {
    return null;
  }

  return (
    <section className={`review-section review-section--${variant}`}>
      <h3 className="review-section__title">{title}</h3>
      <div className="review-section__content">
        {content ? (
          <ReactMarkdown>{content}</ReactMarkdown>
        ) : (
          <span className="review-section__placeholder">
            {isStreaming ? 'Analyzing...' : 'No content'}
          </span>
        )}
      </div>
      {isStreaming && content && (
        <div className="review-section__streaming-indicator">
          <span className="review-section__cursor"></span>
        </div>
      )}
    </section>
  );
}
