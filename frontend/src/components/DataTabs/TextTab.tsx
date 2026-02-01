import { SortableTable, type ColumnsType } from '../SortableTable';
import type { FontSummary, TextBlock } from '../../types/extraction';

interface TextTabProps {
  fonts: FontSummary[];
  textBlocks: TextBlock[];
}

export function TextTab({ fonts, textBlocks }: TextTabProps) {
  const columns: ColumnsType<FontSummary> = [
    { title: 'Font Name', dataIndex: 'name', key: 'name' },
    { title: 'Occurrences', dataIndex: 'count', key: 'count' },
    {
      title: 'Pages',
      dataIndex: 'pages',
      key: 'pages',
      render: (pages: number[]) => pages.join(', '),
    },
  ];

  return (
    <div className="text-tab">
      <h3>Font Summary</h3>
      <SortableTable
        data={fonts}
        columns={columns}
        rowKey="name"
        emptyMessage="No fonts found"
      />
      <p className="text-tab__count">{textBlocks.length} text blocks extracted</p>
    </div>
  );
}
