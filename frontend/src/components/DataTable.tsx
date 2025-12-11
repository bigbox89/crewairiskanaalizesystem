import React, { useMemo, useState } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { ParsedTable } from '../types';

interface DataTableProps {
  table: ParsedTable;
}

const DataTable: React.FC<DataTableProps> = ({ table }) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo<ColumnDef<Record<string, any>>[]>(
    () =>
      table.columns.map((key) => ({
        accessorKey: key,
        header: key,
        cell: ({ getValue }) => {
          const val = getValue();
          if (val === null || val === undefined) return '—';
          if (typeof val === 'object') return JSON.stringify(val);
          return String(val);
        },
      })),
    [table.columns],
  );

  const instance = useReactTable({
    data: table.rows,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="mt-3 rounded-lg border border-neutral-700 bg-neutral-800">
      <div className="flex flex-col gap-2 p-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-200">{table.title || 'Таблица'}</p>
          <p className="text-xs text-gray-400">
            {table.rows.length} строк • сортировка и поиск по всем столбцам
          </p>
        </div>
        <input
          className="w-full rounded bg-neutral-900 px-3 py-1 text-sm text-gray-100 outline-none ring-1 ring-neutral-700 focus:ring-blue-500 sm:w-56"
          placeholder="Поиск..."
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-t border-neutral-700 text-sm">
          <thead className="bg-neutral-900 text-left text-gray-300">
            {instance.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="cursor-pointer px-3 py-2 text-xs uppercase tracking-wide"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {{
                        asc: '↑',
                        desc: '↓',
                      }[header.column.getIsSorted() as string] || ''}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {instance.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-neutral-800 odd:bg-neutral-800/60 even:bg-neutral-800"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 text-gray-100">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col items-center justify-between gap-2 border-t border-neutral-700 px-3 py-2 sm:flex-row">
        <div className="space-x-2">
          <button
            className="rounded bg-neutral-900 px-3 py-1 text-xs text-gray-200 ring-1 ring-neutral-700 disabled:opacity-50"
            onClick={() => instance.previousPage()}
            disabled={!instance.getCanPreviousPage()}
          >
            Назад
          </button>
          <button
            className="rounded bg-neutral-900 px-3 py-1 text-xs text-gray-200 ring-1 ring-neutral-700 disabled:opacity-50"
            onClick={() => instance.nextPage()}
            disabled={!instance.getCanNextPage()}
          >
            Вперёд
          </button>
        </div>
        <div className="text-xs text-gray-400">
          Стр. {instance.getState().pagination.pageIndex + 1} из{' '}
          {instance.getPageCount() || 1}
        </div>
      </div>
    </div>
  );
};

export default DataTable;

