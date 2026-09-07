import { Activity, FlaskConical, LineChart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BacktestChart } from "@/components/backtest/BacktestChart";
import { FilterPanel } from "@/components/backtest/FilterPanel";
import { FundComparison } from "@/components/backtest/FundComparison";
import { ParameterForm } from "@/components/backtest/ParameterForm";
import { RiskRewardMetrics } from "@/components/backtest/RiskRewardMetrics";
import { ActiveRuns } from "@/components/backtest/ActiveRuns";
import { RunHistory } from "@/components/backtest/RunHistory";
import { SweepMatrix } from "@/components/backtest/SweepMatrix";
import { TradeLog } from "@/components/backtest/TradeLog";
import { AlgorithmStatus } from "@/components/live/AlgorithmStatus";
import { CommandCenter } from "@/components/live/CommandCenter";
import { DeploymentHealth } from "@/components/live/DeploymentHealth";
import { LiveOrderLedger } from "@/components/live/LiveOrderLedger";
import { ModelInsights } from "@/components/ml/ModelInsights";
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
type Tab = "backtest" | "live" | "ml";

export default function App() {
  const [tab, setTab] = useState<Tab>("backtest");
  const [staticReport, setStaticReport] = useState<MultiFundBacktestReport | null>(null);
  const [filters, setFilters] = useState<ExecutionFilters>(DEFAULT_FILTERS);
  const { run, submit, attach, submitting, error } = useBacktestRun();
  // Bumped whenever a run settles, so history reloads without the
  // reader having to press anything.
  const [historyToken, setHistoryToken] = useState(0);
  const [staged, setStaged] = useState<{ gridStep: number; profitTarget: number } | null>(
    null,
  );

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

  // Selecting a run (Run history, Active runs) opens ?run=<id> in a NEW
  // tab rather than swapping the current view -- see runUrl() in
  // lib/utils.ts. This is that tab's other half: on load, notice the
  // param and attach to exactly that run, the same way watching one
  // this tab submitted itself works. Forced onto the backtest tab
  // because a run is a backtest-tab concept regardless of which tab a
  // stale bookmark might otherwise land on.
  useEffect(() => {
    const runId = new URLSearchParams(window.location.search).get("run");
    if (!runId) return;
    setTab("backtest");
    void attach(runId);
  }, [attach]);

  // A completed run wins over the export; nothing else changes the view.
  const report = run?.report ?? staticReport;
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
                { id: "ml", label: "Model research", icon: FlaskConical },
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
        ) : tab === "ml" ? (
          <ModelInsights />
        ) : (
          <>
            <ParameterForm
              onSubmit={(request) => submit(request)}
              run={run}
              submitting={submitting}
              error={error}
              range={filters.range}
              staged={staged}
            />

            {/* OUTSIDE the report branch, deliberately. Both were
                previously rendered only when a report was loaded, which
                hid them on exactly the load where they are most
                useful -- a fresh page with nothing selected. Selecting
                a run from either one opens it in its own tab (see
                runUrl() in lib/utils.ts) rather than replacing this
                view, so this tab's own in-progress submission is never
                displaced by a click meant to just glance at something
                else. */}
            <ActiveRuns onSettled={() => setHistoryToken((value) => value + 1)} />

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
              </>
            )}
            <RunHistory refreshToken={historyToken} />
          </>
        )}
      </main>
    </div>
  );
}
