import { SortableTable, type ColumnsType } from '../SortableTable';
import type { PageMargins } from '../../types/extraction';

interface MarginsTabProps {
  margins: PageMargins[];
}

// Convert points to mm for display (72 points = 25.4 mm)
const ptToMm = (pt: number) => `${(pt / 72 * 25.4).toFixed(1)} mm`;

export function MarginsTab({ margins }: MarginsTabProps) {
  const columns: ColumnsType<PageMargins> = [
    { title: 'Page', dataIndex: 'page', key: 'page' },
    { title: 'Top (mm)', dataIndex: 'top', key: 'top', render: ptToMm },
    { title: 'Bottom (mm)', dataIndex: 'bottom', key: 'bottom', render: ptToMm },
    { title: 'Inside (mm)', dataIndex: 'inside', key: 'inside', render: ptToMm },
    { title: 'Outside (mm)', dataIndex: 'outside', key: 'outside', render: ptToMm },
  ];

  return (
    <div className="margins-tab">
      <SortableTable
        data={margins}
        columns={columns}
        rowKey="page"
        emptyMessage="No margin data available"
      />
    </div>
  );
}
