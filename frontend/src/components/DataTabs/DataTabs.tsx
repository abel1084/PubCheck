import { useState } from 'react';
import type { ExtractionResult } from '../../types/extraction';
import { TextTab } from './TextTab';
import { ImagesTab } from './ImagesTab';
import { MarginsTab } from './MarginsTab';
import { MetadataTab } from './MetadataTab';
import './DataTabs.css';

interface DataTabsProps {
  extraction: ExtractionResult;
  defaultCollapsed?: boolean;
}

type TabId = 'text' | 'images' | 'margins' | 'metadata';

export function DataTabs({ extraction, defaultCollapsed = false }: DataTabsProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [activeTab, setActiveTab] = useState<TabId>('text');

  const tabs: { id: TabId; label: string; count: number }[] = [
    { id: 'text', label: 'Text', count: extraction.fonts.length },
    { id: 'images', label: 'Images', count: extraction.images.length },
    { id: 'margins', label: 'Margins', count: extraction.margins.length },
    { id: 'metadata', label: 'Metadata', count: 1 },
  ];

  return (
    <div className="data-tabs">
      <button
        type="button"
        className="data-tabs__toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        aria-expanded={!isCollapsed}
      >
        <span className="data-tabs__toggle-icon">
          {isCollapsed ? '\u25B6' : '\u25BC'}
        </span>
        Extracted Data
      </button>

      {!isCollapsed && (
        <>
          <div className="data-tabs__header">
            {tabs.map(tab => {
              const isEmpty = tab.id !== 'metadata' && tab.count === 0;
              return (
                <button
                  key={tab.id}
                  className={`data-tabs__tab ${activeTab === tab.id ? 'data-tabs__tab--active' : ''} ${isEmpty ? 'data-tabs__tab--disabled' : ''}`}
                  onClick={() => !isEmpty && setActiveTab(tab.id)}
                  disabled={isEmpty}
                >
                  {tab.label} ({tab.count})
                </button>
              );
            })}
          </div>
          <div className="data-tabs__content">
            {activeTab === 'text' && <TextTab fonts={extraction.fonts} textBlocks={extraction.text_blocks} />}
            {activeTab === 'images' && <ImagesTab images={extraction.images} />}
            {activeTab === 'margins' && <MarginsTab margins={extraction.margins} />}
            {activeTab === 'metadata' && <MetadataTab metadata={extraction.metadata} />}
          </div>
        </>
      )}
    </div>
  );
}
