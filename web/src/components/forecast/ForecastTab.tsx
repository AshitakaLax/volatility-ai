import { CalendarClock, Loader2, Play, Sunrise, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Field,
  Select,
  Skeleton,
} from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import { activeRun, easternTime, pollEvery, shownRun } from "@/lib/forecast";
import { appliedBySha, appliedText, keptRowFor, keptText, modelLabel } from "@/lib/forecastReview";
import { sessionDay } from "@/lib/riskReport";
import type { ForecastEngineId, ForecastRun } from "@/types/forecast";
import type { KeptReport, KeptReportDetail, RiskReportEntry } from "@/types/riskReport";

import { ReportView, type Shown } from "./ReportView";
import { TrackRecord } from "./TrackRecord";

/**
 * The Forecast tab: the next session's report, what a report says about
 * each horizon ahead, and how every report kept has done.
 *
 *   Next session   the report the traders will read for the coming session
 *                  (the forecast database's newest for it: the forecast
 *                  service's 07:45 ET one, yours, or none yet) -- where it
 *                  came from and which traders it went to -- and Generate,
 *                  which runs research/forecast_generator here
 *                  (server/forecast_generator.py; writes nothing).
 *   The report     whichever is open: the next session's by default, a run
 *                  made here and not kept yet, or one picked below. Its
 *                  fan through a year, one horizon in full, the table, what
 *                  came of each horizon, what it read, and Keep / Open in
 *                  Live / Download (lib/forecastReview, ReportView).
 *   Track record   every report kept (server/risk_forecasts.py GET
 *                  .../reports), evening and morning ones both, with how
 *                  often each horizon's close landed in its ranges.
 *
 * "Keep" stores a run's report, and what it read, in the forecast database
 * as the Live page's Check does; "Open in Live" hands a report to the Live
 * page's risk report panel, where Check and Apply work as for a pasted one --
 * so sending a report to a trader still happens in one place.
 */

const KEPT_POLL_MS = 60_000;
const ARCHIVE_POLL_MS = 120_000;
const PAGE = 60;

type Key = { kind: "run"; id: string } | { kind: "kept"; sha256: string };

export function ForecastTab({ onOpenLive }: { onOpenLive: () => void }) {
  const [every, setEvery] = useState(pollEvery(undefined));
  const status = usePolled(api.forecastStatus, every);
  const runs = status.data?.runs;
  // Every 2 s while a run is going, every 30 s otherwise.
  useEffect(() => setEvery(pollEvery(runs)), [runs]);

  const [symbol, setSymbol] = useState("TQQQ");
  const [engine, setEngine] = useState<ForecastEngineId | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE);
  const [picked, setPicked] = useState<Key | null>(null);
  const [compareSha, setCompareSha] = useState<string | null>(null);
  const viewRef = useRef<HTMLDivElement>(null);

  const loadKept = useCallback(() => api.keptReports(symbol, limit), [symbol, limit]);
  const kept = usePolled(loadKept, KEPT_POLL_MS);
  const loadChart = useCallback(() => api.riskForecasts(symbol, 60), [symbol]);
  const chart = usePolled(loadChart, KEPT_POLL_MS);
  const deployments = usePolled(api.deployments, ARCHIVE_POLL_MS);
  const takers = useMemo(
    () =>
      (deployments.data ?? [])
        .filter((d) => d.risk_reports?.takes && (!d.symbol || d.symbol === symbol))
        .map((d) => d.id)
        .sort()
        .join(","),
    [deployments.data, symbol],
  );
  const loadArchives = useCallback(async () => {
    const out: Record<string, RiskReportEntry[]> = {};
    await Promise.all(
      takers
        .split(",")
        .filter(Boolean)
        .map(async (id) => {
          try {
            out[id] = (await api.riskReports(id, 200)).sessions;
          } catch {
            out[id] = [];
          }
        }),
    );
    return out;
  }, [takers]);
  const archives = usePolled(loadArchives, ARCHIVE_POLL_MS);
  const applied = useMemo(() => appliedBySha(archives.data ?? {}), [archives.data]);

  const rows = useMemo(() => kept.data?.reports ?? [], [kept.data]);
  const upcoming = kept.data?.upcoming_session ?? status.data?.target_session ?? null;
  const engines = status.data?.engines ?? [];
  const chosenEngine =
    engine ?? engines.find((e) => e.id === "chronos" && e.available)?.id ?? "bootstrap";
  const going = activeRun(runs ?? []);
  const latest = shownRun(runs ?? []);
  const latestResult = latest?.state === "done" ? latest.result : null;
  const latestKept = latestResult ? keptRowFor(latestResult.report, rows) : undefined;
  const forUpcoming = rows.filter((row) => row.session === upcoming);
  const inForce = forUpcoming.find((row) => row.newest) ?? forUpcoming[0];

  // What is open: what was picked, else a run made here not kept yet, else
  // the next session's report, else the newest kept. A run once kept opens
  // as its kept row.
  const fallback: Key | null =
    latest && latestResult && !latestKept
      ? { kind: "run", id: latest.id }
      : (inForce ?? rows[0])
        ? { kind: "kept", sha256: (inForce ?? rows[0])!.sha256 }
        : null;
  const key = resolve(picked ?? fallback, runs ?? [], rows, fallback);
  const openSha = key?.kind === "kept" ? key.sha256 : null;

  // Each report opened or compared is read whole once (its outcomes come
  // from the polled rows, so a score that arrives overnight still shows).
  const [details, setDetails] = useState<Record<string, KeptReportDetail>>({});
  const [detailError, setDetailError] = useState<string | null>(null);
  const asked = useRef(new Set<string>());
  useEffect(() => {
    for (const sha of [openSha, compareSha]) {
      if (!sha || asked.current.has(sha)) continue;
      asked.current.add(sha);
      api
        .keptReport(sha)
        .then((found) => setDetails((prev) => ({ ...prev, [sha]: found })))
        .catch((cause: unknown) => {
          asked.current.delete(sha);
          setDetailError(cause instanceof Error ? cause.message : String(cause));
        });
    }
  }, [openSha, compareSha]);

  const shown: Shown | null = useMemo(() => {
    if (key?.kind === "run") {
      const run = (runs ?? []).find((r) => r.id === key.id);
      const result = run?.result;
      if (!result) return null;
      return {
        report: result.report,
        session: result.audit.session ?? result.report.target_session,
        row: null,
        inputs: {
          snapshot: result.snapshot,
          diagnostics: result.diagnostics,
          sources: result.sources,
        },
        receipts: [],
        run: result,
      };
    }
    if (key?.kind === "kept") {
      const detail = details[key.sha256];
      if (!detail) return null;
      const row = rows.find((r) => r.sha256 === key.sha256) ?? detail;
      return {
        report: detail.report,
        session: row.session,
        row,
        inputs: detail.inputs,
        receipts: detail.receipts,
        run: null,
      };
    }
    return null;
  }, [key, runs, details, rows]);

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      await api.startForecast(symbol, chosenEngine);
      setPicked(null);
      status.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setStarting(false);
    }
  };

  const chooseSymbol = (next: string) => {
    setSymbol(next);
    setPicked(null);
    setCompareSha(null);
    setLimit(PAGE);
  };

  const openFromHistory = (sha256: string) => {
    setPicked({ kind: "kept", sha256 });
    if (compareSha === sha256) setCompareSha(null);
    window.requestAnimationFrame(() =>
      viewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
    );
  };

  const symbols = [
    ...new Set([...(status.data?.symbols ?? ["TQQQ"]), ...(kept.data?.symbols ?? [])]),
  ].sort();

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Sunrise className="size-4" />
          Forecast
        </h2>
        <span className="text-xs text-muted-foreground">
          {status.data?.target_session
            ? `a report made now is for the ${status.data.target_session} session`
            : status.data
              ? "no report can be made right now"
              : "asking the server…"}
        </span>
      </div>

      {status.error ? <Banner tone="loss">{status.error} — is the API running?</Banner> : null}

      <Card data-testid="next-session">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <CalendarClock className="size-4" />
            Next session{upcoming ? ` · ${sessionDay(upcoming)}` : ""}
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            {inForce ? (
              <>
                {symbol}'s report in force: made {easternTime(inForce.as_of)} ET,{" "}
                {keptText(inForce.receipts)} · {modelLabel(inForce.model)} ·{" "}
                {appliedText(applied.get(inForce.sha256), inForce.receipts)}
                {forUpcoming.length > 1 ? ` (the newest of ${forUpcoming.length})` : ""}.
                {openSha !== inForce.sha256 ? (
                  <>
                    {" "}
                    <button
                      type="button"
                      className="font-medium text-foreground underline underline-offset-2"
                      onClick={() => openFromHistory(inForce.sha256)}
                    >
                      Open it
                    </button>
                  </>
                ) : null}
              </>
            ) : kept.data ? (
              `No ${symbol} report kept for ${sessionDay(upcoming)} yet. The forecast service makes one each trading morning (07:45 ET), or generate one here.`
            ) : (
              "Reading the forecast database…"
            )}
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-40">
              <Field label="Fund">
                <Select value={symbol} onChange={(event) => chooseSymbol(event.target.value)}>
                  {symbols.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <div className="w-56">
              <Field label="Engine">
                <Select
                  value={chosenEngine}
                  onChange={(event) => setEngine(event.target.value as ForecastEngineId)}
                >
                  {engines.map((e) => (
                    <option key={e.id} value={e.id} disabled={!e.available}>
                      {e.label}
                      {e.available ? "" : " (not installed)"}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <Button
              onClick={start}
              disabled={!status.data?.can_generate || Boolean(going) || starting}
            >
              {going || starting ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Play className="size-3.5" />
              )}
              {going ? "Generating…" : "Generate"}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {engines.find((e) => e.id === chosenEngine)?.detail}
            {status.data && !status.data.can_generate && status.data.why_not
              ? ` ${status.data.why_not}`
              : ""}
          </p>
          {going ? <Progress run={going} /> : null}
          {latest && !going && !latest.result ? (
            <Banner tone={latest.state === "refused" ? "stuck" : "loss"}>
              {latest.symbol}: {latest.error ?? "the run produced no report"}
            </Banner>
          ) : null}
          {error ? <Banner tone="loss">{error}</Banner> : null}
        </CardContent>
      </Card>

      <div ref={viewRef} className="scroll-mt-4 space-y-4">
        {shown ? (
          <ReportView
            key={key?.kind === "kept" ? key.sha256 : `run-${key?.id}`}
            shown={shown}
            compareOptions={rows.filter((row) => row.sha256 !== openSha)}
            compareSha={compareSha}
            onCompare={setCompareSha}
            compare={compareSha ? (details[compareSha] ?? null) : null}
            applied={openSha ? applied.get(openSha) : undefined}
            onOpenLive={onOpenLive}
            onKept={() => {
              kept.refresh();
              chart.refresh();
            }}
          />
        ) : openSha ? (
          detailError ? (
            <Banner tone="loss">The report could not be read: {detailError}</Banner>
          ) : (
            <Skeleton className="h-64" />
          )
        ) : null}
      </div>

      <TrackRecord
        rows={rows}
        chart={chart.data}
        chartError={chart.error}
        error={kept.error}
        selectedSha={openSha}
        onSelect={openFromHistory}
        applied={applied}
        canShowMore={rows.length >= limit}
        onShowMore={() => setLimit((n) => n + PAGE)}
      />
    </>
  );
}

/** The key to open: a run made here opens as its kept row once kept, and
 * one no longer listed (or without a report) gives way to the fallback. */
function resolve(
  key: Key | null,
  runs: readonly ForecastRun[],
  rows: readonly KeptReport[],
  fallback: Key | null,
): Key | null {
  if (key?.kind !== "run") return key;
  const run = runs.find((r) => r.id === key.id);
  if (!run?.result) return fallback?.kind === "kept" ? fallback : null;
  const keptAs = keptRowFor(run.result.report, rows);
  return keptAs ? { kind: "kept", sha256: keptAs.sha256 } : key;
}

function Progress({ run }: { run: ForecastRun }) {
  return (
    <div className="rounded-md border border-border p-3">
      <p className="flex items-center gap-2 text-xs font-medium">
        <Loader2 className="size-3.5 animate-spin" />
        {run.symbol} · {run.engine === "chronos" ? "Chronos-2" : "historical baseline"}
      </p>
      <ol className="mt-1 space-y-1 text-xs text-muted-foreground">
        {run.progress.map((step) => (
          <li key={`${step.at}-${step.message}`}>{step.message}</li>
        ))}
        {run.progress.length === 0 ? <li>Starting…</li> : null}
      </ol>
    </div>
  );
}

function Banner({ tone, children }: { tone: "loss" | "stuck"; children: ReactNode }) {
  return (
    <Card>
      <CardContent
        className={
          tone === "loss"
            ? "flex items-start gap-2 pt-5 text-sm text-loss"
            : "flex items-start gap-2 pt-5 text-sm text-stuck"
        }
      >
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
        <span>{children}</span>
      </CardContent>
    </Card>
  );
}
