import { useMemo } from "react";

import { BacktestChart } from "@/components/backtest/BacktestChart";
import { FilterPanel } from "@/components/backtest/FilterPanel";
import { FundComparison } from "@/components/backtest/FundComparison";
import { RiskRewardMetrics } from "@/components/backtest/RiskRewardMetrics";
import { SweepMatrix } from "@/components/backtest/SweepMatrix";
import { TradeLog } from "@/components/backtest/TradeLog";
import { Card, CardContent } from "@/components/ui/primitives";
import { usePriceBars } from "@/hooks/usePriceBars";
import { filterExecutions, openLotIds } from "@/lib/filters";
import type {
  BacktestRunState,
  ExecutionFilters,
  MultiFundBacktestReport,
} from "@/types/backtest";

/**
 * The read-only half of the backtesting view, on its own nav tab.
 *
 * WHY A SEPARATE TAB. Opening a run from Run history or Active runs
 * loads a whole report -- summary metrics, an OHLC chart, a trade log,
 * the sweep surface. Rendered inline under the Backtesting tab it sat
 * between the parameter form and the history table it came from, so a
 * glance at an old run pushed the controls off screen. It lands here
 * now, and the Backtesting tab stays the instrument: ParameterForm,
 * ActiveRuns, RunHistory.
 *
 * The execution FILTER is owned by the parent (App), not this
 * component: ParameterForm reads its date range to window a submitted
 * run, so there is one date range for the chart and the engine both --
 * exactly the arrangement that predated this split.
 */

interface Props {
  /** A completed run's report, the static export, or null. */
  report: MultiFundBacktestReport | null;
  /** The run this tab is following. Drives the queued / running /
   *  failed states shown before `report` exists. */
  run: BacktestRunState | null;
  filters: ExecutionFilters;
  onFiltersChange: (filters: ExecutionFilters) => void;
  /** A sweep-matrix cell was clicked -- the parent stages it onto the
   *  parameter form and switches back to the Backtesting tab. */
  onStageCell: (gridStep: number, profitTarget: number) => void;
}

export function BacktestResult({
  report,
  run,
  filters,
  onFiltersChange,
  onStageCell,
}: Props) {
  const tickers = report ? Object.keys(report.funds) : [];
  const selected = filters.tickers[0] ?? tickers[0] ?? null;
  const fund = report && selected ? report.funds[selected] : undefined;

  const executions = fund?.executions ?? [];
  const visible = useMemo(
    () => filterExecutions(executions, filters),
    [executions, filters],
  );
  const open = useMemo(() => openLotIds(executions), [executions]);

  // REAL OHLC from the server for the window in view -- synthesising it
  // from the fills themselves drew a line through fill prices rather
  // than the market between them.
  const { candles, meta: barMeta, error: barError } = usePriceBars(
    selected,
    filters.range.start,
    filters.range.end,
  );

  if (!report) {
    if (run && (run.status === "queued" || run.status === "running")) {
      const percent = Math.round(run.progress * 100);
      return (
        <Card>
          <CardContent className="space-y-3 pt-5">
            <p className="text-sm">
              {run.message ?? (run.status === "queued" ? "Queued…" : "Running…")}
            </p>
            <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full bg-primary transition-all"
                style={{
                  width: `${Math.max(percent, run.status === "queued" ? 100 : 2)}%`,
                }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              This view fills in the moment the run completes. Progress is also on Active runs,
              under the Backtesting tab.
            </p>
          </CardContent>
        </Card>
      );
    }
    if (run && run.status === "failed") {
      return (
        <Card>
          <CardContent className="pt-5 text-sm text-loss">
            {run.error ?? run.message ?? "The run failed."}
          </CardContent>
        </Card>
      );
    }
    return (
      <Card>
        <CardContent className="pt-5 text-sm text-muted-foreground">
          No run loaded. Open one from <span className="text-foreground">Run history</span> or{" "}
          <span className="text-foreground">Active runs</span> on the Backtesting tab, or submit a
          new backtest there.
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      {fund ? <RiskRewardMetrics metrics={fund.metrics} /> : null}

      <FilterPanel
        filters={filters}
        onChange={onFiltersChange}
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

      <SweepMatrix funds={report.funds} onSelectCell={onStageCell} />

      {tickers.length > 1 ? <FundComparison funds={report.funds} /> : null}
    </>
  );
}
