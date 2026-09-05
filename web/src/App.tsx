import { Activity, LineChart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BacktestChart } from "@/components/backtest/BacktestChart";
import { FilterPanel } from "@/components/backtest/FilterPanel";
import { FundComparison } from "@/components/backtest/FundComparison";
import { ParameterForm } from "@/components/backtest/ParameterForm";
import { RiskRewardMetrics } from "@/components/backtest/RiskRewardMetrics";
import { Card, CardContent } from "@/components/ui/primitives";
import { useBacktestRun } from "@/hooks/useBacktestRun";
import { api } from "@/lib/api";
import { type Candle, filterExecutions, openLotIds, toEpochSeconds } from "@/lib/filters";
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

  useEffect(() => {
    void api.staticReport().then(setStaticReport);
  }, []);

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

  // Candles are synthesised from the executions rather than fetched.
  // The bar endpoint serves recent minute data for LIVE charting; a
  // historical run may cover ten years, and pulling a million rows into
  // a browser to draw 40 markers would be the wrong trade. Each
  // execution contributes its own price point, so the line the markers
  // sit on is exactly the prices they executed at.
  const candles = useMemo<Candle[]>(() => {
    const byTime = new Map<number, Candle>();
    for (const execution of executions) {
      const time = toEpochSeconds(execution.timestamp);
      const existing = byTime.get(time);
      if (existing) {
        existing.high = Math.max(existing.high, execution.price);
        existing.low = Math.min(existing.low, execution.price);
        existing.close = execution.price;
      } else {
        byTime.set(time, {
          time,
          open: execution.price,
          high: execution.price,
          low: execution.price,
          close: execution.price,
        });
      }
    }
    return [...byTime.values()].sort((a, b) => a.time - b.time);
  }, [executions]);

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
            </span>
          ) : null}
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-4 px-6 py-6">
        {tab === "live" ? (
          <Card>
            <CardContent className="pt-5 text-sm text-muted-foreground">
              Live telemetry is the next phase. The read-only API it will use is already
              running — until the view lands, the Streamlit dashboard
              (<code className="text-foreground">streamlit run dashboard.py</code>) remains
              the operator view.
            </CardContent>
          </Card>
        ) : (
          <>
            <ParameterForm
              onSubmit={submit}
              run={run}
              submitting={submitting}
              error={error}
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
                  candles={candles}
                  executions={visible}
                  timeframe={filters.timeframe}
                  openLotIds={open}
                  profitTarget={report.parameters.profit_target_pct ?? 0.005}
                />

                {tickers.length > 1 ? <FundComparison funds={report.funds} /> : null}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
