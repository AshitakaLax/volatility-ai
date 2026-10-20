import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { cn, pct } from "@/lib/utils";
import { bytes, freshness, whole } from "@/lib/warehouse";
import type { FundRow } from "@/types/warehouse";

/**
 * Every fund: what the warehouse holds of it, how far behind that is, and
 * how much research has run on it.
 *
 * "Behind" counts NYSE sessions after the fund's last complete one, through
 * the last session that has closed. "Bars to add" is an estimate -- those
 * sessions times the fund's own median bars per session over its last 20
 * -- because funds differ: an extended-hours fund prints ~940 a session, a
 * thinly traded one well under 390.
 */
export function FundsTable({ funds, through }: { funds: FundRow[]; through: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Funds</CardTitle>
        <p className="text-xs text-muted-foreground">
          Up to date means every bar through {through}, the last completed NYSE session. Bars to
          add is an estimate: the sessions missing times the fund&apos;s median bars per session
          over its last 20. Simulations on older bars ran before the fund&apos;s bars last changed.
        </p>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[1180px] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="pb-2 font-medium">Fund</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 text-right font-medium">Behind</th>
              <th className="pb-2 text-right font-medium">≈ Bars to add</th>
              <th className="pb-2 text-right font-medium">Bars</th>
              <th className="pb-2 font-medium">First</th>
              <th className="pb-2 font-medium">Last session</th>
              <th className="pb-2 text-right font-medium">Sessions</th>
              <th className="pb-2 text-right font-medium">Bars / session</th>
              <th className="pb-2 text-right font-medium">Duplicates</th>
              <th className="pb-2 text-right font-medium">Size</th>
              <th className="pb-2 text-right font-medium">Sweeps</th>
              <th className="pb-2 text-right font-medium">Simulations</th>
              <th className="pb-2 text-right font-medium">On older bars</th>
              <th className="pb-2 text-right font-medium">Best return</th>
            </tr>
          </thead>
          <tbody>
            {funds.map((fund) => {
              const badge = freshness(fund);
              return (
                <tr key={fund.ticker} className="border-b border-border/50 last:border-0">
                  <td className="py-2">
                    <div className="font-medium">{fund.ticker}</div>
                    <div className="text-xs text-muted-foreground">
                      {[
                        fund.leverage !== null && fund.leverage !== 1 ? `${fund.leverage}x` : null,
                        fund.sector,
                        fund.known ? null : "not in the fund registry",
                      ]
                        .filter(Boolean)
                        .join(" · ") || "--"}
                    </div>
                  </td>
                  <td className="py-2">
                    <Badge tone={badge.tone}>{badge.label}</Badge>
                  </td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.sessions_behind)}</td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.bars_to_add)}</td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.bars)}</td>
                  <td className="py-2 text-xs">{fund.first?.slice(0, 10) ?? "--"}</td>
                  <td className="py-2 text-xs">{fund.last_session ?? "--"}</td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.sessions)}</td>
                  <td className="py-2 text-right tabular-nums">
                    {whole(fund.bars_per_session)}
                  </td>
                  <td
                    className={cn(
                      "py-2 text-right tabular-nums",
                      fund.duplicates ? "font-semibold text-loss" : "",
                    )}
                    title={
                      fund.duplicates
                        ? "Rows beyond one per minute: an ingest appended bars already held"
                        : undefined
                    }
                  >
                    {whole(fund.duplicates)}
                  </td>
                  <td className="py-2 text-right tabular-nums">{bytes(fund.bytes)}</td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.sweeps)}</td>
                  <td className="py-2 text-right tabular-nums">{whole(fund.simulations)}</td>
                  <td
                    className={cn(
                      "py-2 text-right tabular-nums",
                      fund.older_simulations ? "text-stuck" : "text-muted-foreground",
                    )}
                  >
                    {whole(fund.older_simulations)}
                  </td>
                  <td className="py-2 text-right font-semibold tabular-nums">
                    {pct(fund.best_return, 1, true)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
