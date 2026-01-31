import { createColumnHelper, ColumnDef } from '@tanstack/react-table';
import { SortableTable } from '../SortableTable';
import type { PageMargins } from '../../types/extraction';

interface MarginsTabProps {
  margins: PageMargins[];
}

const columnHelper = createColumnHelper<PageMargins>();

// Convert points to mm for display (72 points = 25.4 mm)
const ptToMm = (pt: number) => (pt / 72 * 25.4).toFixed(1);

const columns: ColumnDef<PageMargins, any>[] = [
  columnHelper.accessor('page', { header: 'Page' }),
  columnHelper.accessor('top', {
    header: 'Top (mm)',
    cell: info => ptToMm(info.getValue()),
  }),
  columnHelper.accessor('bottom', {
    header: 'Bottom (mm)',
    cell: info => ptToMm(info.getValue()),
  }),
  columnHelper.accessor('inside', {
    header: 'Inside (mm)',
    cell: info => ptToMm(info.getValue()),
  }),
  columnHelper.accessor('outside', {
    header: 'Outside (mm)',
    cell: info => ptToMm(info.getValue()),
  }),
];

export function MarginsTab({ margins }: MarginsTabProps) {
  return (
    <div className="margins-tab">
      <SortableTable
        data={margins}
        columns={columns}
        defaultSort={[{ id: 'page', desc: false }]}
        emptyMessage="No margin data available"
      />
    </div>
  );
}
