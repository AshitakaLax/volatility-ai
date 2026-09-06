import { Activity, LineChart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BacktestChart } from "@/components/backtest/BacktestChart";
import { FilterPanel } from "@/components/backtest/FilterPanel";
import { FundComparison } from "@/components/backtest/FundComparison";
import { ParameterForm } from "@/components/backtest/ParameterForm";
import { RiskRewardMetrics } from "@/components/backtest/RiskRewardMetrics";
import { RunHistory } from "@/components/backtest/RunHistory";
import { SweepMatrix } from "@/components/backtest/SweepMatrix";
import { TradeLog } from "@/components/backtest/TradeLog";
import { AlgorithmStatus } from "@/components/live/AlgorithmStatus";
import { CommandCenter } from "@/components/live/CommandCenter";
import { DeploymentHealth } from "@/components/live/DeploymentHealth";
import { LiveOrderLedger } from "@/components/live/LiveOrderLedger";
import { Card, CardContent } from "@/components/ui/primitives";
import { useBacktestRun } from "@/hooks/useBacktestRun";
import { useLiveState } from "@/hooks/useLiveState";
import { usePriceBars } from "@/hooks/usePriceBars";
import { api } from "@/lib/api";
import { filterExecutions, openLotIds } from "@/lib/filters";
import { cn } from "@/lib/utils";
import {
  DEFAULT_FILTERS,
  type ExecutionFilters,
  type MultiFundBacktestReport,
} from "@/types/backtest";

/**
 * Section 1 is the default view, and that ordering is the brief's.
 *
 * The report shown comes from a submitted run when there is one, and
 * falls back to the static export otherwise -- so the page is useful
 * before the API is running, which is also how it was developed.
 */
type Tab = "backtest" | "live";

export default function App() {
  const [tab, setTab] = useState<Tab>("backtest");
  const [staticReport, setStaticReport] = useState<MultiFundBacktestReport | null>(null);
  const [filters, setFilters] = useState<ExecutionFilters>(DEFAULT_FILTERS);
  const { run, submit, submitting, error } = useBacktestRun();
  const [staged, setStaged] = useState<{ gridStep: number; profitTarget: number } | null>(
    null,
  );
  // A run loaded back out of history. Takes precedence over the live
  // one so opening an old result actually shows it, and is cleared when
  // a new run is submitted.
  const [opened, setOpened] = useState<MultiFundBacktestReport | null>(null);

  // --- live ------------------------------------------------------------
  const [stores, setStores] = useState<{ path: string; label: string; paper: boolean }[]>([]);
  const [store, setStore] = useState<string | null>(null);
  const live = useLiveState(tab === "live" ? store : null);

  useEffect(() => {
    if (tab !== "live" || stores.length > 0) return;
    void api
      .stores()
      .then((body) => {
        setStores(body.stores);
        // Select the first store automatically. A picker that starts
        // empty makes an operator choose before seeing anything, and
        // there is usually exactly one.
        setStore((current) => current ?? body.stores[0]?.path ?? null);
      })
      .catch(() => setStores([]));
  }, [tab, stores.length]);

  useEffect(() => {
    void api.staticReport().then(setStaticReport);
  }, []);

  // A completed run wins over the export; nothing else changes the view.
  const report = opened ?? run?.report ?? staticReport;
  const tickers = report ? Object.keys(report.funds) : [];
  const selected = filters.tickers[0] ?? tickers[0] ?? null;
  const fund = report && selected ? report.funds[selected] : undefined;

  const executions = fund?.executions ?? [];
  const visible = useMemo(
    () => filterExecutions(executions, filters),
    [executions, filters],
  );
  const open = useMemo(() => openLotIds(executions), [executions]);

  // REAL OHLC, from the server, for the window in view. Previously
  // these were synthesised from the executions themselves, which drew a
  // line through the fill prices rather than the market -- fine for
  // placing markers, useless for seeing what the price actually did
  // between them.
  const { candles, meta: barMeta, error: barError } = usePriceBars(
    selected,
    filters.range.start,
    filters.range.end,
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-[1600px] items-center gap-6 px-6 py-4">
          <span className="text-sm font-semibold tracking-tight">volatility-ai</span>
          <nav className="flex gap-1">
            {(
              [
                { id: "backtest", label: "Backtesting", icon: LineChart },
                { id: "live", label: "Live", icon: Activity },
              ] as const
            ).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors",
                  tab === id
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </nav>
          {report ? (
            <span className="ml-auto text-xs text-muted-foreground">
              {report.run_id} · {report.parameters.sizing_model} · step{" "}
              {((report.parameters.grid_step_pct ?? 0) * 100).toFixed(2)}% · target{" "}
              {((report.parameters.profit_target_pct ?? 0) * 100).toFixed(2)}% ·{" "}
              {report.parameters.fill_model} fills
              {report.parameters.n_jobs && report.parameters.n_jobs > 1
                ? ` · ${report.parameters.n_jobs} workers`
                : ""}
            </span>
          ) : null}
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-4 px-6 py-6">
        {tab === "live" ? (
          <>
            <AlgorithmStatus state={live.state} />
            <DeploymentHealth
              state={live.state}
              health={live.health}
              stores={stores}
              selected={store}
              onSelect={setStore}
            />
            {live.error ? (
              <Card>
                <CardContent className="pt-5 text-sm text-loss">
                  {live.error} — is the API running?{" "}
                  <code className="text-foreground">uvicorn server.app:app</code>
                </CardContent>
              </Card>
            ) : null}
            <CommandCenter path={store} state={live.state} onHalted={live.refresh} />
            <LiveOrderLedger
              lots={live.state?.lots ?? []}
              lastPrice={live.state?.last_price ?? null}
            />
          </>
        ) : (
          <>
            <ParameterForm
              onSubmit={(request) => {
                // A new run replaces whatever was opened from history,
                // or the page would show an old report beside a running
                // job and give no clue which the metrics belong to.
                setOpened(null);
                submit(request);
              }}
              run={run}
              submitting={submitting}
              error={error}
              range={filters.range}
              staged={staged}
            />

            {!report ? (
              <Card>
                <CardContent className="pt-5 text-sm text-muted-foreground">
                  No run loaded. Submit one above, or generate a static export with{" "}
                  <code className="text-foreground">
                    python tools/export_ui_data.py --tickers TQQQ
                  </code>
                  .
                </CardContent>
              </Card>
            ) : (
              <>
                {fund ? (
                  <RiskRewardMetrics metrics={fund.metrics} />
                ) : null}

                <FilterPanel
                  filters={filters}
                  onChange={setFilters}
                  availableTickers={tickers}
                  showing={visible.length}
                  total={executions.length}
                />

                <BacktestChart
                  candles={candles ?? []}
                  loading={candles === null}
                  bucketSeconds={barMeta?.bucket_seconds ?? null}
                  error={barError}
                  executions={visible}
                  timeframe={filters.timeframe}
                  openLotIds={open}
                  profitTarget={report.parameters.profit_target_pct ?? 0.005}
                />

                <TradeLog
                  executions={visible}
                  totalBeforeFilters={executions.length}
                  profitTarget={report.parameters.profit_target_pct ?? 0.005}
                />

                <SweepMatrix
                  funds={report.funds}
                  onSelectCell={(gridStep, profitTarget) =>
                    setStaged({ gridStep, profitTarget })
                  }
                />

                {tickers.length > 1 ? <FundComparison funds={report.funds} /> : null}

                <RunHistory
                  onOpen={(runId) => {
                    void api
                      .historyRun(runId)
                      .then((stored) => setOpened(stored.report))
                      .catch(() => setOpened(null));
                  }}
                  refreshToken={run?.status === "complete" ? 1 : 0}
                />
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
