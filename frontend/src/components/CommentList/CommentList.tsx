import { useState } from 'react';
import type { ReviewIssue } from '../../types/review';
import './CommentList.css';

interface CommentListProps {
  /** All issues from AI review */
  issues: ReviewIssue[];
  /** Currently selected issue IDs */
  selectedIds: Set<string>;
  /** Toggle selection callback */
  onToggleSelect: (id: string) => void;
}

/**
 * Selectable list of AI review issues for PDF annotation.
 * Groups issues by category with collapsible sections.
 */
export function CommentList({
  issues,
  selectedIds,
  onToggleSelect,
}: CommentListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Group issues by category
  const needsAttention = issues.filter(i => i.category === 'needs_attention');
  const suggestions = issues.filter(i => i.category === 'suggestion');

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Render a section (Needs Attention or Suggestions)
  const renderSection = (
    title: string,
    sectionIssues: ReviewIssue[],
    variant: 'attention' | 'suggestions'
  ) => {
    if (sectionIssues.length === 0) {
      return null;
    }

    const selectedInSection = sectionIssues.filter(i => selectedIds.has(i.id)).length;
    const allSelected = selectedInSection === sectionIssues.length;
    const someSelected = selectedInSection > 0 && !allSelected;

    const handleSectionToggle = () => {
      if (allSelected) {
        // Deselect all in section
        sectionIssues.forEach(i => {
          if (selectedIds.has(i.id)) {
            onToggleSelect(i.id);
          }
        });
      } else {
        // Select all in section
        sectionIssues.forEach(i => {
          if (!selectedIds.has(i.id)) {
            onToggleSelect(i.id);
          }
        });
      }
    };

    return (
      <div className={`comment-list__section comment-list__section--${variant}`}>
        <div className="comment-list__section-header">
          <label className="comment-list__section-checkbox">
            <input
              type="checkbox"
              checked={allSelected}
              ref={el => {
                if (el) el.indeterminate = someSelected;
              }}
              onChange={handleSectionToggle}
            />
            <span className="comment-list__section-title">{title}</span>
          </label>
          <span className="comment-list__section-count">
            {selectedInSection}/{sectionIssues.length}
          </span>
        </div>

        <div className="comment-list__items">
          {sectionIssues.map(issue => (
            <div
              key={issue.id}
              className={`comment-list__item ${selectedIds.has(issue.id) ? 'comment-list__item--selected' : ''}`}
            >
              <div className="comment-list__item-header">
                <label className="comment-list__item-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(issue.id)}
                    onChange={() => onToggleSelect(issue.id)}
                  />
                  <span className="comment-list__item-title">{issue.title}</span>
                </label>
                <span className="comment-list__item-pages">
                  {issue.pages.length === 1
                    ? `p. ${issue.pages[0]}`
                    : `pp. ${issue.pages.join(', ')}`}
                </span>
                <button
                  type="button"
                  className={`comment-list__expand-btn ${expandedIds.has(issue.id) ? 'comment-list__expand-btn--expanded' : ''}`}
                  onClick={() => toggleExpanded(issue.id)}
                  aria-label={expandedIds.has(issue.id) ? 'Collapse' : 'Expand'}
                >
                  <svg
                    className="comment-list__expand-icon"
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                  >
                    <path
                      fill="currentColor"
                      d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"
                    />
                  </svg>
                </button>
              </div>

              {expandedIds.has(issue.id) && (
                <div className="comment-list__item-description">
                  {issue.description}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (issues.length === 0) {
    return (
      <div className="comment-list comment-list--empty">
        <p className="comment-list__empty-text">
          No issues found. Run a review to see selectable comments.
        </p>
      </div>
    );
  }

  const totalSelected = selectedIds.size;

  return (
    <div className="comment-list">
      <div className="comment-list__header">
        <h3 className="comment-list__title">Comments for PDF</h3>
        <span className="comment-list__total-count">
          {totalSelected} of {issues.length} selected
        </span>
      </div>

      {renderSection('Needs Attention', needsAttention, 'attention')}
      {renderSection('Suggestions', suggestions, 'suggestions')}
    </div>
  );
}
