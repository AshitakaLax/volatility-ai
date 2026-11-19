import { Button } from "@/components/ui/primitives";
import { clampPage, pageCount } from "@/lib/paging";

/** Newer / Older for a table shown a page at a time (lib/paging.ts); nothing
 * when it fits on one page. */
export function Pager({
  page,
  rows,
  size,
  onPage,
}: {
  page: number;
  rows: number;
  size: number;
  onPage: (page: number) => void;
}) {
  const pages = pageCount(rows, size);
  if (pages <= 1) return null;
  const at = clampPage(page, rows, size);
  const first = at * size + 1;
  const last = Math.min(rows, (at + 1) * size);
  return (
    <div className="mt-2 flex items-center justify-end gap-2 text-xs text-muted-foreground">
      <span className="tnum">
        {first}–{last} of {rows}
      </span>
      <Button
        variant="outline"
        className="px-2 py-0.5 text-xs"
        disabled={at === 0}
        onClick={() => onPage(at - 1)}
      >
        Newer
      </Button>
      <Button
        variant="outline"
        className="px-2 py-0.5 text-xs"
        disabled={at >= pages - 1}
        onClick={() => onPage(at + 1)}
      >
        Older
      </Button>
    </div>
  );
}
