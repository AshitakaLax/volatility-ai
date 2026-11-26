import { Download, Loader2, Send } from "lucide-react";
import { useState } from "react";

import { Swatch } from "@/components/live/ForecastChart";
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
import { ApiError, api } from "@/lib/api";
import { rememberedOperator } from "@/lib/control";
import {
  easternTime,
  handOffReport,
  horizonRows,
  inputRows,
  pct,
  reportFileName,
} from "@/lib/forecast";
import {
  HORIZON_LABEL,
  appliedText,
  dollars,
  fanPoints,
  inUnit,
  keptText,
  modelLabel,
  outcomeText,
  outcomes,
  reportName,
  type Applied,
  type Unit,
} from "@/lib/forecastReview";
import { sessionDay } from "@/lib/riskReport";
import { cn } from "@/lib/utils";
import {
  HORIZON_KEYS,
  type ForecastResult,
  type GeneratedReport,
  type HorizonKey,
} from "@/types/forecast";
import type { ForecastReceipt, KeptInputs, KeptReport, KeptReportDetail } from "@/types/riskReport";

import { DistributionChart } from "./DistributionChart";
import { FanChart } from "./FanChart";

/**
 * One report, kept or just made here: what it says about each horizon (the
 * fan, one horizon's whole distribution, the table), what came of each once
 * its close is in, what the generator read for it, and the actions -- Keep
 * (a run not kept yet), Open in Live to check and apply, Download.
 */

export interface Shown {
  report: GeneratedReport;
  session: string;
  /** Its row in the forecast database; null for a run not kept yet. */
  row: KeptReport | null;
  inputs: KeptInputs | null;
  receipts: ForecastReceipt[];
  /** A run made here and not kept yet: its audit, and Keep. */
  run: ForecastResult | null;
}

interface Props {
  shown: Shown;
  compareOptions: KeptReport[];
  compareSha: string | null;
  onCompare: (sha256: string | null) => void;
  compare: KeptReportDetail | null;
  applied: Applied[] | undefined;
  onOpenLive: () => void;
  onKept: () => void;
}

const THROUGH: HorizonKey[] = ["next_week", "next_month", "next_quarter", "next_year"];

export function ReportView({
  shown,
  compareOptions,
  compareSha,
  onCompare,
  compare,
  applied,
  onOpenLive,
  onKept,
}: Props) {
  const { report, row, run } = shown;
  const [unit, setUnit] = useState<Unit>("pct");
  const [through, setThrough] = useState<HorizonKey>("next_quarter");
  const [horizon, setHorizon] = useState<HorizonKey>("tomorrow");
  const landed = outcomes(row);
  const signals = report.execution_signals;
  const comparing = compare && compare.sha256 === compareSha ? compare : null;

  return (
    <>
      <Card data-testid="report-view">
        <CardHeader className="flex-row flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-1">
            <CardTitle className="text-sm">
              {report.symbol} for {sessionDay(shown.session)}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Made {easternTime(report.as_of)} ET ·{" "}
              {shown.receipts.length ? keptText(shown.receipts) : "made here"} ·{" "}
              {modelLabel(report.model)} · from the {dollars(report.base_price)} close
            </p>
            <p className="text-xs text-muted-foreground">
              {row
                ? appliedText(applied, shown.receipts)
                : "Not kept yet: keep it to score it after the close."}
            </p>
            <p className="truncate text-[11px] text-muted-foreground/80" title={report.model}>
              {report.model}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {run ? (
              run.audit.ok ? (
                <Badge tone="profit">passes the audit</Badge>
              ) : (
                <Badge tone="loss">fails the audit</Badge>
              )
            ) : null}
            {row && !row.newest ? <Badge>a later report replaced it</Badge> : null}
            {row && row.reports > 1 && row.newest ? (
              <Badge>newest of {row.reports} for its session</Badge>
            ) : null}
            {(run?.audit.warnings.length ?? row?.warnings ?? 0) > 0 ? (
              <Badge>{run?.audit.warnings.length ?? row?.warnings} audit warnings</Badge>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Tile
              label="Expected 1-day move"
              value={`±${signals.expected_1d_move_pct.toFixed(2)}%`}
            />
            <Tile label="Regime" value={signals.regime.replaceAll("_", " ")} />
            <Tile label="Volatility" value={signals.volatility_state} />
            <Tile label="Overnight gap risk" value={signals.overnight_gap_risk} />
            <Tile label="Skew" value={signals.skew_bias.replaceAll("_", " ")} />
          </div>

          <section className="space-y-3" aria-label="Looking ahead">
            <div className="flex flex-wrap items-end gap-3">
              <p className="mr-auto text-sm font-medium">Looking ahead</p>
              <div
                className="flex rounded-md border border-border p-0.5"
                role="group"
                aria-label="Show as"
              >
                {(["pct", "price"] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={unit === value}
                    onClick={() => setUnit(value)}
                    className={cn(
                      "rounded px-2.5 py-1 text-xs",
                      unit === value
                        ? "bg-secondary font-medium text-foreground"
                        : "text-muted-foreground",
                    )}
                  >
                    {value === "pct" ? "% return" : "$ price"}
                  </button>
                ))}
              </div>
              <div className="w-32">
                <Field label="Through">
                  <Select
                    value={through}
                    onChange={(event) => setThrough(event.target.value as HorizonKey)}
                  >
                    {THROUGH.map((key) => (
                      <option key={key} value={key}>
                        {HORIZON_LABEL[key]}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <div className="w-full min-w-0 sm:w-72">
                <Field label="Compare with">
                  <Select
                    value={compareSha ?? ""}
                    onChange={(event) => onCompare(event.target.value || null)}
                  >
                    <option value="">nothing</option>
                    {compareOptions.map((option) => (
                      <option key={option.sha256} value={option.sha256}>
                        {reportName(option)}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
            </div>
            <FanChart
              subject={{
                label: "This report",
                report,
                points: fanPoints(report, through, unit),
              }}
              compare={
                comparing
                  ? {
                      label: reportName(comparing),
                      report: comparing.report,
                      points: fanPoints(comparing.report, through, unit),
                    }
                  : null
              }
              unit={unit}
              outcomes={landed}
              selected={horizon}
              onSelect={setHorizon}
              endOf={(key) => landed?.[key]?.end_session ?? null}
              day={sessionDay}
            />
            {unit === "price" && comparing ? (
              <p className="text-xs text-muted-foreground">
                Each report's prices start from its own close: this one {dollars(report.base_price)}
                , the one compared {dollars(comparing.report.base_price)}.
              </p>
            ) : null}
            <div
              className="flex flex-wrap gap-1.5"
              role="group"
              aria-label="Horizon to show in full"
            >
              {HORIZON_KEYS.map((key) => (
                <button
                  key={key}
                  type="button"
                  aria-pressed={horizon === key}
                  onClick={() => setHorizon(key)}
                  className={cn(
                    "rounded-md border px-2.5 py-1 text-xs",
                    horizon === key
                      ? "border-foreground/40 bg-secondary font-medium text-foreground"
                      : "border-border text-muted-foreground hover:bg-accent",
                  )}
                >
                  {HORIZON_LABEL[key]}
                </button>
              ))}
            </div>
            <DistributionChart
              title={`${HORIZON_LABEL[horizon]} ahead, in full`}
              subject={{
                label: "This report",
                horizon: report.horizons[horizon],
                basePrice: report.base_price,
              }}
              compare={
                comparing
                  ? {
                      label: reportName(comparing),
                      horizon: comparing.report.horizons[horizon],
                      basePrice: comparing.report.base_price,
                    }
                  : null
              }
              outcome={landed?.[horizon] ?? null}
            />
          </section>

          <HorizonTable report={report} landed={landed} />

          {run?.audit.errors.length ? (
            <ul className="space-y-1 text-xs text-loss">
              {run.audit.errors.map((f) => (
                <li key={`e-${f.where}`}>
                  {f.where}: {f.message}
                </li>
              ))}
            </ul>
          ) : null}
          {run?.audit.warnings.length ? (
            <details className="text-xs text-muted-foreground">
              <summary className="cursor-pointer">
                {run.audit.warnings.length} audit{" "}
                {run.audit.warnings.length === 1 ? "warning" : "warnings"} — shown beside the
                report, they change nothing it says
              </summary>
              <ul className="mt-1 space-y-1">
                {run.audit.warnings.map((f) => (
                  <li key={`w-${f.where}`}>
                    {f.where}: {f.message}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}

          <Actions shown={shown} onOpenLive={onOpenLive} onKept={onKept} />
        </CardContent>
      </Card>

      <InputsCard inputs={shown.inputs} />
    </>
  );
}

function HorizonTable({
  report,
  landed,
}: {
  report: GeneratedReport;
  landed: ReturnType<typeof outcomes>;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="pb-2 font-medium">Horizon</th>
            <th className="pb-2 text-right font-medium">5%</th>
            <th className="pb-2 text-right font-medium">Median</th>
            <th className="pb-2 text-right font-medium">95%</th>
            <th className="pb-2 text-right font-medium">Median price</th>
            <th className="pb-2 text-right font-medium">P(up)</th>
            <th className="pb-2 text-right font-medium">ES 5%</th>
            {landed ? <th className="pb-2 pl-4 font-medium">What came of it</th> : null}
          </tr>
        </thead>
        <tbody className="tabular-nums">
          {horizonRows(report).map((row) => {
            const outcome = landed?.[row.key];
            return (
              <tr key={row.key} className="border-b border-border/50 last:border-0">
                <td className="py-1.5">{HORIZON_LABEL[row.key]}</td>
                <td className="py-1.5 text-right">{pct(row.p05)}</td>
                <td className="py-1.5 text-right">{pct(row.median)}</td>
                <td className="py-1.5 text-right">{pct(row.p95)}</td>
                <td className="py-1.5 text-right">
                  {dollars(inUnit(report, row.median, "price"))}
                </td>
                <td className="py-1.5 text-right">{(row.probPositive * 100).toFixed(1)}%</td>
                <td className="py-1.5 text-right">{pct(row.es5)}</td>
                {landed ? (
                  <td className="py-1.5 pl-4 text-xs whitespace-nowrap">
                    {outcome && outcome.landing !== "pending" ? (
                      <span className="inline-flex items-center gap-1.5">
                        <Swatch where={outcome.landing} />
                        <span className="text-foreground">{pct(outcome.return_pct)}</span>
                        <span className="text-muted-foreground">
                          {outcomeText(outcome, sessionDay)}
                        </span>
                      </span>
                    ) : (
                      <span className="text-muted-foreground">
                        {outcomeText(outcome, sessionDay)}
                      </span>
                    )}
                  </td>
                ) : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Actions({
  shown,
  onOpenLive,
  onKept,
}: {
  shown: Shown;
  onOpenLive: () => void;
  onKept: () => void;
}) {
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const [keeping, setKeeping] = useState(false);
  const { report, run } = shown;
  const passes = run ? run.audit.ok : true;

  const keep = async () => {
    if (!run) return;
    setKeeping(true);
    try {
      const stored = await api.recordRiskForecast(report, rememberedOperator(), {
        snapshot: run.snapshot,
        diagnostics: run.diagnostics,
        sources: run.sources,
      });
      setNote({
        ok: true,
        text: stored.new
          ? `Kept in the forecast database for ${stored.session}.`
          : `Already in the forecast database; ${stored.receipts} receipts.`,
      });
      onKept();
    } catch (cause) {
      setNote({
        ok: false,
        text: cause instanceof ApiError || cause instanceof Error ? cause.message : String(cause),
      });
    } finally {
      setKeeping(false);
    }
  };

  const download = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = reportFileName({
      ...report,
      target_session: report.target_session ?? shown.session,
    });
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const openLive = () => {
    if (handOffReport(report)) onOpenLive();
    else
      setNote({
        ok: false,
        text: "This browser refused the hand-off; download it and paste it on Live.",
      });
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {run && !shown.row ? (
        <Button onClick={keep} disabled={!passes || keeping}>
          {keeping ? <Loader2 className="size-3.5 animate-spin" /> : null}
          Keep in the forecast database
        </Button>
      ) : null}
      <Button variant="outline" onClick={openLive} disabled={!passes}>
        <Send className="size-3.5" />
        Open in Live to check and apply
      </Button>
      <Button variant="outline" onClick={download}>
        <Download className="size-3.5" />
        Download JSON
      </Button>
      {note ? (
        <span className={cn("text-xs", note.ok ? "text-muted-foreground" : "text-loss")}>
          {note.text}
        </span>
      ) : null}
    </div>
  );
}

function InputsCard({ inputs }: { inputs: KeptInputs | null }) {
  const snapshot = inputs?.snapshot;
  const diagnostics = inputs?.diagnostics;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">What it read</CardTitle>
        <p className="text-xs text-muted-foreground">
          Shown beside the forecast, never fed to the model: no history exists at the same
          pre-market clock time, so training on these would read the future.
        </p>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {snapshot ? (
          <>
            <table className="w-full min-w-[560px] text-sm">
              <tbody className="tabular-nums">
                {inputRows({
                  ...snapshot,
                  input_observations: snapshot.input_observations ?? [],
                  missing_inputs: snapshot.missing_inputs ?? [],
                }).map((item) => (
                  <tr key={item.field} className="border-b border-border/50 last:border-0">
                    <td className="py-1.5">{item.label}</td>
                    <td className="py-1.5 text-right font-medium">
                      {item.missing ? <span className="text-stuck">not read</span> : item.value}
                    </td>
                    <td className="py-1.5 pl-4 text-xs text-muted-foreground">{item.observed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {snapshot.notes?.length ? (
              <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
                {snapshot.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
            {diagnostics?.history_observations !== undefined ? (
              <p className="mt-3 text-xs text-muted-foreground">
                {diagnostics.history_observations.toLocaleString()} sessions,{" "}
                {diagnostics.covariates_used?.length ?? 0} covariates,{" "}
                {(diagnostics.simulation_paths ?? 0).toLocaleString()} scenarios
                {diagnostics.engine === "chronos"
                  ? `; ${diagnostics.direct_steps} sessions direct, ${diagnostics.extension_steps} extended`
                  : ""}
                .
              </p>
            ) : null}
          </>
        ) : (
          <p className="text-xs text-muted-foreground">
            Not recorded for this report. What a report read is kept only when the Forecast tab or
            the forecast service made it, from this version on; a report made elsewhere (an LLM's, a
            pasted file) never said, and it is not reconstructed after the fact.
          </p>
        )}
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
