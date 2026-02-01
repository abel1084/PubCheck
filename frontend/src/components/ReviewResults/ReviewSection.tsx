import { useState } from 'react';
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
 * Collapsible with toggle button in title bar.
 */
export function ReviewSection({
  title,
  content,
  variant,
  isStreaming = false,
}: ReviewSectionProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Don't render empty sections (unless streaming and might fill)
  if (!content && !isStreaming) {
    return null;
  }

  const toggleCollapse = () => {
    setIsCollapsed((prev) => !prev);
  };

  return (
    <section className={`review-section review-section--${variant}`}>
      <header className="review-section__header">
        <h3 className="review-section__title">{title}</h3>
        <button
          type="button"
          className={`review-section__toggle ${isCollapsed ? 'review-section__toggle--collapsed' : ''}`}
          onClick={toggleCollapse}
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? 'Expand section' : 'Collapse section'}
        >
          <svg
            className="review-section__toggle-icon"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z" />
          </svg>
        </button>
      </header>
      {!isCollapsed && (
        <div className="review-section__content">
          {content ? (
            <ReactMarkdown>{content}</ReactMarkdown>
          ) : (
            <span className="review-section__placeholder">
              {isStreaming ? 'Analyzing...' : 'No content'}
            </span>
          )}
        </div>
      )}
      {!isCollapsed && isStreaming && content && (
        <div className="review-section__streaming-indicator">
          <span className="review-section__cursor"></span>
        </div>
      )}
    </section>
  );
}
