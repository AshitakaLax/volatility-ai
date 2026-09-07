import { FlaskConical, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle, Select } from "@/components/ui/primitives";
import { ApiError, api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AblationResponse, DatasetsResponse, EvaluationResponse, SourcesSummary } from "@/types/ml";

/**
 * What the ML research has found so far -- and how little of it, still.
 *
 * THIS TAB IS READ-ONLY BY CONSTRUCTION. It renders exactly what
 * server/ml_insights.py serves, which is precomputed JSON from
 * tools/{fetch_market_inputs,build_ml_dataset,evaluate_ml_features,
 * ablate_ml_features}.py -- nothing here submits a job, and nothing
 * here is on a path a sizing decision could reach. See ml_plan.md,
 * "Phase ML-0" for the underlying writeup.
 *
 * THE BANNER IS NOT BOILERPLATE. The one measured result this project
 * has (COWZ, one fund, one horizon) is one hit out of six comparisons,
 * which is close to what chance alone produces -- the same
 * selection-bias trap the indicator sweeps (stage2/stage3) already
 * fell into once. A panel that showed a bar chart and a green badge
 * without that context would be MORE confident than the evidence, on a
 * page that exists specifically to avoid that.
 */
export function ModelInsights() {
  const [sources, setSources] = useState<SourcesSummary | null>(null);
  const [sourcesError, setSourcesError] = useState<string | null>(null);

  const [datasets, setDatasets] = useState<DatasetsResponse | null>(null);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  const [labels, setLabels] = useState<string[]>([]);
  const [label, setLabel] = useState<string | null>(null);

  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [evaluationHint, setEvaluationHint] = useState<string | null>(null);

  const [ablation, setAblation] = useState<AblationResponse | null>(null);
  const [ablationHint, setAblationHint] = useState<string | null>(null);

  useEffect(() => {
    void api.mlSources().then(setSources).catch((error: unknown) => {
      setSourcesError(error instanceof ApiError ? error.message : "Could not reach the API.");
    });
    void api.mlDatasets().then(setDatasets).catch((error: unknown) => {
      setDatasetsError(error instanceof ApiError ? error.message : "Could not reach the API.");
    });
    void api.mlEvaluationLabels().then((body) => {
      setLabels(body.labels);
      setLabel((current) => current ?? body.labels[0] ?? null);
    });
  }, []);

  useEffect(() => {
    if (!label) return;
    setEvaluation(null);
    setEvaluationHint(null);
    void api
      .mlEvaluation(label)
      .then(setEvaluation)
      .catch((error: unknown) => setEvaluationHint(error instanceof ApiError ? error.message : null));

    setAblation(null);
    setAblationHint(null);
    void api
      .mlAblation(label)
      .then(setAblation)
      .catch((error: unknown) => setAblationHint(error instanceof ApiError ? error.message : null));
  }, [label]);

  return (
    <div className="space-y-4">
      <Card className="border-stuck/40 bg-stuck/5">
        <CardContent className="flex items-start gap-3 pt-5">
          <FlaskConical className="mt-0.5 size-4 shrink-0 text-stuck" />
          <div className="space-y-1 text-sm">
            <p className="font-medium text-foreground">
              Research view — not connected to trading.
            </p>
            <p className="text-xs text-muted-foreground">
              Nothing on this tab influences the backtest engine, the paper loop, or any sizing
              decision. It shows whether ~118 public data series (rates, credit, volatility term
              structure, sector rotation) carry any predictive signal beyond the bars alone —
              measured on a purged, paired walk-forward split, not just displayed. The honest
              answer so far: one weak, unreplicated result on one fund, out of six comparisons
              tried — about what chance alone produces. See the verdict column below.
            </p>
          </div>
        </CardContent>
      </Card>

      <SourcesCard summary={sources} error={sourcesError} />
      <DatasetsCard summary={datasets} error={datasetsError} />

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Signal evaluation</CardTitle>
          {labels.length > 0 ? (
            <Select
              value={label ?? ""}
              onChange={(event) => setLabel(event.target.value)}
              className="w-56"
            >
              {labels.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          ) : null}
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          <p className="text-xs text-muted-foreground">
            AUC of predicting whether a lot's profit target is reached (touched, not closed —
            the engine fills on touch) within the label's horizon. <code>bar</code> uses only
            the minute bars; <code>macro</code> uses only the 118 external series;{" "}
            <code>both</code> combines them. <code>shuffled</code> fits the same model on
            permuted labels and should sit near 0.500 — the check that the harness itself
            does not leak.
          </p>
          {evaluation ? (
            <EvaluationTable response={evaluation} />
          ) : evaluationHint ? (
            <NotBuiltYet detail={evaluationHint} />
          ) : (
            <p className="text-xs text-muted-foreground">Loading…</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Which feature category, not just &ldquo;macro&rdquo;</CardTitle>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          <p className="text-xs text-muted-foreground">
            &ldquo;Macro helps&rdquo; is not actionable by itself — it is 73 columns across
            fourteen categories. Each row adds ONE category to the bar-only baseline and
            reports the paired lift on identical folds. Fourteen categories × several tickers
            is that many comparisons, and the categories are correlated (vol and credit both
            move on the same risk-off days), so no clean multiple-comparison correction
            applies — more &ldquo;consistent&rdquo; rows than chance alone would supply is
            suggestive, not proof.
          </p>
          {ablation ? (
            <AblationTable response={ablation} />
          ) : ablationHint ? (
            <NotBuiltYet detail={ablationHint} />
          ) : (
            <p className="text-xs text-muted-foreground">Loading…</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function NotBuiltYet({ detail }: { detail: string }) {
  return (
    <p className="flex items-start gap-2 text-xs text-muted-foreground">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
      {detail}
    </p>
  );
}

function SourcesCard({ summary, error }: { summary: SourcesSummary | null; error: string | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Public data sources</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {error ? (
          <NotBuiltYet detail={error} />
        ) : !summary ? (
          <p className="text-xs text-muted-foreground">Loading…</p>
        ) : (
          <div className="space-y-3">
            <p className="tnum text-lg font-semibold">
              {summary.total_series}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                series, no API key, 0 fetch failures
              </span>
            </p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(summary.by_category)
                .sort(([, a], [, b]) => b - a)
                .map(([category, count]) => (
                  <Badge key={category}>
                    {category} · {count}
                  </Badge>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DatasetsCard({ summary, error }: { summary: DatasetsResponse | null; error: string | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Training datasets</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {error ? (
          <NotBuiltYet detail={error} />
        ) : !summary ? (
          <p className="text-xs text-muted-foreground">Loading…</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="py-1.5 pr-4 font-medium">Ticker</th>
                  <th className="py-1.5 pr-4 font-medium">Rows</th>
                  <th className="py-1.5 pr-4 font-medium">Range</th>
                  <th className="py-1.5 pr-4 font-medium">Features</th>
                  <th className="py-1.5 pr-4 font-medium">Fully present</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.tickers).map(([ticker, row]) => (
                  <tr key={ticker} className="border-b border-border/50 last:border-0">
                    <td className="tnum py-1.5 pr-4 font-medium">{ticker}</td>
                    <td className="tnum py-1.5 pr-4">{row.rows.toLocaleString()}</td>
                    <td className="tnum py-1.5 pr-4 text-xs text-muted-foreground">
                      {row.first.slice(0, 10)} → {row.last.slice(0, 10)}
                    </td>
                    <td className="tnum py-1.5 pr-4">{row.feature_count}</td>
                    <td className="tnum py-1.5 pr-4">
                      {row.features_fully_present}/{row.feature_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** ~2 standard errors either side of 0.5. Outside this band the
 * shuffled control itself looks suspicious and is flagged rather than
 * quietly trusted -- see tools/evaluate_ml_features.py's own docstring
 * on why a single-seed control is not evidence either way. */
function verdictTone(verdict: string): "profit" | "loss" | "neutral" {
  if (verdict.includes("ADDS")) return "profit";
  if (verdict.includes("HURTS")) return "loss";
  return "neutral";
}

function EvaluationTable({ response }: { response: EvaluationResponse }) {
  const rows = Object.entries(response.tickers);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="py-1.5 pr-4 font-medium">Ticker</th>
            <th className="py-1.5 pr-4 font-medium">bar</th>
            <th className="py-1.5 pr-4 font-medium">macro</th>
            <th className="py-1.5 pr-4 font-medium">both</th>
            <th className="py-1.5 pr-4 font-medium">shuffled</th>
            <th className="py-1.5 pr-4 font-medium">paired lift (both − bar)</th>
            <th className="py-1.5 pr-4 font-medium">Verdict</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([ticker, row]) => {
            const mean = (values: number[]) => values.reduce((a, b) => a + b, 0) / values.length;
            const shuffledMean = mean(row.per_fold.shuffled);
            const shuffledOff = Math.abs(shuffledMean - 0.5) > 0.03;
            return (
              <tr key={ticker} className="border-b border-border/50 last:border-0">
                <td className="tnum py-1.5 pr-4 font-medium">{ticker}</td>
                <td className="tnum py-1.5 pr-4">{mean(row.per_fold.bar).toFixed(3)}</td>
                <td className="tnum py-1.5 pr-4">{mean(row.per_fold.macro).toFixed(3)}</td>
                <td className="tnum py-1.5 pr-4">{mean(row.per_fold.both).toFixed(3)}</td>
                <td
                  className={cn("tnum py-1.5 pr-4", shuffledOff && "text-loss")}
                  title={shuffledOff ? "More than 0.03 from 0.500 — worth a second look" : undefined}
                >
                  {shuffledMean.toFixed(3)}
                </td>
                <td className="tnum py-1.5 pr-4">
                  {row.paired_lift_mean >= 0 ? "+" : ""}
                  {row.paired_lift_mean.toFixed(4)} ± {row.paired_lift_se.toFixed(4)}
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({row.folds_positive}/{row.per_fold.bar.length} folds)
                  </span>
                </td>
                <td className="py-1.5 pr-4">
                  <Badge tone={verdictTone(row.verdict)}>{row.verdict}</Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AblationTable({ response }: { response: AblationResponse }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Object.entries(response.tickers).map(([ticker, ticketData]) => (
        <div key={ticker} className="rounded-md border border-border p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-semibold">{ticker}</span>
            <span className="text-xs text-muted-foreground">
              baseline {ticketData.baseline_auc.toFixed(3)} · {ticketData.consistent_count}/
              {ticketData.total_blocks} consistent
            </span>
          </div>
          <ul className="space-y-1">
            {ticketData.blocks.map((block) => (
              <li
                key={block.category}
                className={cn(
                  "tnum flex items-center justify-between rounded px-1.5 py-0.5 text-xs",
                  block.consistent && "bg-profit/10",
                )}
              >
                <span className={cn(block.consistent ? "font-medium text-profit" : "text-muted-foreground")}>
                  {block.category} ({block.columns})
                </span>
                <span className={block.consistent ? "text-profit" : "text-muted-foreground"}>
                  {block.lift_mean >= 0 ? "+" : ""}
                  {block.lift_mean.toFixed(4)} · {block.folds_positive}/{block.folds_total}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
