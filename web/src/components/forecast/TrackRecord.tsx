import { History } from "lucide-react";

import { ForecastChart, Swatch } from "@/components/live/ForecastChart";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { landing, signed } from "@/lib/forecastChart";
import {
  appliedText,
  calibration,
  caught,
  easternClock,
  horizonOutcome,
  madeBy,
  modelLabel,
  outcomeText,
  type Applied,
  type ModelRecord,
} from "@/lib/forecastReview";
import { sessionDay } from "@/lib/riskReport";
import { cn } from "@/lib/utils";
import type { KeptReport, RiskForecasts } from "@/types/riskReport";

/**
 * Every report the forecast database keeps, and how each did: how often
 * each horizon's close landed inside its ranges (for the report in force
 * each session and for each model), the Live page's forecast-against-the-
 * close chart, and every report -- a session's evening and morning ones
 * both -- with who made it, what came of it and which traders it went to.
 * A click on a row or a chart column opens that report above.
 */

interface Props {
  rows: KeptReport[];
  chart: RiskForecasts | null;
  chartError: string | null;
  error: string | null;
  selectedSha: string | null;
  onSelect: (sha256: string) => void;
  applied: Map<string, Applied[]>;
  /** More rows were asked for than came back: there may be no more. */
  canShowMore: boolean;
  onShowMore: () => void;
}

export function TrackRecord({
  rows,
  chart,
  chartError,
  error,
  selectedSha,
  onSelect,
  applied,
  canShowMore,
  onShowMore,
}: Props) {
  const { inForce, byModel } = calibration(rows);
  return (
    <Card data-testid="track-record">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <History className="size-4" />
          Track record
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          How often the close landed inside each forecast's range. A forecast that knows its own
          uncertainty puts about 9 in 10 inside its 90% range and half inside its middle 50%; with a
          few sessions, these counts say little yet.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {error ? (
          <p className="text-xs text-loss">The forecast database could not be read: {error}</p>
        ) : null}
        {rows.length ? (
          <>
            <Calibration records={[inForce, ...byModel]} />
            <ForecastChart
              data={chart}
              error={chartError}
              highlight={selectedSha}
              onSelect={onSelect}
            />
            <ReportsTable
              rows={rows}
              selectedSha={selectedSha}
              onSelect={onSelect}
              applied={applied}
            />
            {canShowMore ? (
              <Button variant="outline" onClick={onShowMore}>
                Show older reports
              </Button>
            ) : null}
          </>
        ) : !error ? (
          <p className="rounded-md border border-dashed border-border p-3 text-xs text-muted-foreground">
            No report kept yet. Keep one here, check one on Live, or let the forecast service make
            the morning's; each is scored after its session closes.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Calibration({ records }: { records: ModelRecord[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="tnum w-full min-w-[640px] text-left text-xs">
        <thead className="text-muted-foreground">
          <tr className="border-b border-border">
            <th className="py-1.5 pr-3 font-medium">Reports</th>
            <th className="py-1.5 pr-3 text-right font-medium">Kept</th>
            <th className="py-1.5 pr-3 text-right font-medium">1 day: in 90%</th>
            <th className="py-1.5 pr-3 text-right font-medium">1 day: in 50%</th>
            <th className="py-1.5 pr-3 text-right font-medium">1 week: in 90%</th>
            <th className="py-1.5 pr-3 text-right font-medium">1 month: in 90%</th>
            <th className="py-1.5 text-right font-medium">1 quarter: in 90%</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record, index) => (
            <tr
              key={record.model}
              className={cn(
                "border-b border-border/50 last:border-0",
                index === 0 ? "font-medium" : "",
              )}
            >
              <td className="py-1.5 pr-3">{record.model}</td>
              <td className="py-1.5 pr-3 text-right">{record.reports}</td>
              <td className="py-1.5 pr-3 text-right">{caught(record.horizons.tomorrow, "in90")}</td>
              <td className="py-1.5 pr-3 text-right">{caught(record.horizons.tomorrow, "in50")}</td>
              <td className="py-1.5 pr-3 text-right">
                {caught(record.horizons.next_week, "in90")}
              </td>
              <td className="py-1.5 pr-3 text-right">
                {caught(record.horizons.next_month, "in90")}
              </td>
              <td className="py-1.5 text-right">{caught(record.horizons.next_quarter, "in90")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReportsTable({
  rows,
  selectedSha,
  onSelect,
  applied,
}: {
  rows: KeptReport[];
  selectedSha: string | null;
  onSelect: (sha256: string) => void;
  applied: Map<string, Applied[]>;
}) {
  return (
    <div className="space-y-1" data-testid="every-report">
      <p className="text-sm font-medium">Every report</p>
      <div className="overflow-x-auto">
        <table className="tnum w-full min-w-[880px] text-left text-xs">
          <thead className="text-muted-foreground">
            <tr className="border-b border-border">
              <th className="py-1.5 pr-3 font-medium">Session</th>
              <th className="py-1.5 pr-3 font-medium">Made (ET)</th>
              <th className="py-1.5 pr-3 font-medium">By</th>
              <th className="py-1.5 pr-3 font-medium">Model</th>
              <th className="py-1.5 pr-3 text-right font-medium">1 day: median</th>
              <th className="py-1.5 pr-3 font-medium">90% range</th>
              <th className="py-1.5 pr-3 text-right font-medium">Actual</th>
              <th className="py-1.5 pr-3 font-medium">Landed</th>
              <th className="py-1.5 pr-3 font-medium">1 week</th>
              <th className="py-1.5 font-medium">Traders</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const where = landing(row);
              const weekOutcome = row.horizons?.next_week
                ? horizonOutcome(row, "next_week")
                : undefined;
              const selected = row.sha256 === selectedSha;
              return (
                <tr
                  key={row.sha256}
                  tabIndex={0}
                  aria-selected={selected}
                  onClick={() => onSelect(row.sha256)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(row.sha256);
                    }
                  }}
                  className={cn(
                    "cursor-pointer border-b border-border/50 last:border-0 hover:bg-accent focus-visible:bg-accent focus-visible:outline-none",
                    selected ? "bg-secondary" : "",
                    row.newest ? "" : "text-muted-foreground",
                  )}
                >
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    {sessionDay(row.session)}
                    {row.newest ? "" : " (replaced)"}
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    {new Date(row.as_of).toLocaleDateString("en-US", {
                      timeZone: "America/New_York",
                      month: "short",
                      day: "numeric",
                    })}{" "}
                    {easternClock(row.as_of)}
                  </td>
                  <td className="max-w-40 truncate py-1.5 pr-3">{madeBy(row.receipts)}</td>
                  <td className="max-w-48 truncate py-1.5 pr-3" title={row.model ?? undefined}>
                    {modelLabel(row.model)}
                  </td>
                  <td className="py-1.5 pr-3 text-right">{signed(row.median_pct)}</td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    {signed(row.quantiles.p05)} to {signed(row.quantiles.p95)}
                  </td>
                  <td className="py-1.5 pr-3 text-right">
                    {row.actual ? signed(row.actual.return_pct) : "--"}
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      {where !== "pending" ? <Swatch where={where} /> : null}
                      {outcomeText(
                        { landing: where, return_pct: null, end_session: null },
                        sessionDay,
                      )}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    {weekOutcome && weekOutcome.landing !== "pending" ? (
                      <span className="inline-flex items-center gap-1.5">
                        <Swatch where={weekOutcome.landing} />
                        {signed(weekOutcome.return_pct ?? 0)}
                      </span>
                    ) : (
                      outcomeText(weekOutcome, sessionDay)
                    )}
                  </td>
                  <td
                    className="max-w-56 truncate py-1.5"
                    title={appliedText(applied.get(row.sha256), row.receipts)}
                  >
                    {appliedText(applied.get(row.sha256), row.receipts)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
