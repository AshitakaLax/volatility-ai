import { Activity, ArrowRight, BarChart3, FlaskConical, LineChart } from "lucide-react";
import { useEffect, useState } from "react";

import { ActiveRuns } from "@/components/backtest/ActiveRuns";
import { BacktestResult } from "@/components/backtest/BacktestResult";
import { ParameterForm } from "@/components/backtest/ParameterForm";
import { RunHistory } from "@/components/backtest/RunHistory";
import { AlgorithmStatus } from "@/components/live/AlgorithmStatus";
import { CommandCenter } from "@/components/live/CommandCenter";
import { DeploymentHealth } from "@/components/live/DeploymentHealth";
import { LiveOrderLedger } from "@/components/live/LiveOrderLedger";
import { LivePriceChart } from "@/components/live/LivePriceChart";
import { ModelInsights } from "@/components/ml/ModelInsights";
import { Button, Card, CardContent } from "@/components/ui/primitives";
import { useBacktestRun } from "@/hooks/useBacktestRun";
import { useLiveState } from "@/hooks/useLiveState";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  DEFAULT_FILTERS,
  type ExecutionFilters,
  type MultiFundBacktestReport,
} from "@/types/backtest";

/**
 * Section 1 (Backtesting) is the default view, and that ordering is the
 * brief's.
 *
 * "Backtest result" is a fourth tab rather than a panel inside
 * Backtesting: opening a run loads a whole report, and rendering that
 * between the parameter form and the history table it came from pushed
 * the controls off screen. The Backtesting tab is now purely the
 * instrument (form, active runs, history); the report it produces --
 * from a submission or from opening a saved run -- shows next door in
 * BacktestResult. The report falls back to the static export when there
 * is no run, so the page is useful before the API is up, which is also
 * how it was developed.
 */
type Tab = "backtest" | "result" | "live" | "ml";

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
  // browser tab rather than swapping the current view -- see runUrl() in
  // lib/utils.ts. This is that tab's other half: on load, notice the
  // param, land on the Backtest result tab, and attach to exactly that
  // run -- the same path a run this session submitted itself takes once
  // it completes.
  useEffect(() => {
    const runId = new URLSearchParams(window.location.search).get("run");
    if (!runId) return;
    setTab("result");
    void attach(runId);
  }, [attach]);

  // A completed run wins over the export; nothing else changes the view.
  const report = run?.report ?? staticReport;

  // A run submitted from the form finishes on THIS tab -- the button and
  // the status badge report it -- but the report itself now lives next
  // door. Rather than force-navigate mid-render (which races the "run
  // complete" state a test and a reader both watch for), the Backtesting
  // tab offers the jump when there is something to jump to.
  const submittedReportReady = run?.status === "complete" && Boolean(run.report);

  const stageCell = (gridStep: number, profitTarget: number) => {
    // A sweep-matrix click on the result tab prefills the form on the
    // Backtesting tab -- move there so the staged configuration is
    // visible rather than silently applied on a tab out of view.
    setStaged({ gridStep, profitTarget });
    setTab("backtest");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-[1600px] items-center gap-6 px-6 py-4">
          <span className="text-sm font-semibold tracking-tight">volatility-ai</span>
          <nav className="flex gap-1">
            {(
              [
                { id: "backtest", label: "Backtesting", icon: LineChart },
                { id: "result", label: "Backtest result", icon: BarChart3 },
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
              {report.parameters.name ? (
                <span className="font-medium text-foreground">{report.parameters.name} · </span>
              ) : null}
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
            <LivePriceChart
              symbol={live.state?.parameters?.symbol ?? null}
              lastPrice={live.state?.last_price ?? null}
              lastPriceAt={live.state?.last_tick_at ?? null}
            />
            <LiveOrderLedger
              lots={live.state?.lots ?? []}
              lastPrice={live.state?.last_price ?? null}
            />
          </>
        ) : tab === "ml" ? (
          <ModelInsights />
        ) : tab === "result" ? (
          <BacktestResult
            report={report}
            run={run}
            filters={filters}
            onFiltersChange={setFilters}
            onLoadIntoForm={stageCell}
          />
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

            {submittedReportReady ? (
              <Card>
                <CardContent className="flex items-center justify-between gap-4 pt-5">
                  <p className="text-sm text-muted-foreground">
                    Run complete
                    {run?.report?.parameters.name
                      ? ` — ${run.report.parameters.name}`
                      : ""}
                    . The chart, trade log and sweep surface are on the Backtest result tab.
                  </p>
                  <Button variant="outline" onClick={() => setTab("result")}>
                    Backtest result
                    <ArrowRight className="size-3.5" />
                  </Button>
                </CardContent>
              </Card>
            ) : null}

            {/* Selecting a run from either of these opens it in its own
                browser tab (runUrl() in lib/utils.ts), which lands on
                the Backtest result tab -- so an in-progress submission
                here is never displaced by a click meant to glance at
                something else. */}
            <ActiveRuns onSettled={() => setHistoryToken((value) => value + 1)} />

            <RunHistory refreshToken={historyToken} />
          </>
        )}
      </main>
    </div>
  );
}
