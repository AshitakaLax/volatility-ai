import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button, Select } from "@/components/ui/primitives";

interface Props {
  page: number;
  totalPages: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number | ((prev: number) => number)) => void;
  onPageSizeChange: (size: number) => void;
  pageSizeOptions?: number[];
}

/**
 * Footer for a paginated table. Same copy and affordances as
 * `LiveOrderLedger` ("Showing X to Y of Z entries", Show N entries,
 * Prev/Next) so the three backtest lists read as one UI rather than
 * three similar-but-different ones.
 */
export function Pagination({
  page,
  totalPages,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [25, 50, 100],
}: Props) {
  if (total === 0) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
      <div className="flex items-center gap-2">
        <span>Show</span>
        <Select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="w-20"
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </Select>
        <span>entries</span>
      </div>

      <div className="flex items-center gap-4">
        <span className="tnum">
          Showing {from} to {to} of {total} entries
        </span>
        <div className="flex gap-1">
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => onPageChange((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            aria-label="Previous page"
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => onPageChange((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            aria-label="Next page"
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
