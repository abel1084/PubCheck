import { createColumnHelper } from '@tanstack/react-table';
import { SortableTable } from '../SortableTable';
import type { ImageInfo } from '../../types/extraction';

interface ImagesTabProps {
  images: ImageInfo[];
}

const columnHelper = createColumnHelper<ImageInfo>();

const columns = [
  columnHelper.accessor('page', { header: 'Page' }),
  columnHelper.accessor(row => `${row.width} x ${row.height}`, {
    id: 'dimensions',
    header: 'Dimensions'
  }),
  columnHelper.accessor('dpi_x', {
    header: 'DPI (X)',
    cell: info => info.getValue().toFixed(0),
  }),
  columnHelper.accessor('dpi_y', {
    header: 'DPI (Y)',
    cell: info => info.getValue().toFixed(0),
  }),
  columnHelper.accessor('colorspace', { header: 'Color Space' }),
  columnHelper.accessor('has_mask', {
    header: 'Has Mask',
    cell: info => info.getValue() ? 'Yes' : 'No',
  }),
];

export function ImagesTab({ images }: ImagesTabProps) {
  return (
    <div className="images-tab">
      <SortableTable
        data={images}
        columns={columns}
        defaultSort={[{ id: 'dpi_x', desc: false }]}
        emptyMessage="No images found"
      />
    </div>
  );
}
