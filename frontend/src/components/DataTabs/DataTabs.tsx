import { useState, useEffect } from 'react';
import type { ExtractionResult } from '../../types/extraction';
import type { CheckResult } from '../../types/checks';
import type { DocumentAnalysisResult } from '../../types/ai';
import { TextTab } from './TextTab';
import { ImagesTab } from './ImagesTab';
import { MarginsTab } from './MarginsTab';
import { MetadataTab } from './MetadataTab';
import { CheckResults } from '../CheckResults';
import './DataTabs.css';

interface DataTabsProps {
  extraction: ExtractionResult;
  checkResult?: CheckResult | null;
  isChecking?: boolean;
  onRecheck?: () => void;
  // AI analysis props
  aiResult?: DocumentAnalysisResult | null;
  isAnalyzing?: boolean;
  aiProgress?: string;
  onReanalyze?: () => void;
  // Document type for ignored rules filtering
  documentType?: string;
  // PDF file for report generation
  pdfFile?: File | null;
}

type TabId = 'text' | 'images' | 'margins' | 'metadata' | 'check-results';

export function DataTabs({
  extraction,
  checkResult,
  isChecking,
  onRecheck,
  aiResult,
  isAnalyzing,
  aiProgress,
  onReanalyze,
  documentType,
  pdfFile
}: DataTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('text');

  // Auto-switch to check-results tab when checking/analyzing starts or result arrives
  useEffect(() => {
    if (isChecking || checkResult || isAnalyzing || aiResult) {
      setActiveTab('check-results');
    }
  }, [isChecking, checkResult, isAnalyzing, aiResult]);

  const showCheckResultsTab = Boolean(isChecking || checkResult || isAnalyzing || aiResult);

  // Calculate combined issue count for tab label
  const getCheckResultsCount = (): number | null => {
    let count = 0;
    if (checkResult) {
      count += checkResult.total_errors + checkResult.total_warnings;
    }
    if (aiResult) {
      count += aiResult.total_findings;
    }
    return count > 0 ? count : (checkResult || aiResult ? 0 : null);
  };

  const tabs: { id: TabId; label: string; count: number | null; visible: boolean }[] = [
    { id: 'text', label: 'Text', count: extraction.fonts.length, visible: true },
    { id: 'images', label: 'Images', count: extraction.images.length, visible: true },
    { id: 'margins', label: 'Margins', count: extraction.margins.length, visible: true },
    { id: 'metadata', label: 'Metadata', count: 1, visible: true },
    { id: 'check-results', label: 'Check Results', count: getCheckResultsCount(), visible: showCheckResultsTab },
  ];

  return (
    <div className="data-tabs">
      <div className="data-tabs__header">
        {tabs.filter(tab => tab.visible).map(tab => {
          const isEmpty = tab.id !== 'metadata' && tab.id !== 'check-results' && tab.count === 0;
          const isCheckResults = tab.id === 'check-results';
          return (
            <button
              key={tab.id}
              className={`data-tabs__tab ${activeTab === tab.id ? 'data-tabs__tab--active' : ''} ${isEmpty ? 'data-tabs__tab--disabled' : ''} ${isCheckResults ? 'data-tabs__tab--check-results' : ''}`}
              onClick={() => !isEmpty && setActiveTab(tab.id)}
              disabled={isEmpty}
            >
              {tab.label}{tab.count !== null ? ` (${tab.count})` : ''}
            </button>
          );
        })}
      </div>
      <div className="data-tabs__content">
        {activeTab === 'text' && <TextTab fonts={extraction.fonts} textBlocks={extraction.text_blocks} />}
        {activeTab === 'images' && <ImagesTab images={extraction.images} />}
        {activeTab === 'margins' && <MarginsTab margins={extraction.margins} />}
        {activeTab === 'metadata' && <MetadataTab metadata={extraction.metadata} />}
        {activeTab === 'check-results' && (
          (isChecking && !checkResult) ? (
            <div className="data-tabs__loading">
              <span className="data-tabs__spinner"></span>
              Checking...
            </div>
          ) : (
            <CheckResults
              result={checkResult}
              onRecheck={onRecheck}
              aiResult={aiResult}
              isAnalyzing={isAnalyzing}
              aiProgress={aiProgress}
              onReanalyze={onReanalyze}
              documentType={documentType}
              pdfFile={pdfFile}
            />
          )
        )}
      </div>
    </div>
  );
}
