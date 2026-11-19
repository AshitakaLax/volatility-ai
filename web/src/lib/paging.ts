/** A table shown a page at a time, so a busy session's hundreds of rows never
 * become hundreds of DOM rows re-rendered on every poll. */

export function pageCount(rows: number, size: number): number {
  return Math.max(1, Math.ceil(rows / size));
}

/** The page in range: a list that shrank (a new session) clamps to its last. */
export function clampPage(page: number, rows: number, size: number): number {
  return Math.min(Math.max(0, page), pageCount(rows, size) - 1);
}

export function pageOf<T>(rows: readonly T[], page: number, size: number): T[] {
  const start = clampPage(page, rows.length, size) * size;
  return rows.slice(start, start + size);
}
