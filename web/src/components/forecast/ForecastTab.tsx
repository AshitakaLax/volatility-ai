import { Download, Loader2, Play, Send, Sunrise, TriangleAlert } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Field,
  Select,
} from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { ApiError, api } from "@/lib/api";
import { rememberedOperator } from "@/lib/control";
import {
  activeRun,
  easternTime,
  handOffReport,
  horizonRows,
  inputRows,
  pct,
  pollEvery,
  reportFileName,
  shownRun,
} from "@/lib/forecast";
import { cn } from "@/lib/utils";
import type { ForecastEngineId, ForecastResult, ForecastRun } from "@/types/forecast";
import type { RecordedForecast } from "@/types/riskReport";

/**
 * The pre-market forecast generator, in the page (server/forecast_generator.py,
 * research/forecast_generator/): it fetches the fund's daily history and the
 * overnight inputs from Yahoo and Cboe, runs Chronos-2 (or the historical
 * baseline where requirements-dl.txt is not installed), and shows the risk
 * report it makes beside the inputs it read.
 *
 * Generating writes nothing. "Keep" stores the report in the forecast
 * database through server/risk_forecasts.py, the way the Live page's Check
 * does; "Open in Live" hands it to the Live page's risk report panel, where
 * Check and Apply work exactly as for a pasted report -- so sending a report
 * to a trader still happens in one place.
 */
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

  const engines = status.data?.engines ?? [];
  const chosenEngine =
    engine ?? engines.find((e) => e.id === "chronos" && e.available)?.id ?? "bootstrap";
  const going = activeRun(runs ?? []);
  const shown = shownRun(runs ?? []);

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      await api.startForecast(symbol, chosenEngine);
      status.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setStarting(false);
    }
  };

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
      {status.data && !status.data.can_generate ? (
        <Banner tone="stuck">{status.data.why_not}</Banner>
      ) : null}

      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 pt-5">
          <div className="w-40">
            <Field label="Fund">
              <Select value={symbol} onChange={(event) => setSymbol(event.target.value)}>
                {(status.data?.symbols ?? ["TQQQ"]).map((s) => (
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
          <p className="min-w-0 basis-full text-xs text-muted-foreground">
            {engines.find((e) => e.id === chosenEngine)?.detail}
          </p>
        </CardContent>
      </Card>

      {error ? <Banner tone="loss">{error}</Banner> : null}
      {shown ? <RunCard run={shown} onOpenLive={onOpenLive} /> : null}
    </>
  );
}

function RunCard({ run, onOpenLive }: { run: ForecastRun; onOpenLive: () => void }) {
  if (run.state === "queued" || run.state === "running") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Loader2 className="size-4 animate-spin" />
            {run.symbol} · {run.engine === "chronos" ? "Chronos-2" : "historical baseline"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-1 text-xs text-muted-foreground">
            {run.progress.map((step) => (
              <li key={`${step.at}-${step.message}`}>{step.message}</li>
            ))}
            {run.progress.length === 0 ? <li>Starting…</li> : null}
          </ol>
        </CardContent>
      </Card>
    );
  }
  if (!run.result) {
    return (
      <Banner tone={run.state === "refused" ? "stuck" : "loss"}>
        {run.symbol}: {run.error ?? "the run produced no report"}
      </Banner>
    );
  }
  return <ResultView result={run.result} onOpenLive={onOpenLive} />;
}

function ResultView({ result, onOpenLive }: { result: ForecastResult; onOpenLive: () => void }) {
  const { report, audit, snapshot, diagnostics } = result;
  const signals = report.execution_signals;
  const [kept, setKept] = useState<{ ok: boolean; text: string } | null>(null);
  const [keeping, setKeeping] = useState(false);

  const keep = async () => {
    setKeeping(true);
    try {
      const stored: RecordedForecast = await api.recordRiskForecast(report, rememberedOperator());
      setKept({
        ok: true,
        text: stored.new
          ? `Kept in the forecast database for ${stored.session}.`
          : `Already in the forecast database; ${stored.receipts} receipts.`,
      });
    } catch (cause) {
      setKept({
        ok: false,
        text:
          cause instanceof ApiError || cause instanceof Error ? cause.message : String(cause),
      });
    } finally {
      setKeeping(false);
    }
  };

  const download = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = reportFileName(report);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const openLive = () => {
    if (handOffReport(report)) onOpenLive();
    else setKept({ ok: false, text: "This browser refused the hand-off; download it and paste it on Live." });
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-sm">
              {report.symbol} for {report.target_session}
            </CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Made {easternTime(report.as_of)} ET, anchored to the {snapshot.base_session_date}{" "}
              close ${report.base_price.toFixed(2)} · {report.model}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {audit.ok ? (
              <Badge tone="profit">passes the audit</Badge>
            ) : (
              <Badge tone="loss">fails the audit</Badge>
            )}
            {audit.warnings.length ? <Badge>{audit.warnings.length} warnings</Badge> : null}
            {diagnostics.calibration_status === "uncalibrated" ? <Badge>uncalibrated</Badge> : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Tile label="Expected 1-day move" value={`±${signals.expected_1d_move_pct.toFixed(2)}%`} />
            <Tile label="Regime" value={signals.regime.replaceAll("_", " ")} />
            <Tile label="Volatility" value={signals.volatility_state} />
            <Tile label="Overnight gap risk" value={signals.overnight_gap_risk} />
            <Tile label="Skew" value={signals.skew_bias.replaceAll("_", " ")} />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-medium">Horizon</th>
                  <th className="pb-2 text-right font-medium">5%</th>
                  <th className="pb-2 text-right font-medium">Median</th>
                  <th className="pb-2 text-right font-medium">95%</th>
                  <th className="pb-2 text-right font-medium">P(up)</th>
                  <th className="pb-2 text-right font-medium">ES 5%</th>
                  <th className="pb-2 text-right font-medium">In the bins</th>
                </tr>
              </thead>
              <tbody className="tabular-nums">
                {horizonRows(report).map((row) => (
                  <tr key={row.key} className="border-b border-border/50 last:border-0">
                    <td className="py-1.5">{row.label}</td>
                    <td className="py-1.5 text-right">{pct(row.p05)}</td>
                    <td className="py-1.5 text-right">{pct(row.median)}</td>
                    <td className="py-1.5 text-right">{pct(row.p95)}</td>
                    <td className="py-1.5 text-right">{(row.probPositive * 100).toFixed(1)}%</td>
                    <td className="py-1.5 text-right">{pct(row.es5)}</td>
                    <td
                      className={cn(
                        "py-1.5 text-right",
                        row.binCoverage < 0.9 ? "text-muted-foreground" : "",
                      )}
                    >
                      {(row.binCoverage * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {audit.errors.length ? (
            <ul className="space-y-1 text-xs text-loss">
              {audit.errors.map((f) => (
                <li key={`e-${f.where}`}>
                  {f.where}: {f.message}
                </li>
              ))}
            </ul>
          ) : null}
          {audit.warnings.length ? (
            <details className="text-xs text-muted-foreground">
              <summary className="cursor-pointer">
                {audit.warnings.length} audit {audit.warnings.length === 1 ? "warning" : "warnings"}{" "}
                — shown beside the report, they change nothing it says
              </summary>
              <ul className="mt-1 space-y-1">
                {audit.warnings.map((f) => (
                  <li key={`w-${f.where}`}>
                    {f.where}: {f.message}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={keep} disabled={!audit.ok || keeping}>
              {keeping ? <Loader2 className="size-3.5 animate-spin" /> : null}
              Keep in the forecast database
            </Button>
            <Button variant="outline" onClick={openLive} disabled={!audit.ok}>
              <Send className="size-3.5" />
              Open in Live to check and apply
            </Button>
            <Button variant="outline" onClick={download}>
              <Download className="size-3.5" />
              Download JSON
            </Button>
            {kept ? (
              <span className={cn("text-xs", kept.ok ? "text-muted-foreground" : "text-loss")}>
                {kept.text}
              </span>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">What it read</CardTitle>
          <p className="text-xs text-muted-foreground">
            Shown beside the forecast, never fed to the model: no history exists at the same
            pre-market clock time, so training on these would read the future.
          </p>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <tbody className="tabular-nums">
              {inputRows(snapshot).map((row) => (
                <tr key={row.field} className="border-b border-border/50 last:border-0">
                  <td className="py-1.5">{row.label}</td>
                  <td className="py-1.5 text-right font-medium">
                    {row.missing ? <span className="text-stuck">not read</span> : row.value}
                  </td>
                  <td className="py-1.5 pl-4 text-xs text-muted-foreground">{row.observed}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {snapshot.notes.length ? (
            <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
              {snapshot.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
          <p className="mt-3 text-xs text-muted-foreground">
            {diagnostics.history_observations.toLocaleString()} sessions,{" "}
            {diagnostics.covariates_used.length} covariates,{" "}
            {diagnostics.simulation_paths.toLocaleString()} scenarios
            {diagnostics.engine === "chronos"
              ? `; ${diagnostics.direct_steps} sessions direct, ${diagnostics.extension_steps} extended`
              : ""}
            .
          </p>
        </CardContent>
      </Card>
    </>
  );
}

function Banner({ tone, children }: { tone: "loss" | "stuck"; children: ReactNode }) {
  return (
    <Card>
      <CardContent
        className={cn(
          "flex items-start gap-2 pt-5 text-sm",
          tone === "loss" ? "text-loss" : "text-stuck",
        )}
      >
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
        <span>{children}</span>
      </CardContent>
    </Card>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-semibold capitalize">{value}</div>
    </div>
  );
}
