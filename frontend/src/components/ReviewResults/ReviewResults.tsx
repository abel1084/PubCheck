import type { AIReviewSections } from '../../types/review';
import { ReviewSection } from './ReviewSection';
import './ReviewResults.css';

interface ReviewResultsProps {
  sections: AIReviewSections;
  isStreaming: boolean;
  isComplete: boolean;
  error: string | null;
  onRetry?: () => void;
}

/**
 * Main review results container.
 * Displays AI review organized by priority sections.
 */
export function ReviewResults({
  sections,
  isStreaming,
  isComplete,
  error,
  onRetry,
}: ReviewResultsProps) {
  // Show error state
  if (error) {
    return (
      <div className="review-results review-results--error">
        <div className="review-results__error">
          <h3>Review Failed</h3>
          <p>{error}</p>
          {onRetry && (
            <button
              type="button"
              className="review-results__retry-button"
              onClick={onRetry}
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  // Show empty state before review starts
  const hasContent = Object.values(sections).some(s => s.length > 0);
  if (!hasContent && !isStreaming) {
    return (
      <div className="review-results review-results--empty">
        <p className="review-results__empty-text">
          Click "Review" to analyze the document for design compliance.
        </p>
      </div>
    );
  }

  // Show loading state when streaming but no content yet
  if (isStreaming && !hasContent) {
    return (
      <div className="review-results review-results--loading">
        <div className="review-results__loading-spinner"></div>
        <p className="review-results__loading-text">
          Analyzing document...
        </p>
      </div>
    );
  }

  return (
    <div className="review-results">
      <div className="review-results__header">
        <h2 className="review-results__title">Design Review</h2>
        {isComplete && (
          <span className="review-results__status review-results__status--complete">
            Review Complete
          </span>
        )}
        {isStreaming && (
          <span className="review-results__status review-results__status--streaming">
            Reviewing...
          </span>
        )}
      </div>

      <div className="review-results__sections">
        <ReviewSection
          title="Overview"
          content={sections.overview}
          variant="overview"
          isStreaming={isStreaming && !sections.needsAttention}
        />

        <ReviewSection
          title="Needs Attention"
          content={sections.needsAttention}
          variant="attention"
          isStreaming={isStreaming && !!sections.overview && !sections.lookingGood}
        />

        <ReviewSection
          title="Looking Good"
          content={sections.lookingGood}
          variant="good"
          isStreaming={isStreaming && !!sections.needsAttention && !sections.suggestions}
        />

        <ReviewSection
          title="Suggestions"
          content={sections.suggestions}
          variant="suggestions"
          isStreaming={isStreaming && !!sections.lookingGood}
        />
      </div>

      {onRetry && isComplete && (
        <div className="review-results__footer">
          <button
            type="button"
            className="review-results__review-button"
            onClick={onRetry}
          >
            Re-review
          </button>
        </div>
      )}
    </div>
  );
}

export { ReviewSection } from './ReviewSection';
