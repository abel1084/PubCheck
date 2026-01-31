import { createColumnHelper, ColumnDef } from '@tanstack/react-table';
import { SortableTable } from '../SortableTable';
import type { FontSummary, TextBlock } from '../../types/extraction';

interface TextTabProps {
  fonts: FontSummary[];
  textBlocks: TextBlock[];
}

const columnHelper = createColumnHelper<FontSummary>();

const columns: ColumnDef<FontSummary, any>[] = [
  columnHelper.accessor('name', { header: 'Font Name' }),
  columnHelper.accessor('count', { header: 'Occurrences' }),
  columnHelper.accessor('pages', {
    header: 'Pages',
    cell: info => info.getValue().join(', '),
  }),
];

export function TextTab({ fonts, textBlocks }: TextTabProps) {
  return (
    <div className="text-tab">
      <h3>Font Summary</h3>
      <SortableTable
        data={fonts}
        columns={columns}
        defaultSort={[{ id: 'count', desc: true }]}
        emptyMessage="No fonts found"
      />
      <p className="text-tab__count">{textBlocks.length} text blocks extracted</p>
    </div>
  );
}
