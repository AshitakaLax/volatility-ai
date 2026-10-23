/**
 * The Warehouse tab's two reads, mirrored by hand from
 * server/warehouse_status.py (and engine/warehouse/inventory.py, which
 * computes most of it).
 *
 * Times are ISO 8601 strings, sizes are bytes, returns and drawdowns are
 * percent (a total_return of 230.7 is +230.7%). `null` means "could not
 * be measured here" -- never zero.
 */

/** One fund: in the warehouse (`ingested`), in the fund registry
 * (`known`), or both. Every bar field is null for a fund never ingested. */
export interface FundRow {
  ticker: string;
  ingested: boolean;
  known: boolean;
  bars: number | null;
  first: string | null;
  last: string | null;
  /** Sessions with at least one bar (Eastern dates). */
  sessions: number | null;
  /** Rows beyond one per timestamp: an overlapping ingest. */
  duplicates: number | null;
  /** Median bars per session over the fund's last 20 sessions. */
  bars_per_session: number | null;
  /** The last completed NYSE session: what "up to date" means. */
  through: string;
  last_session: string | null;
  /** The last session was fetched before it closed. */
  partial: boolean;
  sessions_behind: number | null;
  /** An estimate: sessions behind x bars_per_session. */
  bars_to_add: number | null;
  sweeps: number;
  simulations: number;
  /** Simulations run on the bars the warehouse holds now. */
  current_simulations: number;
  /** ...and on an earlier version of them. */
  older_simulations: number;
  best_return: number | null;
  bytes: number | null;
  sector: string | null;
  inception: string | null;
  leverage: number | null;
}

/** One sweep (a run x fund), newest first. */
export interface SweepRow {
  id: string;
  algorithm: string;
  created: string | null;
  fund: string | null;
  strategy: string | null;
  /** A server run's id: opens it with runUrl(). Null for a cli.py sweep. */
  run_id: string | null;
  run_name: string | null;
  simulations: number;
  failed: number;
  last: string | null;
  best_return: number | null;
  best_drawdown: number | null;
  /** Return/Drawdown of the best configuration; null when infinite. */
  best_calmar: number | null;
}

/** Sweeps grouped by fund and strategy, ranked by Total Return %. */
export interface StrategyRow {
  fund: string;
  strategy: string;
  sweeps: number;
  simulations: number;
  failed: number;
  best_return: number | null;
  best_drawdown: number | null;
  best_calmar: number | null;
  best_sweep: string | null;
  last: string | null;
}

export interface Catalog {
  name: string;
  bytes: number;
  modified: string;
}

export interface Lake {
  files: number;
  bytes: number;
}

export interface Storage {
  root: string | null;
  catalogs: Catalog[] | null;
  lakes: { ohlcv: Lake & { by_fund: Record<string, number> }; executions: Lake; external: Lake } | null;
  tmp_bytes: number | null;
  disk: { total: number; free: number } | null;
  duckdb: string | null;
  tables: {
    assets: number | null;
    broker_environments: number | null;
    market_events: Record<string, number>;
    external_series: { provider: string; series: number; newest: string | null }[];
  } | null;
}

/** GET /api/backtest/warehouse */
export interface WarehouseStatus {
  at: string;
  /** A warehouse exists here. */
  available: boolean;
  /** Another process is writing it: the figures are the last good read. */
  busy: boolean;
  error: string | null;
  /** The last completed NYSE session. */
  through: string;
  summary: {
    funds: number;
    bars: number;
    sweeps: number;
    simulations: number;
    executions: number;
    last_hour: number;
    last_day: number;
    bytes: number;
    free: number | null;
  };
  funds: FundRow[];
  results: {
    by_status: Record<string, number>;
    /** Simulations finished per hour, oldest first, the current hour last. */
    hourly: { hour: string; n: number }[];
    mean_ms_last_hour: number | null;
    executions: { rows: number; simulations: number };
    strategies: StrategyRow[];
    recent: SweepRow[];
  };
  storage: Storage;
}

export interface Temperature {
  label: string;
  c: number;
  /** The CPU's own limits: cooling should be at full / it slows itself down. */
  high: number | null;
  crit: number | null;
  hottest: number;
}

export interface Disk {
  label: string;
  path: string;
  total: number | null;
  free: number | null;
}

export interface RunningRun {
  id: string;
  name: string | null;
  progress: number;
  msg: string | null;
  shard: string | null;
  configurations: number | null;
}

/** GET /api/backtest/system */
export interface SystemStatus {
  at: string;
  build: {
    commit: string | null;
    branch: string | null;
    dirty: boolean | null;
    uptime_s: number;
    python: string;
    pid: number;
  };
  host: {
    cpus: number | null;
    load: [number, number, number] | null;
    temperatures: Temperature[];
    /** Null in a Docker container, which masks the kernel's counters. */
    throttling: { throttled_cpus: number; max_events: number } | null;
  };
  /** cgroup v2 figures; null outside a container. */
  container: {
    mem_mb: number;
    mem_limit_mb: number | null;
    cpu_pct: null;
    /** Cores in use since the previous read; null on the first. */
    cores_busy: number | null;
  } | null;
  disks: Disk[];
  queue: {
    paused: boolean;
    counts: Record<string, number>;
    running: RunningRun[];
    remaining_runs: number;
    /** Every queued run plus the unfinished part of each running one. */
    remaining_configurations: number;
    /** A queued run whose request no longer validates: not in the total. */
    some_unsized: boolean;
  };
  shards: { total: number; online: number; working: number };
  backups: {
    dir: string;
    count: number;
    bytes: number;
    latest: { name: string; bytes: number; at: string } | null;
  } | null;
}
