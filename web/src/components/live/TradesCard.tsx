import { ArrowLeftRight } from "lucide-react";
import { useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { tradeTotals } from "@/lib/control";
import { cn, usd } from "@/lib/utils";
import type { TraderFill } from "@/types/control";

/**
 * What the trader bought and sold, newest first, from its fill journal --
 * each sale with what it fetched against what its lot cost. The ledger
 * cannot say that (it keeps lots, never a sale's price), which is why this
 * reads the trader's own record of each fill as it booked it.
 *
 * A sale realising a loss is shown as one: only Ultimate's regime exit may
 * (the two-key signal exit), and hiding it among the harvests would hide the
 * one distinction the no-loss design is built around.
 */
interface Props {
  fills: TraderFill[] | null;
  /** Sessions the fills cover. */
  sessions: number;
  onSessions: (sessions: number) => void;
}

const SHOWN = 50;

export function TradesCard({ fills, sessions, onSessions }: Props) {
  const [all, setAll] = useState(false);
  const rows = [...(fills ?? [])].reverse();
  const totals = tradeTotals(fills ?? []);
  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <ArrowLeftRight className="size-4" />
          Trades
        </CardTitle>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>
            {totals.buys} buys ({usd(totals.bought, 0)}) · {totals.sells} sells · realised{" "}
            <span className={cn(totals.realized > 0 && "text-profit", totals.realized < 0 && "text-loss")}>
              {usd(totals.realized)}
            </span>
          </span>
          <select
            className="rounded border border-border bg-background px-1 py-0.5"
            value={sessions}
            onChange={(event) => onSessions(Number(event.currentTarget.value))}
          >
            <option value={1}>today</option>
            <option value={5}>5 sessions</option>
            <option value={10}>10 sessions</option>
          </select>
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {fills === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No fills recorded in this window. The trader journals every fill from the session
            after this build reaches it.
          </p>
        ) : (
          <>
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-medium">Time</th>
                  <th className="pb-2 font-medium">Side</th>
                  <th className="pb-2 text-right font-medium">Shares</th>
                  <th className="pb-2 text-right font-medium">Price</th>
                  <th className="pb-2 text-right font-medium">Value</th>
                  <th className="pb-2 text-right font-medium">Realised</th>
                </tr>
              </thead>
              <tbody>
                {(all ? rows : rows.slice(0, SHOWN)).map((fill, index) => (
                  <tr key={`${fill.t}-${fill.lot}-${index}`} className="border-b border-border/50 last:border-0">
                    <td className="py-1.5 text-xs text-muted-foreground">
                      {new Date(fill.t * 1000).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-1.5">
                      {fill.side === "buy" ? (
                        <Badge>buy</Badge>
                      ) : fill.reason === "signal_exit" ? (
                        <Badge tone="stuck" title="Ultimate's regime exit">
                          regime exit
                        </Badge>
                      ) : (
                        <Badge tone="profit">sell</Badge>
                      )}
                    </td>
                    <td className="tnum py-1.5 text-right">{fill.qty.toFixed(4)}</td>
                    <td className="tnum py-1.5 text-right">{usd(fill.price)}</td>
                    <td className="tnum py-1.5 text-right">
                      {usd(fill.side === "buy" ? (fill.value ?? null) : (fill.proceeds ?? null))}
                    </td>
                    <td
                      className={cn(
                        "tnum py-1.5 text-right",
                        (fill.pnl ?? 0) > 0 && "text-profit",
                        (fill.pnl ?? 0) < 0 && "text-loss",
                      )}
                    >
                      {fill.side === "sell" ? usd(fill.pnl ?? null) : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length > SHOWN && !all ? (
              <button
                type="button"
                className="mt-2 text-xs text-muted-foreground underline"
                onClick={() => setAll(true)}
              >
                Show all {rows.length}
              </button>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
