import { TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle, Skeleton } from "@/components/ui/primitives";
import { useNow } from "@/hooks/useNow";
import { api } from "@/lib/api";
import { duration } from "@/lib/fidelity";
import { performance, type PerformanceRow, type Tracking } from "@/lib/performance";
import { cn, usd } from "@/lib/utils";
import type { TraderFill } from "@/types/control";

/**
 * How the deployment has done over time: realised profit each session and
 * running, and -- where the `tracking` service has recorded it -- the
 * backtest of the same algorithm on the same days beside it, the share of
 * orders that filled, and how long a Fidelity bridge was not ready.
 *
 * Realised profit, not account value: the ledger keeps no history of its
 * own worth, and open lots are on the cards above. The shadow is today's
 * algorithm over every tracked session, started from cash on the first
 * (tools/track_live.py says what that does and does not mean).
 */
const POLL_MS = 5 * 60_000;
const JOURNAL_SESSIONS = 10;

interface Props {
  deploymentId: string;
}

export function PerformanceCard({ deploymentId }: Props) {
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [fills, setFills] = useState<TraderFill[] | null>(null);

  useEffect(() => {
    setTracking(null);
    setFills(null);
    let cancelled = false;
    const load = () => {
      // A server older than the tracking route answers 404: the journal alone then.
      api
        .deploymentTracking(deploymentId)
        .catch((): Tracking => ({ sessions: [], updated_at: null }))
        .then((next) => {
          if (!cancelled) setTracking(next);
        });
      api
        .deploymentFills(deploymentId, JOURNAL_SESSIONS)
        .catch((): TraderFill[] => [])
        .then((next) => {
          if (!cancelled) setFills(next);
        });
    };
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [deploymentId]);

  const result = useMemo(
    () => (tracking && fills ? performance(tracking.sessions, fills) : null),
    [tracking, fills],
  );
  const now = useNow(60_000);
  const recorded = tracking?.updated_at
    ? `tracking record written ${duration(now / 1000 - tracking.updated_at)} ago`
    : "from the trader's journal: its newest sessions only";

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="size-4" />
          Performance
          {result && result.rows.length ? (
            <span className="font-normal text-muted-foreground">
              · {result.rows.length} session{result.rows.length === 1 ? "" : "s"}
            </span>
          ) : null}
        </CardTitle>
        <span className="text-xs text-muted-foreground">{recorded}</span>
      </CardHeader>
      <CardContent className="space-y-4">
        {result === null ? (
          <Skeleton className="h-40" />
        ) : result.rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No sessions recorded yet. Trades appear here from the trader's journal as it books
            them; the daily <code>tracking</code> service adds the backtest of the same days.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3 lg:grid-cols-6">
              <Stat label="Realised" value={usd(result.realized)} sign={result.realized} />
              <Stat
                label="Sessions up / down"
                value={`${result.winning} / ${result.losing}`}
                note={result.missed ? `${result.missed} missed` : undefined}
              />
              <Stat label="Buys · sells" value={`${result.buys} · ${result.sells}`} />
              <Stat
                label="Best · worst session"
                value={`${result.best ? usd(result.best.realized, 0) : "--"} · ${
                  result.worst ? usd(result.worst.realized, 0) : "--"
                }`}
              />
              <Stat
                label="Backtest, same days"
                value={result.shadow ? usd(result.shadow.shadow) : "--"}
                note={
                  result.shadow
                    ? `live ${usd(result.shadow.live)} over ${result.shadow.sessions} sessions`
                    : "not tracked yet"
                }
              />
              <Stat
                label="Orders filled"
                value={result.fillShare === null ? "--" : `${(result.fillShare * 100).toFixed(0)}%`}
                note={
                  result.notReadyMinutes === null
                    ? undefined
                    : `bridge not ready ${duration(result.notReadyMinutes * 60)} of regular hours`
                }
              />
            </div>
            <Chart rows={result.rows} />
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <Key className="bg-profit" label="session realised" />
              <Key className="bg-foreground" label="running, live" />
              {result.shadow ? <Key className="bg-stuck" label="running, backtest of the same days" /> : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  note,
  sign,
}: {
  label: string;
  value: string;
  note?: string | undefined;
  sign?: number;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "tnum text-base font-semibold",
          sign !== undefined && sign > 0 && "text-profit",
          sign !== undefined && sign < 0 && "text-loss",
        )}
      >
        {value}
      </span>
      {note ? <span className="text-xs text-muted-foreground">{note}</span> : null}
    </div>
  );
}

function Key({ className, label }: { className: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("inline-block h-0.5 w-4 rounded", className)} />
      {label}
    </span>
  );
}

const WIDTH = 1000;
const HEIGHT = 220;
const PAD = { top: 10, right: 12, bottom: 22, left: 12 };

/** Bars for each session's realised profit, lines for the running totals. */
function Chart({ rows }: { rows: PerformanceRow[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const values = rows.flatMap((row) => [row.realized, row.running, row.shadowRunning ?? 0]);
  const top = Math.max(0, ...values);
  const bottom = Math.min(0, ...values);
  const span = top - bottom || 1;
  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const slot = plotWidth / rows.length;
  const x = (index: number) => PAD.left + slot * (index + 0.5);
  const y = (value: number) => PAD.top + ((top - value) / span) * plotHeight;
  const line = (pick: (row: PerformanceRow) => number | null) =>
    rows
      .map((row, index) => [index, pick(row)] as const)
      .filter((point): point is readonly [number, number] => point[1] !== null)
      .map(([index, value], i) => `${i ? "L" : "M"}${x(index).toFixed(1)},${y(value).toFixed(1)}`)
      .join(" ");
  const barWidth = Math.max(1, Math.min(28, slot * 0.6));
  const shown = hover === null ? null : rows[hover];
  const first = rows[0]?.session;
  const last = rows[rows.length - 1]?.session;

  return (
    <div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-52 w-full"
        preserveAspectRatio="none"
        role="img"
        aria-label={`Realised profit by session from ${first} to ${last}`}
        onMouseLeave={() => setHover(null)}
        onMouseMove={(event) => {
          const box = event.currentTarget.getBoundingClientRect();
          const at = ((event.clientX - box.left) / box.width) * WIDTH - PAD.left;
          setHover(Math.max(0, Math.min(rows.length - 1, Math.floor(at / slot))));
        }}
      >
        <line
          x1={PAD.left}
          x2={WIDTH - PAD.right}
          y1={y(0)}
          y2={y(0)}
          className="stroke-border"
          vectorEffect="non-scaling-stroke"
        />
        {rows.map((row, index) => (
          <rect
            key={row.session}
            x={x(index) - barWidth / 2}
            width={barWidth}
            y={Math.min(y(row.realized), y(0))}
            height={Math.max(Math.abs(y(row.realized) - y(0)), row.realized === 0 ? 0 : 1)}
            className={cn(row.realized < 0 ? "fill-loss/70" : "fill-profit/70", hover === index && "opacity-60")}
          />
        ))}
        <path
          d={line((row) => row.shadowRunning)}
          fill="none"
          className="stroke-stuck"
          strokeWidth={1.5}
          strokeDasharray="5 4"
          vectorEffect="non-scaling-stroke"
        />
        <path
          d={line((row) => row.running)}
          fill="none"
          className="stroke-foreground"
          strokeWidth={1.75}
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="tnum flex min-h-5 flex-wrap justify-between gap-x-4 text-xs text-muted-foreground">
        {shown ? (
          <span>
            <span className="text-foreground">{shown.session}</span> · {shown.buys} buys ·{" "}
            {shown.sells} sells · realised {usd(shown.realized)} · running {usd(shown.running)}
            {shown.shadowRealized !== null ? ` · backtest ${usd(shown.shadowRealized)}` : ""}
            {shown.status && shown.status !== "traded" ? ` · ${shown.status}` : ""}
          </span>
        ) : (
          <>
            <span>{first}</span>
            <span>{last}</span>
          </>
        )}
      </div>
    </div>
  );
}
