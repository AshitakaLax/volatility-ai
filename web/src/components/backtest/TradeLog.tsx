import { ChevronDown, ChevronRight, Download, ListOrdered } from "lucide-react";
import { useState } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { buildCycles } from "@/lib/filters";
import { cn, usd } from "@/lib/utils";
import type { BacktestExecution } from "@/types/backtest";

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
 * TWO VIEWS OF THE SAME DATA:
 *
 *   fills   every buy and sell as the engine recorded it.
 *   cycles  one row per lot -- entry, exit, hold, realised P&L. This is
 *           the one that answers "what did this trade actually make",
 *           which a flat fill list cannot without mental joining.
 */

interface Props {
  executions: BacktestExecution[];
  /** For the header, so a reader knows the log respects the filters. */
  totalBeforeFilters: number;
  /**
   * The run's profit target, as a fraction, so an open lot can show the
   * price it is waiting for. Passed rather than derived: the execution
   * carries no target, and computing one from an assumed value would
   * name a price no resting order is at.
   */
  profitTarget: number;
}

// Enough to scroll through and see the shape; past this a table stops
// being something a person reads. The count is always stated so the cap
// is visible rather than silently truncating.
const MAX_ROWS = 500;

type View = "fills" | "cycles";

export function TradeLog({ executions, totalBeforeFilters, profitTarget }: Props) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<View>("cycles");

  const cycles = buildCycles(executions);
  const closed = cycles.filter((cycle) => !cycle.open);
  const stuck = cycles.filter((cycle) => cycle.open);
  const realised = closed.reduce((total, cycle) => total + (cycle.realized ?? 0), 0);

  const rows = view === "fills" ? executions.length : cycles.length;

  return (
    <Card>
      <CardHeader
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
            {executions.length} fill{executions.length === 1 ? "" : "s"}
            {executions.length !== totalBeforeFilters
              ? ` of ${totalBeforeFilters}, filtered`
              : ""}
          </span>
          <span>
            {closed.length} closed · {stuck.length} open
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
            <Button
              variant="ghost"
              className="ml-auto h-7 px-2 text-xs"
              onClick={() => download(executions)}
              title="Download the filtered fills as CSV"
            >
              <Download className="size-3.5" />
              CSV
            </Button>
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
                  {cycles.slice(0, MAX_ROWS).map((cycle) => {
                    const exit = cycle.sells[cycle.sells.length - 1];
                    return (
                      <tr key={cycle.lotId} className="border-b border-border/50 last:border-0">
                        <td className="py-1.5 font-mono text-xs">{cycle.lotId}</td>
                        <td className="py-1.5 text-xs">{stamp(cycle.buy.timestamp)}</td>
                        <td className="py-1.5 text-right">{usd(cycle.buy.price, 4)}</td>
                        <td className="py-1.5 text-right">{cycle.buy.shares.toFixed(4)}</td>
                        <td className="py-1.5 text-right text-muted-foreground">
                          {/* Absent inside the indicator's warmup. Not
                              zero, which would read as extremely
                              oversold. */}
                          {cycle.buy.rsi_at_entry?.toFixed(1) ?? "--"}
                        </td>
                        <td className="py-1.5 text-xs">
                          {exit ? (
                            stamp(exit.timestamp)
                          ) : (
                            <span className="text-stuck">still open</span>
                          )}
                        </td>
                        <td className="py-1.5 text-right">{exit ? usd(exit.price, 4) : "--"}</td>
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
                          {exit?.sell_reason === "signal_exit" ? (
                            <Badge tone="loss">signal exit</Badge>
                          ) : exit ? (
                            <span className="text-muted-foreground">target</span>
                          ) : (
                            <span className="text-muted-foreground">
                              waiting for {usd(cycle.buy.price * (1 + profitTarget), 4)}
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
                  {executions.slice(0, MAX_ROWS).map((execution) => (
                    <tr
                      key={execution.order_id}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="py-1.5 text-xs">{stamp(execution.timestamp)}</td>
                      <td className="py-1.5">
                        <Badge tone={execution.type === "BUY" ? "neutral" : "profit"}>
                          {execution.type}
                        </Badge>
                      </td>
                      <td className="py-1.5 font-mono text-xs text-muted-foreground">
                        {execution.matched_buy_id ?? execution.order_id.split("-buy-")[0]}
                      </td>
                      <td className="py-1.5 text-right">{usd(execution.price, 4)}</td>
                      <td className="py-1.5 text-right">{execution.shares.toFixed(4)}</td>
                      <td className="py-1.5 text-right text-muted-foreground">
                        {usd(execution.price * execution.shares)}
                      </td>
                      <td className="py-1.5 text-right text-muted-foreground">
                        {execution.rsi_at_entry?.toFixed(1) ?? "--"}
                      </td>
                      <td
                        className={cn(
                          "py-1.5 text-right",
                          (execution.profit_realized ?? 0) > 0 && "text-profit",
                          (execution.profit_realized ?? 0) < 0 && "text-loss",
                        )}
                      >
                        {execution.profit_realized === undefined
                          ? "--"
                          : usd(execution.profit_realized)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {rows > MAX_ROWS ? (
              <p className="mt-3 text-xs text-muted-foreground">
                Showing the first {MAX_ROWS} of {rows}. Narrow the date range, or use the
                CSV, which is not capped.
              </p>
            ) : null}
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

function download(executions: BacktestExecution[]): void {
  const header = [
    "timestamp",
    "type",
    "lot_id",
    "ticker",
    "price",
    "shares",
    "rsi_at_entry",
    "profit_realized",
    "sell_reason",
  ];
  const lines = executions.map((execution) =>
    [
      execution.timestamp,
      execution.type,
      execution.matched_buy_id ?? execution.order_id.split("-buy-")[0] ?? "",
      execution.ticker,
      execution.price,
      execution.shares,
      // Empty, not 0. A spreadsheet that read a warmup bar as RSI 0
      // would filter it as extremely oversold.
      execution.rsi_at_entry ?? "",
      execution.profit_realized ?? "",
      execution.sell_reason ?? "",
    ].join(","),
  );
  const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "trades.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}
