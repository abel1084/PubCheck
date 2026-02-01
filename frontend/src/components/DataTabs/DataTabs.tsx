import { useState } from 'react';
import { Collapse, Tabs, type TabsProps } from 'antd';
import type { ExtractionResult } from '../../types/extraction';
import { TextTab } from './TextTab';
import { ImagesTab } from './ImagesTab';
import { MarginsTab } from './MarginsTab';
import { MetadataTab } from './MetadataTab';

interface DataTabsProps {
  extraction: ExtractionResult;
  defaultCollapsed?: boolean;
}

export function DataTabs({ extraction, defaultCollapsed = false }: DataTabsProps) {
  const [activeKey, setActiveKey] = useState(defaultCollapsed ? [] : ['data']);

  const tabItems: TabsProps['items'] = [
    {
      key: 'text',
      label: `Text (${extraction.fonts.length})`,
      children: <TextTab fonts={extraction.fonts} textBlocks={extraction.text_blocks} />,
    },
    {
      key: 'images',
      label: `Images (${extraction.images.length})`,
      children: <ImagesTab images={extraction.images} />,
      disabled: extraction.images.length === 0,
    },
    {
      key: 'margins',
      label: `Margins (${extraction.margins.length})`,
      children: <MarginsTab margins={extraction.margins} />,
      disabled: extraction.margins.length === 0,
    },
    {
      key: 'metadata',
      label: 'Metadata',
      children: <MetadataTab metadata={extraction.metadata} />,
    },
  ];

  const collapseItems = [
    {
      key: 'data',
      label: 'Extracted Data',
      children: (
        <Tabs
          items={tabItems}
          defaultActiveKey="text"
          size="small"
        />
      ),
    },
  ];

  return (
    <Collapse
      activeKey={activeKey}
      onChange={(keys) => setActiveKey(keys as string[])}
      items={collapseItems}
      style={{ marginTop: 16 }}
    />
  );
}
