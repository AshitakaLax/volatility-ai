import { useEffect, useMemo, useState } from "react";

import { BacktestChart } from "@/components/backtest/BacktestChart";
import { ConfigurationList } from "@/components/backtest/ConfigurationList";
import { FilterPanel } from "@/components/backtest/FilterPanel";
import { FundComparison } from "@/components/backtest/FundComparison";
import { RiskRewardMetrics } from "@/components/backtest/RiskRewardMetrics";
import { SweepMatrix } from "@/components/backtest/SweepMatrix";
import { SweepSummary } from "@/components/backtest/SweepSummary";
import { TradeLog } from "@/components/backtest/TradeLog";
import { Button, Card, CardContent } from "@/components/ui/primitives";
import { useBacktestRun } from "@/hooks/useBacktestRun";
import { buildDetailRequest } from "@/lib/detailRun";
import { filterExecutions, openLotIds, resolveSelectedFund } from "@/lib/filters";
import { configurationKey } from "@/lib/sweepSummary";
import { isRunning } from "@/lib/runQueue";
import type {
  Cell,
  ChartResolution,
  DateRange,
  ExecutionFilters,
  Report,
  Run,
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
 *
 * WHICH CONFIGURATION THIS PAGE IS SHOWING. A run can be a sweep of many
 * (grid_step, profit_target, strategy_params) configurations, but every
 * configuration but the engine's top pick carries METRICS ONLY on the
 * wire (server/backtest.py: carrying every cell's executions too "would
 * multiply the payload by the size of the grid"). So `selection` (below)
 * is local, page-only UI state -- unlike `filters`, it need not survive a
 * tab switch -- and selecting a non-top configuration shows its
 * metrics INSTANTLY (already shipped) while the chart/trade log offer an
 * explicit "View full detail" re-run (a normal, scoped ~23s backtest
 * job) rather than pretending that data already exists.
 */

interface Props {
  /** A completed run's report, the static export, or null. */
  report: Report | null;
  /** The run this tab is following. Drives the queued / running /
   *  failed states shown before `report` exists. */
  run: Run | null;
  filters: ExecutionFilters;
  onFiltersChange: (filters: ExecutionFilters) => void;
  /** A sweep-matrix cell's "load into form" affordance was used -- the
   *  parent stages it onto the parameter form and switches back to the
   *  Backtesting tab, to launch a broader NEW sweep from that point.
   *  Distinct from selecting a configuration to view IN PLACE here. */
  onLoadIntoForm: (gridStep: number, profitTarget: number) => void;
}

/** A configuration key qualified by its fund -- the detail cache's key. */
function scopedKey(ticker: string, configKey: string): string {
  return JSON.stringify([ticker, configKey]);
}

export function BacktestResult({
  report,
  run,
  filters,
  onFiltersChange,
  onLoadIntoForm,
}: Props) {
  const tickers = report ? Object.keys(report.funds) : [];
  const selected = resolveSelectedFund(filters.tickers, tickers);
  const fund = report && selected ? report.funds[selected] : undefined;
  const configurations = useMemo(() => fund?.cells ?? [], [fund]);
  const topPick = configurations[0];

  // Which configuration this page shows, qualified by the fund it was
  // picked on -- null means "the engine's top pick," so an ordinary
  // (non-swept) run needs no selection at all. A selection applies only
  // while its fund is the one in view: configurationKey carries no fund,
  // and every fund in a sweep shares the same keys, so an unqualified key
  // would silently select the same-looking cell on a different fund.
  const [selection, setSelection] = useState<{ ticker: string; key: string } | null>(null);
  // One on-demand "View full detail" re-run per fund+configuration a
  // reader has actually asked to see (scopedKey), so re-selecting one
  // already viewed doesn't refire the job.
  const [detailRuns, setDetailRuns] = useState<Record<string, Run>>({});
  // Which fund+configuration the CURRENTLY IN-FLIGHT detail run belongs
  // to -- tracked separately from `selection` because a reader can select
  // something else while one is still running; the completion handler
  // must file the result under what it was actually submitted for.
  const [pendingDetailKey, setPendingDetailKey] = useState<string | null>(null);
  const detailBacktest = useBacktestRun();

  // A different report invalidates all of the above. A different FUND
  // does not need to: everything is keyed by fund already, so switching
  // back restores that fund's selection and cached detail.
  useEffect(() => {
    setSelection(null);
    setDetailRuns({});
    setPendingDetailKey(null);
  }, [report?.id]);

  const selectedConfigKey = selection && selection.ticker === selected ? selection.key : null;
  const selectedConfig: Cell | undefined =
    (selectedConfigKey &&
      configurations.find((entry) => configurationKey(entry) === selectedConfigKey)) ||
    topPick;
  // True when there is nothing to distinguish (nothing explicitly
  // selected) or the selection IS the engine's own pick -- in both cases
  // `fund`'s baked-in fills/equity are already the right ones to show.
  const isTopPick =
    !topPick || !selectedConfig || configurationKey(selectedConfig) === configurationKey(topPick);
  const detailKey =
    selected && selectedConfig ? scopedKey(selected, configurationKey(selectedConfig)) : null;
  const detailRun = detailKey ? detailRuns[detailKey] : undefined;
  const detailFund = selected ? detailRun?.report?.funds[selected] : undefined;
  // The fund result actually feeding the chart/trade log below.
  const activeFund = isTopPick ? fund : detailFund;

  // File a completed detail run into the cache under the key it was
  // SUBMITTED for (pendingDetailKey), not whatever happens to be
  // selected once it lands.
  useEffect(() => {
    if (pendingDetailKey && detailBacktest.run?.status === "complete") {
      setDetailRuns((current) => ({ ...current, [pendingDetailKey]: detailBacktest.run! }));
    }
  }, [detailBacktest.run, pendingDetailKey]);

  const isDetailPending =
    pendingDetailKey !== null &&
    pendingDetailKey === detailKey &&
    !detailRun &&
    (detailBacktest.submitting ||
      detailBacktest.run?.status === "queued" ||
      (detailBacktest.run !== null && isRunning(detailBacktest.run.status)));
  const detailError =
    pendingDetailKey !== null && pendingDetailKey === detailKey && !detailRun && !isDetailPending
      ? (detailBacktest.run?.error ??
        detailBacktest.error ??
        (detailBacktest.run?.status === "failed" ? "The run failed." : null))
      : null;

  // The original request's cash yield, when the run this tab follows IS
  // the report on screen. A report doesn't carry it; the run's echoed
  // request does, archived runs included. Otherwise unknown, and omitted.
  const originalCashYield =
    run?.report && report && run.report.id === report.id ? run.req.cash_yield_pct : undefined;

  const viewFullDetail = () => {
    if (!report || !selected || !selectedConfig || !fund) return;
    const request = buildDetailRequest(report, selected, fund, selectedConfig, originalCashYield);
    // Only marked pending once there is something to submit -- a pending
    // key with no submission behind it would file whatever run the hook
    // still holds from before.
    if (!request) return;
    setPendingDetailKey(scopedKey(selected, configurationKey(selectedConfig)));
    void detailBacktest.submit(request);
  };

  // Picking a heatmap cell can switch the fund too: when the fund in view
  // has no sweep, the heatmap shows another fund's, and a cell there only
  // means something on that fund.
  const selectFromHeatmap = (config: Cell, ticker: string) => {
    setSelection({ ticker, key: configurationKey(config) });
    if (ticker !== selected) onFiltersChange({ ...filters, tickers: [ticker] });
  };

  // Stabilise `executions` so the two downstream useMemos don't see a new
  // array reference on every render (activeFund?.fills ?? []
  // creates a new [] literal each time activeFund is undefined).
  const executions = useMemo(() => activeFund?.fills ?? [], [activeFund]);
  const visible = useMemo(
    () => filterExecutions(executions, filters),
    [executions, filters],
  );
  const open = useMemo(() => openLotIds(executions), [executions]);

  // The run's actual data bounds -- the anchor the chart's zoom levels
  // measure back from when the filter range is open. Per-fund `bars` is
  // more precise than the report-wide window.
  const dataRange: DateRange = {
    start: fund?.bars.start ?? report?.start ?? null,
    end: fund?.bars.end ?? report?.end ?? null,
  };
  const profitTarget = selectedConfig?.target ?? report?.target ?? 0.005;

  if (!report) {
    if (run && (run.status === "queued" || isRunning(run.status))) {
      const percent = Math.round(run.progress * 100);
      return (
        <Card>
          <CardContent className="space-y-3 pt-5">
            <p className="text-sm">
              {run.msg ?? (run.status === "queued" ? "Queued…" : "Running…")}
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
            {run.error ?? run.msg ?? "The run failed."}
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

  const showSweepDetails = configurations.length > 1;

  return (
    <>
      {selectedConfig ? (
        <RiskRewardMetrics
          metrics={selectedConfig.m}
          benchmarkCagr={selectedConfig.m.buy_hold_cagr_pct ?? null}
        />
      ) : null}

      {showSweepDetails ? <SweepSummary configurations={configurations} /> : null}

      <SweepMatrix
        funds={report.funds}
        selectedTicker={selected ?? ""}
        onSelectTicker={(ticker) => onFiltersChange({ ...filters, tickers: [ticker] })}
        onSelectConfiguration={selectFromHeatmap}
        onLoadIntoForm={onLoadIntoForm}
      />

      {showSweepDetails ? (
        <ConfigurationList
          configurations={configurations}
          selectedKey={selectedConfig ? configurationKey(selectedConfig) : null}
          onSelect={(config) => {
            if (selected) setSelection({ ticker: selected, key: configurationKey(config) });
          }}
        />
      ) : null}

      <FilterPanel
        filters={filters}
        onChange={onFiltersChange}
        availableTickers={tickers}
        showing={visible.length}
        total={executions.length}
      />

      {activeFund ? (
        <>
          <BacktestChart
            ticker={selected}
            executions={visible}
            resolution={filters.chartResolution}
            onResolutionChange={(chartResolution: ChartResolution) =>
              onFiltersChange({ ...filters, chartResolution })
            }
            range={filters.range}
            dataRange={dataRange}
            openLotIds={open}
            profitTarget={profitTarget}
          />

          <TradeLog
            executions={visible}
            ticker={selected}
            totalBeforeFilters={executions.length}
            profitTarget={profitTarget}
          />
        </>
      ) : (
        <Card>
          <CardContent className="space-y-3 pt-5">
            {isDetailPending ? (
              <>
                <p className="text-sm">
                  {detailBacktest.run?.msg ??
                    (detailBacktest.run?.status === "running" ? "Running…" : "Queued…")}
                </p>
                <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{
                      width: `${Math.max(
                        Math.round((detailBacktest.run?.progress ?? 0) * 100),
                        detailBacktest.run?.status === "queued" ? 100 : 2,
                      )}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Re-running just this configuration — roughly 23 seconds for a full window.
                </p>
              </>
            ) : (
              <>
                {detailError ? (
                  <p className="text-sm text-loss">{detailError}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    This configuration&apos;s trade-level detail hasn&apos;t been run yet — the
                    metrics above are already accurate. Run it to see the chart and trade log.
                  </p>
                )}
                <Button onClick={viewFullDetail} disabled={detailBacktest.submitting}>
                  {detailError ? "Try again" : "View full detail"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {tickers.length > 1 ? <FundComparison funds={report.funds} /> : null}
    </>
  );
}
