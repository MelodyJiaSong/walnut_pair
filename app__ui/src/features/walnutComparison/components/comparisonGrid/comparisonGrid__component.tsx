'use client';

// Comparison Grid Component using TanStack Table

import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  flexRender,
  ColumnResizeMode,
  GroupingState,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { Table, Spin } from 'antd';
import { WalnutComparisonDTO } from '@/types/api__type';
import { gridColumns } from './gridColumns__constant';
import './comparisonGrid__style.scss';

interface ComparisonGridProps {
  data: WalnutComparisonDTO[];
  loading?: boolean;
}

export default function ComparisonGrid({ data, loading = false }: ComparisonGridProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [grouping, setGrouping] = useState<GroupingState>([]);
  const [columnResizeMode, setColumnResizeMode] = useState<ColumnResizeMode>('onChange');

  const columns = useMemo(() => gridColumns, []);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      grouping,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGroupingChange: setGrouping,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    enableGrouping: true,
    enableColumnResizing: true,
    columnResizeMode,
  });

  if (loading) {
    return (
      <div className="comparison-grid__loading">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="comparison-grid">
      <div className="comparison-grid__table-wrapper">
        <table className="comparison-grid__table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    style={{
                      width: header.getSize(),
                      position: 'relative',
                    }}
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        {...{
                          className: header.column.getCanSort() ? 'cursor-pointer select-none' : '',
                          onClick: header.column.getToggleSortingHandler(),
                        }}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{
                          asc: ' ↑',
                          desc: ' ↓',
                        }[header.column.getIsSorted() as string] ?? null}
                      </div>
                    )}
                    {header.column.getCanResize() && (
                      <div
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        className={`resizer ${header.column.getIsResizing() ? 'isResizing' : ''}`}
                      />
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} style={{ width: cell.column.getSize() }}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

