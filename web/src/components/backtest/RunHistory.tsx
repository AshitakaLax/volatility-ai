import { ArrowDown, ArrowUp, ArrowUpDown, History, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import { RunHistoryFilterBar } from "@/components/backtest/RunHistoryFilterBar";
import { Pagination } from "@/components/ui/Pagination";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Field, Select } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import {
  historyQueryBody,
  nextRunHistorySort,
  type RunHistoryColumn,
  type RunHistorySort,
} from "@/lib/filters";
import { cn, pct, runUrl, timestamp, usd } from "@/lib/utils";
import {
  EMPTY_RUN_HISTORY_FILTERS,
  type HistoryFacets,
  type HistoryFund,
  type HistoryMetrics,
  type HistoryPage,
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

type MetricKey = keyof HistoryMetrics;

/** The fund to open on: the one most recently run, since that is what a
 * reader most likely came back to look at. */
function defaultFund(funds: HistoryFund[]): string | null {
  const ranked = [...funds].sort((a, b) => (b.last_saved ?? 0) - (a.last_saved ?? 0));
  return ranked[0]?.ticker ?? null;
}

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
  const value = row.m[key];
  // A report exported before a metric existed has no value for it.
  // null sorts LAST in either direction -- missing is not "worst", and
  // treating it as zero would rank an old run as the best drawdown ever.
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function sortIcon(direction: "asc" | "desc" | null) {
  if (direction === "asc") return <ArrowUp className="size-3" />;
  if (direction === "desc") return <ArrowDown className="size-3" />;
  // Faint, undirected -- a hint that the header is clickable without
  // claiming a direction that is not actually applied.
  return <ArrowUpDown className="size-3 opacity-30" />;
}

/**
 * One clickable, sortable column header. Module-scope like the other
 * small pieces in this codebase's tables/forms -- redefined inside
 * RunHistory on every render, it would remount on every keystroke
 * elsewhere on the page.
 */
function SortableHeader({
  column,
  label,
  align = "left",
  active,
  onSort,
}: {
  column: RunHistoryColumn;
  label: ReactNode;
  align?: "left" | "right";
  active: RunHistorySort | null;
  onSort: (column: RunHistoryColumn) => void;
}) {
  const direction = active?.column === column ? active.direction : null;
  return (
    <th className={cn("pb-2 font-medium", align === "right" && "text-right")}>
      <button
        type="button"
        onClick={() => onSort(column)}
        className={cn(
          "inline-flex items-center gap-1 hover:text-foreground",
          direction && "text-foreground",
        )}
      >
        {label}
        {sortIcon(direction)}
      </button>
    </th>
  );
}

export function RunHistory({ refreshToken }: Props) {
  const [funds, setFunds] = useState<HistoryFund[] | null>(null);
  const [ticker, setTicker] = useState<string | null>(null);
  const [facets, setFacets] = useState<HistoryFacets | null>(null);
  const [metric, setMetric] = useState<MetricKey>("cagr_pct");
  // Clicking a column header overrides Rank by's fixed direction for as
  // long as it is active; null ("off") falls back to Rank by exactly as
  // before this existed.
  const [columnSort, setColumnSort] = useState<RunHistorySort | null>(null);
  const toggleSort = (column: RunHistoryColumn) =>
    setColumnSort((current) => nextRunHistorySort(current, column));
  const [filters, setFilters] = useState<RunHistoryFilters>(EMPTY_RUN_HISTORY_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [data, setData] = useState<HistoryPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloads, setReloads] = useState(0);
  const load = useCallback(() => setReloads((count) => count + 1), []);

  // Which funds have history; keep the current pick if it still does.
  useEffect(() => {
    let cancelled = false;
    api
      .historyFunds()
      .then((list) => {
        if (cancelled) return;
        setFunds(list);
        setTicker((current) =>
          current && list.some((fund) => fund.ticker === current) ? current : defaultFund(list),
        );
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      });
    return () => {
      cancelled = true;
    };
  }, [refreshToken, reloads]);

  // The selected fund's filter options.
  useEffect(() => {
    if (!ticker) return;
    let cancelled = false;
    setFacets(null);
    api
      .historyFacets(ticker)
      .then((body) => {
        if (!cancelled) setFacets(body);
      })
      .catch(() => {
        if (!cancelled) setFacets(null);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker, refreshToken, reloads]);

  // A different fund's rows are never shown under this one's header.
  useEffect(() => {
    setData(null);
  }, [ticker]);

  // Back to the first page whenever what is being paged changes.
  useEffect(() => {
    setPage(1);
  }, [ticker, filters, columnSort, metric, pageSize]);

  const spec = RANKINGS.find((entry) => entry.key === metric) ?? RANKINGS[0]!;
  const bodyKey = ticker
    ? JSON.stringify(
        historyQueryBody({
          ticker,
          filters,
          sort: columnSort,
          rankBy: metric,
          higherIsBetter: spec.higherIsBetter,
          page,
          pageSize,
        }),
      )
    : null;

  // One page, queried server-side. Debounced so typing in a range box is
  // one request, not one per keystroke; a response to anything but the
  // latest request is dropped.
  useEffect(() => {
    if (!bodyKey) return;
    let cancelled = false;
    setLoading(true);
    const timer = window.setTimeout(() => {
      api
        .historyQuery(JSON.parse(bodyKey))
        .then((body) => {
          if (cancelled) return;
          setData(body);
          setError(null);
        })
        .catch((cause: unknown) => {
          if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [bodyKey, refreshToken, reloads]);

  // When a simulation's own save time is unknown, it's treated as having
  // happened right now -- read once at mount via useState's lazy
  // initializer (React's sanctioned escape hatch for an impure read like
  // this one), not once per row, so every row missing `saved_at` agrees
  // on what "now" means for the life of this view.
  const [nowSeconds] = useState(() => Date.now() / 1000);
  const total = data?.total ?? 0;
  const totalUnfiltered = data?.total_unfiltered ?? 0;
  const pageRows = data?.rows ?? [];
  const firstIndex = data?.offset ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <Card>
      <CardHeader className="flex-row items-end justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="size-4" />
            Run history
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            {ticker ? `${ticker}: ` : ""}
            {total === totalUnfiltered
              ? total.toLocaleString()
              : `${total.toLocaleString()} of ${totalUnfiltered.toLocaleString()}`}{" "}
            configuration{totalUnfiltered === 1 ? "" : "s"} across {data?.runs_matched ?? 0} run
            {data?.runs_matched === 1 ? "" : "s"}, ranked by {spec.label.toLowerCase()}
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

      {funds && funds.length > 0 && ticker ? (
        <CardContent className="pt-0">
          <RunHistoryFilterBar
            funds={funds}
            ticker={ticker}
            onTickerChange={setTicker}
            facets={facets}
            filters={filters}
            onChange={setFilters}
            showing={total}
            total={totalUnfiltered}
          />
        </CardContent>
      ) : null}

      <CardContent className="overflow-x-auto">
        {error ? (
          <p className="text-sm text-loss">
            {error} — the backtest engine host may be unreachable.
          </p>
        ) : funds !== null && funds.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No completed runs yet. Submit one above; every finished run is kept and appears
            here, including across a server restart.
          </p>
        ) : data === null ? (
          <p className="text-sm text-muted-foreground">Loading {ticker ?? "history"}…</p>
        ) : total === 0 ? (
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
          // Dimmed while the next page or filter result is on its way, so
          // a reader never mistakes the previous result for the new one.
          <table
            className={cn("w-full min-w-[1080px] text-sm transition-opacity", loading && "opacity-50")}
            aria-busy={loading}
          >
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">#</th>
                <SortableHeader column="name" label="Name" active={columnSort} onSort={toggleSort} />
                <SortableHeader column="ticker" label="Fund" active={columnSort} onSort={toggleSort} />
                <SortableHeader
                  column="grid_step"
                  label="Step"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader
                  column="profit_target"
                  label="Target"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader
                  column="sizing_model"
                  label="Model"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <th className="pb-2 text-right font-medium">
                  <button
                    type="button"
                    onClick={() => toggleSort("metric")}
                    className={cn(
                      "inline-flex items-center gap-1 hover:text-foreground",
                      columnSort?.column === "metric" && "text-foreground",
                    )}
                  >
                    {spec.label}
                    {columnSort?.column === "metric"
                      ? sortIcon(columnSort.direction)
                      : sortIcon(spec.higherIsBetter ? "asc" : "desc")}
                  </button>
                </th>
                <SortableHeader
                  column="cagr_pct"
                  label="CAGR"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader
                  column="max_drawdown_pct"
                  label="Max DD"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader
                  column="worst_year_pct"
                  label="Worst yr"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader
                  column="total_trades"
                  label="Trades"
                  align="right"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader column="window" label="Window" active={columnSort} onSort={toggleSort} />
                <SortableHeader
                  column="saved_at"
                  label="Timestamp"
                  active={columnSort}
                  onSort={toggleSort}
                />
                <SortableHeader column="run_id" label="Run" active={columnSort} onSort={toggleSort} />
              </tr>
            </thead>
            <tbody className="tnum">
              {pageRows.map((row, index) => {
                const value = valueOf(row, spec.key);
                const worst = valueOf(row, "worst_year_pct");
                return (
                  <tr
                    // (run, fund, rank) -- rank is the cell's index in that
                    // fund's engine-ranked list, so it is unique where no
                    // combination of its VALUES is: a Bayesian search
                    // re-tries the same configuration (dozens of identical
                    // rows), and colliding keys let React reconcile new
                    // data onto stale rows -- the "table didn't clear" bug.
                    key={`${row.run}-${row.ticker}-${row.rank}`}
                    data-testid="history-row"
                    className="cursor-pointer border-b border-border/50 last:border-0 hover:bg-accent"
                    // A real <a> (below, in the Run column) is what gives
                    // ctrl/cmd-click, middle-click and "copy link" their
                    // normal browser behaviour; this is the click-anywhere
                    // convenience for the rest of the row, opening the
                    // SAME url the same way -- a new, independent tab, so
                    // this history table is never replaced by the report
                    // it opens.
                    onClick={() => window.open(runUrl(row.run), "_blank", "noopener,noreferrer")}
                    title="Open this run in a new tab"
                  >
                    <td className="py-2 text-muted-foreground">{firstIndex + index + 1}</td>
                    <td
                      className="max-w-[180px] truncate py-2 text-xs"
                      title={row.name ?? undefined}
                    >
                      {row.name ?? <span className="text-muted-foreground">--</span>}
                    </td>
                    <td className="py-2 font-medium">{row.ticker}</td>
                    <td className="py-2 text-right">
                      {row.grid === null ? "--" : pct(row.grid * 100, 3)}
                    </td>
                    <td className="py-2 text-right">
                      {row.target === null ? "--" : pct(row.target * 100, 3)}
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {row.model ?? "--"}
                      {row.rank === 0 ? (
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
                    <td className="py-2 text-right">{pct(row.m.cagr_pct, 1)}</td>
                    <td className="py-2 text-right text-loss">
                      {pct(row.m.max_drawdown_pct, 1)}
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
                        row.m.total_trades === 0 && "text-stuck",
                      )}
                      title={
                        row.m.total_trades === 0
                          ? "This configuration never traded. A book that sits in cash has no drawdown and no losing year, so it ranks first on those metrics without doing anything."
                          : undefined
                      }
                    >
                      {row.m.total_trades}
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {row.start?.slice(0, 10) ?? "--"} → {row.end?.slice(0, 10) ?? "--"}
                    </td>
                    <td
                      className="py-2 text-xs text-muted-foreground"
                      title={
                        row.saved_at === null
                          ? "no recorded save time -- shown as now"
                          : undefined
                      }
                    >
                      {timestamp(row.saved_at ?? nowSeconds)}
                    </td>
                    <td className="py-2 font-mono text-xs text-muted-foreground">
                      <a
                        href={runUrl(row.run)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-foreground hover:underline"
                        // The row's own onClick already opens this exact
                        // url in a new tab; without this, clicking the
                        // link itself would fire BOTH, opening two tabs.
                        onClick={(event) => event.stopPropagation()}
                      >
                        {row.run.slice(0, 8)}
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {pageRows.some((row) => row.m.total_trades === 0) &&
        !spec.higherIsBetter ? (
          <p className="mt-3 text-xs text-stuck">
            Some configurations never traded. A book that sits in cash has no drawdown and
            no losing year, so it tops those rankings without doing anything — check the
            trade count before reading a row as a result.
          </p>
        ) : null}
        <Pagination
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          total={total}
          onPageChange={(next) =>
            setPage((prev) =>
              Math.min(Math.max(1, typeof next === "function" ? next(prev) : next), totalPages),
            )
          }
          onPageSizeChange={setPageSize}
        />
      </CardContent>
    </Card>
  );
}
