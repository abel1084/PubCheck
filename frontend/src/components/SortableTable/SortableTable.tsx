import { Table, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';

// Re-export ColumnsType for consumers
export type { ColumnsType };

interface SortableTableProps<T extends object> {
  data: T[];
  columns: ColumnsType<T>;
  rowKey?: string | ((record: T) => string);
  emptyMessage?: string;
}

export function SortableTable<T extends object>({
  data,
  columns,
  rowKey = 'id',
  emptyMessage = 'No data available',
}: SortableTableProps<T>) {
  // Add sorter to each column that has a dataIndex
  const columnsWithSort: ColumnsType<T> = columns.map((col) => {
    // Only add sorter if not already defined and has dataIndex
    if ('dataIndex' in col && col.dataIndex && !col.sorter) {
      const dataIndex = col.dataIndex as keyof T;
      return {
        ...col,
        sorter: (a: T, b: T) => {
          const aVal = a[dataIndex];
          const bVal = b[dataIndex];
          if (typeof aVal === 'number' && typeof bVal === 'number') {
            return aVal - bVal;
          }
          if (typeof aVal === 'string' && typeof bVal === 'string') {
            return aVal.localeCompare(bVal);
          }
          return 0;
        },
      };
    }
    return col;
  });

  if (data.length === 0) {
    return <Empty description={emptyMessage} />;
  }

  return (
    <Table<T>
      columns={columnsWithSort}
      dataSource={data}
      rowKey={rowKey}
      pagination={false}
      size="small"
      scroll={{ x: true }}
    />
  );
}
