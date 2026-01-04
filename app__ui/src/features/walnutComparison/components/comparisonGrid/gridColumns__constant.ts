// Grid Column Definitions for TanStack Table

import { ColumnDef } from '@tanstack/react-table';
import { WalnutComparisonDTO } from '@/types/api__type';

export const gridColumns: ColumnDef<WalnutComparisonDTO>[] = [
  {
    accessorKey: 'walnut_id',
    header: 'Walnut ID',
    enableGrouping: true,
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'includesString',
  },
  {
    accessorKey: 'compared_walnut_id',
    header: 'Compared Walnut ID',
    enableGrouping: true,
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'includesString',
  },
  {
    accessorKey: 'width_diff_mm',
    header: 'Width Diff (mm)',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number;
      return value.toFixed(2);
    },
  },
  {
    accessorKey: 'height_diff_mm',
    header: 'Height Diff (mm)',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number;
      return value.toFixed(2);
    },
  },
  {
    accessorKey: 'thickness_diff_mm',
    header: 'Thickness Diff (mm)',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number;
      return value.toFixed(2);
    },
  },
  {
    accessorKey: 'basic_similarity',
    header: 'Basic Similarity',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number | null;
      if (value === null) return 'N/A';
      return `${(value * 100).toFixed(2)}%`;
    },
  },
  {
    accessorKey: 'advanced_similarity',
    header: 'Advanced Similarity',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number | null;
      if (value === null) return 'N/A';
      return `${(value * 100).toFixed(2)}%`;
    },
  },
  {
    accessorKey: 'final_similarity',
    header: 'Final Similarity',
    enableSorting: true,
    enableColumnFilter: true,
    filterFn: 'inNumberRange',
    cell: ({ getValue }) => {
      const value = getValue() as number;
      const percentage = (value * 100).toFixed(2);
      return `${percentage}%`;
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Created At',
    enableSorting: true,
    cell: ({ getValue }) => {
      const value = getValue() as string;
      return new Date(value).toLocaleString();
    },
  },
  {
    accessorKey: 'updated_at',
    header: 'Updated At',
    enableSorting: true,
    cell: ({ getValue }) => {
      const value = getValue() as string;
      return new Date(value).toLocaleString();
    },
  },
];

