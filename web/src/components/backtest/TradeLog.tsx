import { ChevronDown, ChevronRight, Download, ListOrdered } from "lucide-react";
import { useState } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { Pagination } from "@/components/ui/Pagination";
import { type FillsSource, useFills } from "@/hooks/useFills";
import { usePagination } from "@/hooks/usePagination";
import { api } from "@/lib/api";
import { fillKey } from "@/lib/filters";
import { cn, usd } from "@/lib/utils";
import type { CycleRow, Fill, FillsQuery, FillsSummary } from "@/types/backtest";

/**
 * Every trade the simulation would make, in the window in view.
 *
 * COLLAPSED BY DEFAULT, and that is not only about screen space. A ten
 * year run produces tens of thousands of executions; rendering them all
 * on load would make the page slow to open for a table most visits do
 * not need. Opening it is a deliberate act, and the row cap below keeps
 * even that bounded.
 *
 * It shows the FILTERED executions, the same set the chart is drawing.
 * A log that ignored the filters would disagree with the markers beside
 * it, and the reader would have no way to tell which was right.
 *
 * PAGED FROM THE SERVER. A busy run has ~850k fills; the log fetches only
 * the page it is showing (and nothing while collapsed), the header's
 * counts come from the filtered set's summary, and the CSV streams from
 * the server rather than being assembled in the browser.
 *
 * TWO VIEWS OF THE SAME DATA:
 *
 *   fills   every buy and sell as the engine recorded it.
 *   cycles  one row per lot -- entry, exit, hold, realised P&L. This is
 *           the one that answers "what did this trade actually make",
 *           which a flat fill list cannot without mental joining.
 */

interface Props {
  /** The run+fund to page fills from. */
  source: FillsSource | null;
  /** The page's execution filters as fills-endpoint parameters. */
  filterQuery: Omit<FillsQuery, "ticker">;
  /** Counts over the whole filtered set, fetched by the parent. */
  summary: FillsSummary | null;
  ticker: string | null;
  /**
   * The run's profit target, as a fraction, so an open lot can show the
   * price it is waiting for. Passed rather than derived: the execution
   * carries no target, and computing one from an assumed value would
   * name a price no resting order is at.
   */
  profitTarget: number;
}

// Enough to scroll through and see the shape; past this a table stops
// being something a person reads. Paginated (not silently truncated),
// with the CSV uncapped for the full set.
const PAGE_SIZE = 50;

type View = "fills" | "cycles";

export function TradeLog({ source, filterQuery, summary, ticker, profitTarget }: Props) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<View>("cycles");

  const fillCount = summary?.fills ?? 0;
  const cycleCount = (summary?.closed ?? 0) + (summary?.open ?? 0);
  const realised = summary?.realized ?? 0;

  const rows = view === "fills" ? fillCount : cycleCount;
  const cyclesPagination = usePagination(cycleCount, PAGE_SIZE);
  const fillsPagination = usePagination(fillCount, PAGE_SIZE);
  const pagination = view === "cycles" ? cyclesPagination : fillsPagination;
  const pageQuery = open
    ? { ...filterQuery, offset: pagination.start, limit: pagination.pageSize }
    : null;
  const { page: cyclesPage } = useFills<CycleRow>(
    source,
    pageQuery && view === "cycles" ? { ...pageQuery, view: "cycles" } : null,
  );
  const { page: fillsPage } = useFills<Fill>(source, pageQuery && view === "fills" ? pageQuery : null);
  const csvHref = source ? api.fillsCsvUrl(source.runId, { ...filterQuery, ticker: source.ticker }) : null;

  return (
    <Card>
      <CardHeader
        data-testid="trade-log-toggle"
        className="flex-row cursor-pointer items-center justify-between select-none"
        onClick={() => setOpen((value) => !value)}
      >
        <CardTitle className="flex items-center gap-2">
          {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
          <ListOrdered className="size-4" />
          Trade log
        </CardTitle>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>
            {fillCount.toLocaleString()} fill{fillCount === 1 ? "" : "s"}
            {summary && summary.fills !== summary.fills_unfiltered
              ? ` of ${summary.fills_unfiltered.toLocaleString()}, filtered`
              : ""}
          </span>
          <span>
            {(summary?.closed ?? 0).toLocaleString()} closed · {(summary?.open ?? 0).toLocaleString()} open
          </span>
          <Badge tone={realised >= 0 ? "profit" : "loss"}>{usd(realised)}</Badge>
        </div>
      </CardHeader>

      {open ? (
        <>
          <CardContent className="flex items-center gap-2 pb-3">
            {(["cycles", "fills"] as const).map((option) => (
              <Button
                key={option}
                variant={view === option ? "default" : "outline"}
                className="h-7 px-2 text-xs"
                onClick={() => setView(option)}
              >
                {option === "cycles" ? "By lot" : "By fill"}
              </Button>
            ))}
            <span className="ml-2 text-xs text-muted-foreground">
              {view === "cycles"
                ? "one row per lot: entry, exit, and what it actually made"
                : "every buy and sell as the engine recorded it"}
            </span>
            {csvHref ? (
              <a
                href={csvHref}
                download={`trades-${ticker ?? "fund"}.csv`}
                className="ml-auto inline-flex h-7 items-center gap-1.5 rounded-md px-2 text-xs font-medium hover:bg-accent"
                title="Download the filtered fills as CSV"
              >
                <Download className="size-3.5" />
                CSV
              </a>
            ) : null}
          </CardContent>

          <CardContent className="overflow-x-auto pt-0">
            {rows === 0 ? (
              <p className="text-sm text-muted-foreground">
                No trades in this window. A low-volatility fund on a grid tuned for a
                leveraged one legitimately never triggers — widen the range, or lower the
                grid step.
              </p>
            ) : view === "cycles" ? (
              <table className="w-full min-w-[900px] text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2 font-medium">Lot</th>
                    <th className="pb-2 font-medium">Bought</th>
                    <th className="pb-2 text-right font-medium">Price</th>
                    <th className="pb-2 text-right font-medium">Shares</th>
                    <th className="pb-2 text-right font-medium">RSI</th>
                    <th className="pb-2 font-medium">Sold</th>
                    <th className="pb-2 text-right font-medium">Price</th>
                    <th className="pb-2 text-right font-medium">P&amp;L</th>
                    <th className="pb-2 font-medium">Why</th>
                  </tr>
                </thead>
                <tbody className="tnum">
                  {(cyclesPage?.rows ?? []).map((cycle) => {
                    const exit = cycle.sells[cycle.sells.length - 1];
                    return (
                      <tr key={cycle.lot} className="border-b border-border/50 last:border-0">
                        <td className="py-1.5 font-mono text-xs">{cycle.lot}</td>
                        <td className="py-1.5 text-xs">{stamp(cycle.buy.ts)}</td>
                        <td className="py-1.5 text-right">{usd(cycle.buy.px, 4)}</td>
                        <td className="py-1.5 text-right">{cycle.buy.qty.toFixed(4)}</td>
                        <td className="py-1.5 text-right text-muted-foreground">
                          {/* Absent inside the indicator's warmup. Not
                              zero, which would read as extremely
                              oversold. */}
                          {cycle.buy.rsi?.toFixed(1) ?? "--"}
                        </td>
                        <td className="py-1.5 text-xs">
                          {exit ? (
                            stamp(exit.ts)
                          ) : (
                            <span className="text-stuck">still open</span>
                          )}
                        </td>
                        <td className="py-1.5 text-right">{exit ? usd(exit.px, 4) : "--"}</td>
                        <td
                          className={cn(
                            "py-1.5 text-right font-medium",
                            cycle.realized !== null && cycle.realized >= 0 && "text-profit",
                            cycle.realized !== null && cycle.realized < 0 && "text-loss",
                          )}
                        >
                          {cycle.realized === null ? "--" : usd(cycle.realized)}
                        </td>
                        <td className="py-1.5 text-xs">
                          {exit?.why === "signal_exit" ? (
                            <Badge tone="loss">signal exit</Badge>
                          ) : exit ? (
                            <span className="text-muted-foreground">target</span>
                          ) : (
                            <span className="text-muted-foreground">
                              waiting for {usd(cycle.buy.px * (1 + profitTarget), 4)}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <table className="w-full min-w-[820px] text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2 font-medium">When</th>
                    <th className="pb-2 font-medium">Side</th>
                    <th className="pb-2 font-medium">Lot</th>
                    <th className="pb-2 text-right font-medium">Price</th>
                    <th className="pb-2 text-right font-medium">Shares</th>
                    <th className="pb-2 text-right font-medium">Value</th>
                    <th className="pb-2 text-right font-medium">RSI</th>
                    <th className="pb-2 text-right font-medium">P&amp;L</th>
                  </tr>
                </thead>
                <tbody className="tnum">
                  {(fillsPage?.rows ?? []).map((execution) => (
                    <tr
                      key={fillKey(execution)}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="py-1.5 text-xs">{stamp(execution.ts)}</td>
                      <td className="py-1.5">
                        <Badge tone={execution.side === "BUY" ? "neutral" : "profit"}>
                          {execution.side}
                        </Badge>
                      </td>
                      <td className="py-1.5 font-mono text-xs text-muted-foreground">
                        {execution.lot}
                      </td>
                      <td className="py-1.5 text-right">{usd(execution.px, 4)}</td>
                      <td className="py-1.5 text-right">{execution.qty.toFixed(4)}</td>
                      <td className="py-1.5 text-right text-muted-foreground">
                        {usd(execution.px * execution.qty)}
                      </td>
                      <td className="py-1.5 text-right text-muted-foreground">
                        {execution.rsi?.toFixed(1) ?? "--"}
                      </td>
                      <td
                        className={cn(
                          "py-1.5 text-right",
                          (execution.pnl ?? 0) > 0 && "text-profit",
                          (execution.pnl ?? 0) < 0 && "text-loss",
                        )}
                      >
                        {execution.pnl === undefined
                          ? "--"
                          : usd(execution.pnl)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <Pagination
              page={pagination.page}
              totalPages={pagination.totalPages}
              pageSize={pagination.pageSize}
              total={rows}
              onPageChange={pagination.setPage}
              onPageSizeChange={pagination.setPageSize}
            />
          </CardContent>
        </>
      ) : null}
    </Card>
  );
}

function stamp(iso: string): string {
  // Minute precision: the engine runs on minute bars, and seconds would
  // be three characters of noise on every row.
  return iso.replace("T", " ").slice(0, 16);
}
