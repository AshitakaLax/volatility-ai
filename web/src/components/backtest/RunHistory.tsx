import { ArrowDown, ArrowUp, History, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { RunHistoryFilterBar } from "@/components/backtest/RunHistoryFilterBar";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Field, Select } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { filterHistoryRows } from "@/lib/filters";
import { cn, pct, runUrl, usd } from "@/lib/utils";
import {
  EMPTY_RUN_HISTORY_FILTERS,
  type FundPerformanceMetrics,
  type HistoryRow,
  type RunHistoryFilters,
} from "@/types/backtest";

/**
 * Every run this server has completed, ranked by a metric you choose.
 *
 * ONE ROW PER CONFIGURATION, not per run. A run holds several funds and
 * each fund several grid cells, and the comparable thing is a single
 * configuration's metrics -- "which run was best" is not answerable
 * because a run is not one result.
 *
 * WHY THE RANKING METRIC IS A CHOICE AND NOT A DEFAULT. This project's
 * own results repeatedly show the highest-return configuration being one
 * nobody would deploy: the sweep that led on CAGR also carried an 80%
 * drawdown, and the one with the best worst-year gave up half the
 * return. A single "best" column would quietly assert an answer to a
 * question the data does not settle. So the column is picked, the
 * direction is stated, and the engine's own pick is marked separately
 * so a reader can see when their metric disagrees with it.
 */

interface Props {
  /** Bumped by the caller when a run finishes, to refresh the list. */
  refreshToken?: number;
}

type MetricKey = keyof FundPerformanceMetrics;

interface RankSpec {
  key: MetricKey;
  label: string;
  /** Which end of the scale is better. */
  higherIsBetter: boolean;
  format: (value: number) => string;
  hint?: string;
}

// The four the brief named, plus the ones this project actually ranks
// by. `higherIsBetter` is data rather than a special case per column,
// so adding one is a line here and nothing else.
const RANKINGS: RankSpec[] = [
  {
    key: "net_yield_pct",
    label: "Most profitable",
    higherIsBetter: true,
    format: (v) => pct(v, 2),
    hint: "total return over the window",
  },
  { key: "cagr_pct", label: "Best CAGR", higherIsBetter: true, format: (v) => pct(v, 2) },
  {
    key: "worst_year_pct",
    label: "Best worst year",
    higherIsBetter: true,
    format: (v) => pct(v, 2),
    hint: "the year it did worst — least bad wins",
  },
  {
    key: "max_drawdown_pct",
    label: "Lowest drawdown",
    higherIsBetter: false,
    format: (v) => pct(v, 2),
  },
  {
    key: "return_over_drawdown",
    label: "Return / drawdown",
    higherIsBetter: true,
    format: (v) => v.toFixed(3),
    hint: "return per unit of pain",
  },
  { key: "sharpe_ratio", label: "Sharpe", higherIsBetter: true, format: (v) => v.toFixed(2) },
  { key: "sortino_ratio", label: "Sortino", higherIsBetter: true, format: (v) => v.toFixed(2) },
  {
    key: "profit_factor",
    label: "Profit factor",
    higherIsBetter: true,
    format: (v) => v.toFixed(2),
  },
  { key: "win_rate_pct", label: "Win rate", higherIsBetter: true, format: (v) => pct(v, 1) },
  {
    key: "stuck_capital_value",
    label: "Least stuck capital",
    higherIsBetter: false,
    format: (v) => usd(v, 0),
    hint: "capital the grid could not get back",
  },
  {
    key: "capital_velocity_index",
    label: "Capital velocity",
    higherIsBetter: true,
    format: (v) => v.toFixed(3),
  },
  {
    key: "avg_hold_duration",
    label: "Shortest hold",
    higherIsBetter: false,
    format: (v) => `${v.toFixed(0)} bars`,
  },
];

function valueOf(row: HistoryRow, key: MetricKey): number | null {
  const value = row.metrics[key];
  // A report exported before a metric existed has no value for it.
  // null sorts LAST in either direction -- missing is not "worst", and
  // treating it as zero would rank an old run as the best drawdown ever.
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function RunHistory({ refreshToken }: Props) {
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [metric, setMetric] = useState<MetricKey>("cagr_pct");
  const [filters, setFilters] = useState<RunHistoryFilters>(EMPTY_RUN_HISTORY_FILTERS);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api
      .history()
      .then((body) => {
        setRows(body.rows);
        setError(null);
      })
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : String(cause)),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load, refreshToken]);

  // The filter narrows the flattened rows; ranking then orders whatever
  // survives. Both are cheap, but memoised so typing in a range box
  // does not re-sort a thousand rows on every keystroke.
  const visible = useMemo(() => filterHistoryRows(rows, filters), [rows, filters]);
  const visibleRuns = useMemo(
    () => new Set(visible.map((row) => row.run_id)).size,
    [visible],
  );

  const spec = RANKINGS.find((entry) => entry.key === metric) ?? RANKINGS[0]!;
  const ranked = [...visible].sort((a, b) => {
    const left = valueOf(a, spec.key);
    const right = valueOf(b, spec.key);
    if (left === null && right === null) return 0;
    if (left === null) return 1;
    if (right === null) return -1;
    return spec.higherIsBetter ? right - left : left - right;
  });

  return (
    <Card>
      <CardHeader className="flex-row items-end justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="size-4" />
            Run history
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            {visible.length === rows.length
              ? `${rows.length}`
              : `${visible.length} of ${rows.length}`}{" "}
            configuration{rows.length === 1 ? "" : "s"} across {visibleRuns} run
            {visibleRuns === 1 ? "" : "s"}, ranked by {spec.label.toLowerCase()}
            {spec.hint ? ` — ${spec.hint}` : ""}.
          </p>
        </div>
        <div className="flex items-end gap-3">
          <Field label="Rank by">
            <Select
              data-testid="rank-by"
              value={metric}
              onChange={(event) => setMetric(event.currentTarget.value as MetricKey)}
            >
              {RANKINGS.map((entry) => (
                <option key={entry.key} value={entry.key}>
                  {entry.label}
                </option>
              ))}
            </Select>
          </Field>
          <Button variant="ghost" onClick={load} title="Reload">
            <RefreshCw className={cn("size-3.5", loading && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>

      {!error && rows.length > 0 ? (
        <CardContent className="pt-0">
          <RunHistoryFilterBar
            rows={rows}
            filters={filters}
            onChange={setFilters}
            showing={visible.length}
            total={rows.length}
          />
        </CardContent>
      ) : null}

      <CardContent className="overflow-x-auto">
        {error ? (
          <p className="text-sm text-loss">
            {error} — the backtest engine host may be unreachable.
          </p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No completed runs yet. Submit one above; every finished run is kept and appears
            here, including across a server restart.
          </p>
        ) : visible.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No runs match these filters. Loosen a bound or{" "}
            <button
              type="button"
              className="underline hover:text-foreground"
              onClick={() => setFilters(EMPTY_RUN_HISTORY_FILTERS)}
            >
              reset
            </button>
            .
          </p>
        ) : (
          <table className="w-full min-w-[1080px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">#</th>
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Fund</th>
                <th className="pb-2 text-right font-medium">Step</th>
                <th className="pb-2 text-right font-medium">Target</th>
                <th className="pb-2 font-medium">Model</th>
                <th className="pb-2 text-right font-medium">
                  <span className="inline-flex items-center gap-1">
                    {spec.label}
                    {spec.higherIsBetter ? (
                      <ArrowUp className="size-3" />
                    ) : (
                      <ArrowDown className="size-3" />
                    )}
                  </span>
                </th>
                <th className="pb-2 text-right font-medium">CAGR</th>
                <th className="pb-2 text-right font-medium">Max DD</th>
                <th className="pb-2 text-right font-medium">Worst yr</th>
                <th className="pb-2 text-right font-medium">Trades</th>
                <th className="pb-2 font-medium">Window</th>
                <th className="pb-2 font-medium">Run</th>
              </tr>
            </thead>
            <tbody className="tnum">
              {ranked.slice(0, 100).map((row, index) => {
                const value = valueOf(row, spec.key);
                const worst = valueOf(row, "worst_year_pct");
                return (
                  <tr
                    key={`${row.run_id}-${row.ticker}-${row.grid_step}-${row.profit_target}`}
                    data-testid="history-row"
                    className="cursor-pointer border-b border-border/50 last:border-0 hover:bg-accent"
                    // A real <a> (below, in the Run column) is what gives
                    // ctrl/cmd-click, middle-click and "copy link" their
                    // normal browser behaviour; this is the click-anywhere
                    // convenience for the rest of the row, opening the
                    // SAME url the same way -- a new, independent tab, so
                    // this history table is never replaced by the report
                    // it opens.
                    onClick={() => window.open(runUrl(row.run_id), "_blank", "noopener,noreferrer")}
                    title="Open this run in a new tab"
                  >
                    <td className="py-2 text-muted-foreground">{index + 1}</td>
                    <td
                      className="max-w-[180px] truncate py-2 text-xs"
                      title={row.name ?? undefined}
                    >
                      {row.name ?? <span className="text-muted-foreground">--</span>}
                    </td>
                    <td className="py-2 font-medium">{row.ticker}</td>
                    <td className="py-2 text-right">
                      {row.grid_step === null ? "--" : pct(row.grid_step * 100, 3)}
                    </td>
                    <td className="py-2 text-right">
                      {row.profit_target === null ? "--" : pct(row.profit_target * 100, 3)}
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {row.sizing_model ?? "--"}
                      {row.engine_rank === 0 ? (
                        <Badge className="ml-1.5">engine pick</Badge>
                      ) : null}
                    </td>
                    <td className="py-2 text-right font-semibold">
                      {value === null ? (
                        <span className="text-muted-foreground" title="not recorded in this run">
                          --
                        </span>
                      ) : (
                        spec.format(value)
                      )}
                    </td>
                    <td className="py-2 text-right">{pct(row.metrics.cagr_pct, 1)}</td>
                    <td className="py-2 text-right text-loss">
                      {pct(row.metrics.max_drawdown_pct, 1)}
                    </td>
                    <td
                      className={cn(
                        "py-2 text-right",
                        worst !== null && worst < 0 && "text-loss",
                        worst !== null && worst >= 0 && "text-profit",
                      )}
                    >
                      {worst === null ? "--" : pct(worst, 1)}
                    </td>
                    <td
                      className={cn(
                        "py-2 text-right",
                        row.metrics.total_trades === 0 && "text-stuck",
                      )}
                      title={
                        row.metrics.total_trades === 0
                          ? "This configuration never traded. A book that sits in cash has no drawdown and no losing year, so it ranks first on those metrics without doing anything."
                          : undefined
                      }
                    >
                      {row.metrics.total_trades}
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {row.start?.slice(0, 10) ?? "--"} → {row.end?.slice(0, 10) ?? "--"}
                    </td>
                    <td className="py-2 font-mono text-xs text-muted-foreground">
                      <a
                        href={runUrl(row.run_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-foreground hover:underline"
                        // The row's own onClick already opens this exact
                        // url in a new tab; without this, clicking the
                        // link itself would fire BOTH, opening two tabs.
                        onClick={(event) => event.stopPropagation()}
                      >
                        {row.run_id.slice(0, 8)}
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {visible.some((row) => row.metrics.total_trades === 0) &&
        !spec.higherIsBetter ? (
          <p className="mt-3 text-xs text-stuck">
            Some configurations never traded. A book that sits in cash has no drawdown and
            no losing year, so it tops those rankings without doing anything — check the
            trade count before reading a row as a result.
          </p>
        ) : null}
        {ranked.length > 100 ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Showing the top 100 of {ranked.length}.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
