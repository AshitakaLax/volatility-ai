import { Package } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { cn, pct, usd } from "@/lib/utils";
import type { InventoryLot } from "@/types/telemetry";

/**
 * The open book, lot by lot.
 *
 * UN-MERGED, DELIBERATELY. A grid accumulates many small positions at
 * different prices, each with its own cost basis and its own resting
 * exit order. Showing an average would hide exactly what an operator
 * needs: which lots are near their target and which are deep under
 * water. The engine never merges them either -- each partial fill opens
 * its own lot, because the increments genuinely executed at different
 * prices and blending them would invent a basis no execution had.
 *
 * Sorted by distance to target, closest first, so the rows most likely
 * to do something next are at the top.
 */

interface Props {
  lots: InventoryLot[];
  /** The loop's own last observed price. null outside market hours. */
  lastPrice: number | null;
}

export function LiveOrderLedger({ lots, lastPrice }: Props) {
  const sorted = [...lots].sort((a, b) => {
    // null (no mark to compare against) sorts last -- it is not "far",
    // it is unknown, and putting it first would push real rows down.
    if (a.distance_to_target === null) return 1;
    if (b.distance_to_target === null) return -1;
    return a.distance_to_target - b.distance_to_target;
  });

  const stuckValue = lots.reduce((total, lot) => total + (lot.current_value ?? 0), 0);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Package className="size-4" />
          Inventory lots
        </CardTitle>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>
            {lots.length} open · {usd(stuckValue, 0)} committed
          </span>
          {lastPrice === null ? (
            <Badge tone="stuck">no mark</Badge>
          ) : (
            <span className="tnum">mark {usd(lastPrice)}</span>
          )}
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {lots.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No open lots. Either nothing has been bought yet, or every lot has been
            harvested — both are ordinary states, not errors.
          </p>
        ) : (
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Lot</th>
                <th className="pb-2 text-right font-medium">Shares</th>
                <th className="pb-2 text-right font-medium">Buy</th>
                <th className="pb-2 text-right font-medium">Value</th>
                <th className="pb-2 text-right font-medium">Target</th>
                <th className="pb-2 text-right font-medium">To target</th>
                <th className="pb-2 text-right font-medium">Below mark</th>
              </tr>
            </thead>
            <tbody className="tnum">
              {sorted.map((lot) => {
                const distance = lot.distance_to_target;
                // Zero is "already there", which is a real and different
                // state from null ("no price to compare against").
                const reached = distance !== null && distance <= 0;
                return (
                  <tr key={lot.order_id} className="border-b border-border/50 last:border-0">
                    <td className="py-2 font-mono text-xs">{lot.order_id}</td>
                    <td className="py-2 text-right">{lot.shares.toFixed(4)}</td>
                    <td className="py-2 text-right">{usd(lot.buy_price)}</td>
                    <td className="py-2 text-right">{usd(lot.current_value)}</td>
                    <td className="py-2 text-right">{usd(lot.target_sell_price)}</td>
                    <td
                      className={cn(
                        "py-2 text-right font-medium",
                        reached && "text-profit",
                        distance !== null && distance > 0.02 && "text-stuck",
                      )}
                    >
                      {distance === null ? "--" : reached ? "at target" : pct(distance * 100)}
                    </td>
                    <td className="py-2 text-right text-muted-foreground">
                      {lot.distance_to_next_step === null
                        ? "--"
                        : pct(lot.distance_to_next_step * 100, 2, true)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}
