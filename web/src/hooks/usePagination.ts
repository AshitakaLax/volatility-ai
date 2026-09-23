import { useEffect, useMemo, useState } from "react";

/**
 * Client-side pagination over an already filtered+sorted list.
 *
 * Follows `LiveOrderLedger`'s behavior exactly: page resets to 1 when
 * the item count or page size changes, `totalPages` is at least 1, and
 * the slice is `(page-1)*pageSize .. page*pageSize`. The hook owns the
 * page state so every list (RunHistory, Simulations, TradeLog) shares
 * one convention instead of three hand-rolled copies.
 */
export function usePagination(totalItems: number, defaultPageSize = 50) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  useEffect(() => {
    setPage(1);
  }, [totalItems, pageSize]);

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;

  const paginate = useMemo(
    () =>
      <T,>(items: T[]): T[] =>
        items.slice(start, start + pageSize),
    [start, pageSize],
  );

  return {
    page: safePage,
    pageSize,
    totalPages,
    start,
    setPage: (next: number | ((prev: number) => number)) =>
      setPage((prev) => {
        const value = typeof next === "function" ? next(prev) : next;
        return Math.min(Math.max(1, value), Math.max(1, Math.ceil(totalItems / pageSize)));
      }),
    setPageSize,
    paginate,
  };
}
