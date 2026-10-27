import { ListChecks } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { orderRows, outcomeWords, sessionWords, windowWords } from "@/lib/orders";
import { cn, usd } from "@/lib/utils";
import type { OrderEvent, WindowSummary } from "@/types/control";

/**
 * Today's orders, one row each, from the trader's orders journal: the
 * window it was placed in, its limit, what filled and at what price, and how
 * it ended -- filled, cancelled because it rested too long or its window
 * closed, expired, rejected. Outside the regular session every order is a
 * limit that may never fill, so this is where "did it fill?" is answered.
 *
 * Above them, the last window's audit (engine/trading/live_trading_loop.py):
 * when a window ends the trader checks every order it placed there is gone
 * at the venue and the venue's position is the ledger's. A problem halts new
 * buys and is shown here as it was found.
 */
const OUTCOME_TONE = {
  filled: "profit",
  working: "neutral",
  partially_filled: "stuck",
  cancelled: "neutral",
  expired: "neutral",
  rejected: "loss",
} as const;

export function OrdersCard({
  events,
  lastWindow,
}: {
  events: OrderEvent[] | null;
  lastWindow: WindowSummary | null | undefined;
}) {
  const rows = orderRows(events ?? []);
  if (!rows.length && !lastWindow) return null;
  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <ListChecks className="size-4" />
          Orders today
        </CardTitle>
        <span className="text-xs text-muted-foreground">
          {rows.length} order{rows.length === 1 ? "" : "s"}
        </span>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {lastWindow ? (
          <div
            className={cn(
              "rounded-md border p-2 text-xs",
              lastWindow.problem ? "border-loss/50 bg-loss/10" : "border-border bg-secondary/30",
            )}
          >
            <p className="font-medium">Last window — {windowWords(lastWindow)}</p>
            {typeof lastWindow.position === "object" ? (
              <p className="text-muted-foreground">
                Position: venue {lastWindow.position.venue}, ledger {lastWindow.position.ledger}
              </p>
            ) : lastWindow.position ? (
              <p className="text-muted-foreground">Position {lastWindow.position}</p>
            ) : null}
            {lastWindow.problem ? (
              <p className="mt-1 text-loss">{lastWindow.problem}</p>
            ) : null}
          </div>
        ) : null}
        {rows.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-left text-muted-foreground">
                <tr>
                  <th className="py-1 pr-2 font-normal">Placed</th>
                  <th className="py-1 pr-2 font-normal">Side</th>
                  <th className="py-1 pr-2 font-normal">Window</th>
                  <th className="py-1 pr-2 text-right font-normal">Limit</th>
                  <th className="py-1 pr-2 text-right font-normal">Filled</th>
                  <th className="py-1 font-normal">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.order} className="border-t border-border/50">
                    <td className="py-1 pr-2 tabular-nums">
                      {row.placedAt
                        ? new Date(row.placedAt * 1000).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "—"}
                    </td>
                    <td className="py-1 pr-2">{row.kind}</td>
                    <td className="py-1 pr-2">{sessionWords(row.session)}</td>
                    <td className="py-1 pr-2 text-right tabular-nums">
                      {row.limit !== null ? usd(row.limit) : "—"}
                    </td>
                    <td className="py-1 pr-2 text-right tabular-nums">
                      {row.filledQty > 0
                        ? `${row.filledQty}${row.qty ? `/${row.qty}` : ""} @ ${row.avgPrice !== null ? usd(row.avgPrice) : "—"}`
                        : row.qty
                          ? `0/${row.qty}`
                          : "0"}
                    </td>
                    <td className="py-1">
                      <Badge tone={OUTCOME_TONE[row.outcome]}>{outcomeWords(row)}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
