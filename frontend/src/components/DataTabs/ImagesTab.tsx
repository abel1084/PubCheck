import { SortableTable, type ColumnsType } from '../SortableTable';
import type { ImageInfo } from '../../types/extraction';

interface ImagesTabProps {
  images: ImageInfo[];
}

type ImageWithKey = ImageInfo & { key: string };

export function ImagesTab({ images }: ImagesTabProps) {
  const columns: ColumnsType<ImageWithKey> = [
    { title: 'Page', dataIndex: 'page', key: 'page' },
    {
      title: 'Dimensions',
      key: 'dimensions',
      render: (_, record) => `${record.width} x ${record.height}`,
    },
    {
      title: 'DPI (X)',
      dataIndex: 'dpi_x',
      key: 'dpi_x',
      render: (v: number) => v.toFixed(0),
    },
    {
      title: 'DPI (Y)',
      dataIndex: 'dpi_y',
      key: 'dpi_y',
      render: (v: number) => v.toFixed(0),
    },
    { title: 'Color Space', dataIndex: 'colorspace', key: 'colorspace' },
    {
      title: 'Has Mask',
      dataIndex: 'has_mask',
      key: 'has_mask',
      render: (v: boolean) => (v ? 'Yes' : 'No'),
    },
  ];

  // Add key to each image for rowKey
  const dataWithKeys: ImageWithKey[] = images.map((img, i) => ({
    ...img,
    key: `${img.page}-${i}`,
  }));

  return (
    <div className="images-tab">
      <SortableTable
        data={dataWithKeys}
        columns={columns}
        rowKey="key"
        emptyMessage="No images found"
      />
    </div>
  );
}
