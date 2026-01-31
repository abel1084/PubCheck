interface AIProgressProps {
  progress: string;
  isAnalyzing: boolean;
}

/**
 * Progress indicator for AI analysis.
 * Shows a spinner and progress text during analysis.
 */
export function AIProgress({ progress, isAnalyzing }: AIProgressProps) {
  if (!isAnalyzing && !progress) return null;

  return (
    <div className="ai-progress">
      {isAnalyzing && <span className="ai-progress__spinner" />}
      <span className="ai-progress__text">{progress}</span>
    </div>
  );
}
