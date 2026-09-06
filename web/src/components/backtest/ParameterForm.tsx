import { AlertCircle, Play } from "lucide-react";
import { useEffect, useState } from "react";

import { api, type FundAvailability } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Field, Input, Select } from "@/components/ui/primitives";
import type { BacktestRunRequest, BacktestRunState, DateRange } from "@/types/backtest";

/**
 * The bidirectional half: submit a run and watch it.
 *
 * This is the one control in the application that causes work to happen
 * rather than changing what is drawn. It is visually separated from
 * FilterPanel for that reason -- filtering is free and instant, a run
 * costs real engine time, and a user should be able to tell which
 * button does which before pressing it.
 *
 * Submission is allowed here and refused for live state because the two
 * differ in what they can touch: a backtest is a simulation over a CSV
 * in a process with no broker and no credentials.
 */

interface Props {
  onSubmit: (request: BacktestRunRequest) => void;
  run: BacktestRunState | null;
  submitting: boolean;
  error: string | null;
  /**
   * The filter panel's window, submitted WITH the run.
   *
   * One date range, two jobs: it filters what is drawn, and it bounds
   * what the engine reads. Two separate pickers for the same concept
   * would let them disagree, and the chart would then be showing a
   * different period than the metrics beside it.
   */
  range: DateRange;
  /**
   * Parameters staged from a sweep-matrix cell, as PERCENTAGES.
   *
   * Applied to the inputs rather than submitted, so a click loads a
   * configuration for review and the run stays an explicit act. A cell
   * click that silently started 23 seconds of engine time would be a
   * surprising amount of work for a single click.
   */
  staged?: { gridStep: number; profitTarget: number } | null;
}

export function ParameterForm({ onSubmit, run, submitting, error, range, staged }: Props) {
  const [funds, setFunds] = useState<FundAvailability[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [tickers, setTickers] = useState<string[]>(["TQQQ"]);
  const [gridStep, setGridStep] = useState(1.0);
  const [profitTarget, setProfitTarget] = useState(0.5);
  const [model, setModel] = useState("fixed");
  const [fillModel, setFillModel] = useState<"close" | "intrabar">("close");
  const [limit, setLimit] = useState(50_000);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    api
      .funds()
      .then((body) => {
        setFunds(body.funds);
        setModels(body.sizing_models);
      })
      .catch((cause: unknown) => {
        setLoadError(
          cause instanceof Error
            ? `${cause.message} — is the API running? uvicorn server.app:app`
            : "could not reach the API",
        );
      });
  }, []);

  useEffect(() => {
    if (!staged) return;
    setGridStep(Number((staged.gridStep * 100).toFixed(4)));
    setProfitTarget(Number((staged.profitTarget * 100).toFixed(4)));
  }, [staged]);

  const toggle = (ticker: string) =>
    setTickers((current) =>
      current.includes(ticker)
        ? current.filter((value) => value !== ticker)
        : [...current, ticker],
    );

  const busy = submitting || run?.status === "queued" || run?.status === "running";

  const submit = () =>
    onSubmit({
      tickers,
      // Percentages in the UI, fractions on the wire. The engine works
      // in fractions and a form that sent 1.0 meaning "one percent"
      // would run a 100% grid step and silently produce nothing.
      grid_steps: [gridStep / 100],
      profit_targets: [profitTarget / 100],
      sizing_model: model,
      fill_model: fillModel,
      strategy_params: model === "fixed" ? { allocation_pct: 0.05 } : {},
      limit,
      ...(range.start ? { start: range.start } : {}),
      ...(range.end ? { end: range.end } : {}),
    });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Play className="size-4" />
            Run a backtest
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Queued on the server. A full ten-year run is roughly 23 seconds per
            configuration.
            {range.start || range.end
              ? ` Windowed to ${range.start ?? "start"} – ${range.end ?? "end"} from the filters below.`
              : ""}
          </p>
        </div>
        {run ? <RunStatus run={run} /> : null}
      </CardHeader>

      <CardContent className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Funds</span>
          <div className="flex flex-wrap gap-1.5">
            {funds.map((fund) => (
              <button
                key={fund.ticker}
                type="button"
                disabled={!fund.available || busy}
                onClick={() => toggle(fund.ticker)}
                title={fund.available ? fund.path : "not downloaded — see cli.py fetch-data"}
                className={
                  "rounded-md border px-2 py-1 text-xs transition-colors disabled:opacity-40 " +
                  (tickers.includes(fund.ticker)
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border hover:bg-accent")
                }
              >
                {fund.ticker}
              </button>
            ))}
            {funds.length === 0 && !loadError ? (
              <span className="text-xs text-muted-foreground">loading…</span>
            ) : null}
          </div>
        </div>

        <Field label="Grid step %">
          <Input
            type="number"
            step="0.05"
            min="0.01"
            className="w-24"
            value={gridStep}
            disabled={busy}
            onChange={(event) => setGridStep(Number(event.currentTarget.value))}
          />
        </Field>

        <Field label="Profit target %">
          <Input
            type="number"
            step="0.05"
            min="0.01"
            className="w-24"
            value={profitTarget}
            disabled={busy}
            onChange={(event) => setProfitTarget(Number(event.currentTarget.value))}
          />
        </Field>

        <Field label="Sizing model">
          <Select
            value={model}
            disabled={busy}
            onChange={(event) => setModel(event.currentTarget.value)}
          >
            {models.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Fill model">
          <Select
            value={fillModel}
            disabled={busy}
            onChange={(event) => setFillModel(event.currentTarget.value as "close" | "intrabar")}
          >
            <option value="close">close</option>
            <option value="intrabar">intrabar</option>
          </Select>
        </Field>

        <Field label="Bars">
          <Select
            value={String(limit)}
            disabled={busy}
            onChange={(event) => setLimit(Number(event.currentTarget.value))}
          >
            <option value="20000">20k (fast)</option>
            <option value="50000">50k</option>
            <option value="200000">200k</option>
            <option value="2000000">everything (slow)</option>
          </Select>
        </Field>

        <Button onClick={submit} disabled={busy || tickers.length === 0}>
          {busy ? "Running…" : "Run"}
        </Button>
      </CardContent>

      {/* intrabar is not a cosmetic setting: it fills a level TOUCHED
          during a bar rather than requiring the close to reach it, which
          this project measured at roughly 1.85x more fills on both
          sides. Two runs differing only here are not comparable. */}
      {fillModel === "intrabar" ? (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">
            Intrabar fills a level touched during the bar — roughly 1.85x more fills than
            “close” on this project's own minute data. Not comparable with a close-model run.
          </p>
        </CardContent>
      ) : null}

      {(error ?? loadError) ? (
        <CardContent className="pt-0">
          <p className="flex items-start gap-2 text-xs text-loss">
            <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
            {error ?? loadError}
          </p>
        </CardContent>
      ) : null}
    </Card>
  );
}

function RunStatus({ run }: { run: BacktestRunState }) {
  const tone =
    run.status === "failed" ? "loss" : run.status === "complete" ? "profit" : "stuck";
  return (
    <div className="flex items-center gap-3">
      {run.status === "running" ? (
        <div className="h-1 w-28 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${Math.round(run.progress * 100)}%` }}
          />
        </div>
      ) : null}
      <Badge tone={tone}>{run.message ?? run.status}</Badge>
    </div>
  );
}
