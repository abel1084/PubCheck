import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  SortingState,
  ColumnDef,
} from '@tanstack/react-table';
import './SortableTable.css';

interface SortableTableProps<T> {
  data: T[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: ColumnDef<T, any>[];
  defaultSort?: SortingState;
  emptyMessage?: string;
}

export function SortableTable<T>({
  data,
  columns,
  defaultSort = [],
  emptyMessage = 'No data available'
}: SortableTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>(defaultSort);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (data.length === 0) {
    return (
      <div className="sortable-table__empty">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="sortable-table-container">
      <table className="sortable-table">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => {
                const canSort = header.column.getCanSort();
                const sortDirection = header.column.getIsSorted();

                const headerClassNames = [
                  'sortable-table__header',
                  canSort ? 'sortable-table__header--sortable' : '',
                  sortDirection ? 'sortable-table__header--sorted' : '',
                ].filter(Boolean).join(' ');

                return (
                  <th
                    key={header.id}
                    onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                    className={headerClassNames}
                  >
                    <div className="sortable-table__header-content">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {canSort && (
                        <span className="sortable-table__sort-indicator">
                          {sortDirection === 'asc' && ' \u25B2'}
                          {sortDirection === 'desc' && ' \u25BC'}
                          {!sortDirection && ' \u21C5'}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="sortable-table__row">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="sortable-table__cell">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
