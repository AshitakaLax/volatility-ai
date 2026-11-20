import { CalendarClock } from "lucide-react";
import { useCallback } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import { levers, percent, sessionDay, tierLabel, tierTone } from "@/lib/riskReport";

/**
 * One deployment's nightly risk reports: the overlay its next session would
 * trade under (or "no report: trading as configured"), then the sessions its
 * trader archived -- the tier, the step and the week's cap, who sent each
 * report and what came of it. Read from GET .../risk-reports (server/live.py,
 * the trader's risk_reports/). How each suggestion was followed, and what
 * the shadows say it cost or saved, is in the tracking columns once the
 * tracking service has scored it.
 */

const POLL_MS = 30000;

const FOLLOWED: Record<string, string> = {
  followed: "followed",
  late: "followed late",
  not_followed: "not followed",
  not_actionable: "no button",
  enforced: "enforced",
};

export function RiskReportHistory({ deploymentId }: { deploymentId: string }) {
  const load = useCallback(() => api.riskReports(deploymentId, 20), [deploymentId]);
  const loadTracking = useCallback(() => api.deploymentTracking(deploymentId, 40), [deploymentId]);
  const reports = usePolled(load, POLL_MS);
  const tracking = usePolled(loadTracking, POLL_MS * 4);
  const scored = new Map((tracking.data?.sessions ?? []).map((row) => [row.session, row.risk ?? null]));
  const data = reports.data;
  if (!data?.settings) return null;
  const next = data.next;

  return (
    <Card data-testid="risk-report-history">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="size-4" />
          Risk reports
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge>{data.settings.mode}</Badge>
          <Badge>mapping {data.settings.mapping}</Badge>
          {!data.takes ? <Badge tone="stuck">{data.why_not}</Badge> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {next ? (
          <div className="rounded-md border border-border bg-secondary/30 p-3 text-sm">
            <p>
              <span className="text-muted-foreground">{sessionDay(next.session)}: </span>
              {next.has_report || levers(next.overlay).length ? next.summary : "no report: trading as configured"}
            </p>
            {data.settings.mode === "advisory" && next.has_report ? (
              <p className="mt-1 text-xs text-muted-foreground">
                Advisory: shown and logged, not traded. A suggested pause is yours to make with Pause buys.
              </p>
            ) : null}
          </div>
        ) : null}
        {data.sessions.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="py-1 pr-3 font-medium">Session</th>
                  <th className="py-1 pr-3 font-medium">Tier</th>
                  <th className="py-1 pr-3 font-medium">Step</th>
                  <th className="py-1 pr-3 font-medium">Week&apos;s cap</th>
                  <th className="py-1 pr-3 font-medium">Outcome</th>
                  <th className="py-1 pr-3 font-medium">Followed</th>
                  <th className="py-1 pr-3 font-medium">Forecast</th>
                  <th className="py-1 pr-3 font-medium">From</th>
                </tr>
              </thead>
              <tbody>
                {data.sessions.map((row) => (
                  <tr key={`${row.session}-${row.sha256}`} className="border-t border-border align-top">
                    <td className="py-1 pr-3 whitespace-nowrap">{sessionDay(row.session)}</td>
                    <td className="py-1 pr-3">
                      <Badge tone={tierTone(row.tier, row.abstained)}>{tierLabel(row.tier, row.abstained)}</Badge>
                    </td>
                    <td className="py-1 pr-3 tnum">×{(row.overlay?.step_multiplier ?? 1).toFixed(1)}</td>
                    <td className="py-1 pr-3 tnum">{percent(row.overlay?.weekly_ceiling ?? null)}</td>
                    <td className="py-1 pr-3" title={row.summary}>
                      {row.outcome.replace("_", " ")}
                      {row.receipts.length > 1 ? ` (${row.receipts.length} received)` : ""}
                    </td>
                    <td className="py-1 pr-3">{FOLLOWED[scored.get(row.session)?.followed ?? ""] ?? "--"}</td>
                    <td className="py-1 pr-3 tnum" title="the session's return against the report's 90% interval">
                      {forecast(scored.get(row.session)?.score)}
                    </td>
                    <td className="py-1 pr-3 whitespace-nowrap text-muted-foreground">
                      {row.operator} · {new Date(row.received_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">No report archived yet. A session without one trades as configured.</p>
        )}
        {reports.error ? <p className="text-xs text-loss">{reports.error}</p> : null}
      </CardContent>
    </Card>
  );
}

function forecast(score: { return_pct: number; in_90: boolean } | null | undefined): string {
  if (!score) return "--";
  const sign = score.return_pct >= 0 ? "+" : "";
  return `${sign}${score.return_pct.toFixed(1)}% ${score.in_90 ? "inside" : "outside"} its 90%`;
}
