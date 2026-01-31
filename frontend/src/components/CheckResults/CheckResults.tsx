import { useMemo } from 'react';
import type { CheckResult, CategoryResult, CheckIssue } from '../../types/checks';
import type { DocumentAnalysisResult } from '../../types/ai';
import { StatusBadge } from './StatusBadge';
import { CategorySection } from './CategorySection';
import { ReviewSummaryBar } from './ReviewSummaryBar';
import { AIProgress } from './AIProgress';
import { useReviewState, getIssueId } from '../../hooks/useReviewState';
import './CheckResults.css';

interface CheckResultsProps {
  result?: CheckResult | null;
  onRecheck?: () => void;
  // AI analysis props
  aiResult?: DocumentAnalysisResult | null;
  isAnalyzing?: boolean;
  aiProgress?: string;
  onReanalyze?: () => void;
}

// Fixed category order per CONTEXT.md
const CATEGORY_ORDER = ['cover', 'margins', 'typography', 'images', 'required_elements', 'ai_analysis'];

/**
 * Convert AI findings to CheckIssue format for unified display.
 */
function convertAIFindingsToIssues(aiResult: DocumentAnalysisResult): CheckIssue[] {
  const issues: CheckIssue[] = [];

  for (const pageResult of aiResult.page_results) {
    // Handle page errors
    if (pageResult.error) {
      issues.push({
        rule_id: 'ai_error',
        rule_name: 'AI Analysis Error',
        severity: 'warning',
        message: pageResult.error,
        expected: null,
        actual: null,
        pages: [pageResult.page_number],
        ai_verified: true,
        ai_confidence: 'low',
      });
      continue;
    }

    // Convert findings
    for (const finding of pageResult.findings) {
      if (!finding.passed) {
        issues.push({
          rule_id: `ai_${finding.check_name.toLowerCase().replace(/\s+/g, '_')}`,
          rule_name: finding.check_name,
          severity: finding.confidence === 'low' ? 'warning' : 'error',
          message: finding.message,
          expected: null,
          actual: finding.location || null,
          pages: [pageResult.page_number],
          how_to_fix: finding.suggestion,
          ai_verified: true,
          ai_confidence: finding.confidence,
          ai_reasoning: finding.reasoning,
        });
      }
    }
  }

  return issues;
}

/**
 * Main check results component.
 * Shows status badge, summary counts, and categorized issues.
 * Pass status shows green success banner.
 * Supports AI analysis results with progress indicator.
 */
export function CheckResults({
  result,
  onRecheck,
  aiResult,
  isAnalyzing,
  aiProgress,
  onReanalyze
}: CheckResultsProps) {
  // Convert AI findings to issues
  const aiIssues = aiResult ? convertAIFindingsToIssues(aiResult) : [];

  // Create AI analysis category if there are AI results
  const aiCategory: CategoryResult | null = aiResult ? {
    category_id: 'ai_analysis',
    category_name: 'AI Analysis',
    issues: aiIssues,
    error_count: aiIssues.filter(i => i.severity === 'error').length,
    warning_count: aiIssues.filter(i => i.severity === 'warning').length,
  } : null;

  // Sort and combine categories - memoize to prevent infinite loops
  const sortedCategories = useMemo(() => {
    const allCategories: CategoryResult[] = [
      ...(result?.categories || []),
      ...(aiCategory ? [aiCategory] : []),
    ];

    return [...allCategories].sort((a: CategoryResult, b: CategoryResult) => {
      const aIndex = CATEGORY_ORDER.indexOf(a.category_id);
      const bIndex = CATEGORY_ORDER.indexOf(b.category_id);
      // Unknown categories go to end
      const aOrder = aIndex === -1 ? CATEGORY_ORDER.length : aIndex;
      const bOrder = bIndex === -1 ? CATEGORY_ORDER.length : bIndex;
      return aOrder - bOrder;
    });
  }, [result?.categories, aiCategory]);

  // Initialize review state with all categories (sorted)
  const {
    selectedIssues,
    notes,
    severityFilter,
    categoryFilter,
    filteredCategories,
    counts,
    toggleSelection,
    selectCategory,
    deselectCategory,
    selectAllVisible,
    deselectAll,
    setNote,
    setSeverityFilter,
    setCategoryFilter,
  } = useReviewState(sortedCategories);

  // Compute issue IDs for filtered categories (for current display)
  // When filtering, issues shift position but we need stable IDs based on original index
  const filteredCategoryIssueIds = useMemo(() => {
    const result: Record<string, string[]> = {};
    for (const category of filteredCategories) {
      // Find original category to get original indices
      const originalCategory = sortedCategories.find(c => c.category_id === category.category_id);
      if (!originalCategory) continue;

      // Map filtered issues to their original IDs using original index
      result[category.category_id] = category.issues.map((issue) => {
        // Find the original index of this issue by matching rule_id, pages, and message
        const originalIndex = originalCategory.issues.findIndex(
          (o) => o.rule_id === issue.rule_id && o.pages.join(',') === issue.pages.join(',') && o.message === issue.message
        );
        return getIssueId(issue, category.category_id, originalIndex !== -1 ? originalIndex : 0);
      });
    }
    return result;
  }, [filteredCategories, sortedCategories]);

  // Calculate combined totals
  const totalErrors = (result?.total_errors || 0) + (aiCategory?.error_count || 0);
  const totalWarnings = (result?.total_warnings || 0) + (aiCategory?.warning_count || 0);

  // Determine overall status
  const getStatus = (): 'pass' | 'fail' | 'warning' => {
    if (totalErrors > 0) return 'fail';
    if (totalWarnings > 0) return 'warning';
    return 'pass';
  };

  const status = result?.status || (aiResult ? getStatus() : 'pass');
  const isAllPassed = status === 'pass' && !isAnalyzing;

  // Show nothing if no results and not analyzing
  if (!result && !aiResult && !isAnalyzing) {
    return (
      <div className="check-results">
        <div className="check-results__empty">
          Click "Check" to run compliance checks or "Analyze with AI" for AI-powered analysis.
        </div>
      </div>
    );
  }

  // Add padding class when summary bar is visible
  const hasResultsWithIssues = !isAllPassed && sortedCategories.length > 0;

  return (
    <div className={`check-results ${hasResultsWithIssues ? 'check-results--has-summary-bar' : ''}`}>
      <div className="check-results__header">
        <div className="check-results__title-row">
          <h3 className="check-results__title">Compliance Check Results</h3>
          <StatusBadge status={status} />
        </div>
        <div className="check-results__summary">
          {totalErrors > 0 && (
            <span className="check-results__count check-results__count--error">
              {totalErrors} error{totalErrors !== 1 ? 's' : ''}
            </span>
          )}
          {totalWarnings > 0 && (
            <span className="check-results__count check-results__count--warning">
              {totalWarnings} warning{totalWarnings !== 1 ? 's' : ''}
            </span>
          )}
          {onRecheck && (
            <button
              type="button"
              className="check-results__recheck"
              onClick={onRecheck}
            >
              Re-check
            </button>
          )}
          {onReanalyze && (
            <button
              type="button"
              className="check-results__recheck"
              onClick={onReanalyze}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? 'Analyzing...' : 'Re-analyze'}
            </button>
          )}
          <div className="check-results__filters">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="check-results__category-filter"
            >
              <option value="all">All Categories</option>
              {sortedCategories.map(cat => (
                <option key={cat.category_id} value={cat.category_id}>
                  {cat.category_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* AI Progress indicator */}
      <AIProgress progress={aiProgress || ''} isAnalyzing={isAnalyzing || false} />

      {isAllPassed ? (
        <div className="check-results__success">
          <span className="check-results__success-icon">{'\u2713'}</span>
          <span className="check-results__success-text">All checks passed</span>
        </div>
      ) : filteredCategories.length === 0 && sortedCategories.length > 0 ? (
        <div className="check-results__filter-empty">
          No issues match current filters
        </div>
      ) : (
        <div className="check-results__categories">
          {filteredCategories.map((category) => (
            <CategorySection
              key={category.category_id}
              category={category}
              issueIds={filteredCategoryIssueIds[category.category_id]}
              selectedIds={selectedIssues}
              notes={notes}
              onToggleSelect={toggleSelection}
              onSelectCategory={() => selectCategory(category.category_id, filteredCategoryIssueIds[category.category_id] || [])}
              onDeselectCategory={() => deselectCategory(category.category_id, filteredCategoryIssueIds[category.category_id] || [])}
              onNoteChange={setNote}
            />
          ))}
        </div>
      )}

      {/* Document summary from AI */}
      {aiResult?.document_summary && (
        <div className="check-results__ai-summary">
          <h4 className="check-results__ai-summary-title">AI Summary</h4>
          <p className="check-results__ai-summary-text">{aiResult.document_summary}</p>
        </div>
      )}

      <div className="check-results__footer">
        {result && (
          <span className="check-results__duration">
            Check completed in {result.check_duration_ms}ms
          </span>
        )}
        {aiResult && (
          <span className="check-results__duration">
            {result ? ' | ' : ''}AI analysis completed in {aiResult.analysis_duration_ms}ms
          </span>
        )}
      </div>

      {/* Review summary bar - fixed at bottom */}
      {!isAllPassed && (
        <ReviewSummaryBar
          counts={counts}
          severityFilter={severityFilter}
          onFilterChange={setSeverityFilter}
          onSelectAllVisible={selectAllVisible}
          onDeselectAll={deselectAll}
          canGenerateReport={counts.selected > 0}
        />
      )}
    </div>
  );
}
