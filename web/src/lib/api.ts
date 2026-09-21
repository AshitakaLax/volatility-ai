/**
 * Typed access to the Python API.
 *
 * Everything goes through the Vite dev proxy (`/api`), so the browser only
 * ever talks to one origin. That is why there is no base URL here:
 * introducing one would make development and production differ in exactly
 * the way CORS bugs hide in.
 */
import type {
  Bars,
  Catalog,
  History,
  HistoryRow,
  Report,
  Run,
  RunOp,
  RunReq,
  Shard,
  ShardList,
  ShardOp,
  ShardSchedule,
  SubmitResponse,
  Validation,
} from "@/types/backtest";
import type { Ablation, ByTicker, Dataset, Eval, MlSeries } from "@/types/ml";
import type { Activity, LiveState, Rsi } from "@/types/telemetry";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    // FastAPI puts the useful part in `detail`. Surfacing the raw status
    // instead would turn "Unknown strategy_id 'fixd'. Known strategies:
    // ..." into "400", which is the difference between a message someone
    // can act on and one they cannot.
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = JSON.stringify(body.detail);
    } catch {
      /* a non-JSON error body is not itself an error worth reporting */
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

const query = (params: Record<string, string | number | null | undefined>) =>
  new URLSearchParams(
    Object.entries(params).flatMap(([key, value]) =>
      value === null || value === undefined || value === "" ? [] : [[key, String(value)]],
    ),
  ).toString();

/**
 * What the server may do, and which build it is. `caps` is read from the
 * server rather than compiled in, so the Command Center renders what THIS
 * deployment says. Liquidation and live parameter overrides are never
 * listed, by design (server/control.py).
 */
export interface Health {
  caps: ("live" | "halt" | "backtest" | "ml")[];
  /** Where sweeps run; null when this server runs them itself. */
  upstream: string | null;
  build: {
    commit: string | null;
    branch: string | null;
    /** null means "could not tell", which is different from false. */
    dirty: boolean | null;
    uptime_s: number;
    python: string;
    pid: number;
  };
  /** null outside a container -- cgroup is the only place these are true. */
  container: { mem_mb: number; mem_limit_mb: number | null; cpu_pct: number | null } | null;
}

export const api = {
  health: () => request<Health>("/api/health"),

  // -- Backtest ----------------------------------------------------------

  funds: () => request<Catalog>("/api/backtest/funds"),

  bars: (ticker: string, start?: string | null, end?: string | null, maxPoints = 3000) =>
    request<Bars>(`/api/backtest/bars?${query({ ticker, start, end, max_points: maxPoints })}`),

  /**
   * Run history as table rows: each cell joined with the run-level fields
   * it is filtered and sorted on. The wire states those once per run
   * (`runs`) rather than once per cell.
   */
  history: async (): Promise<{ rows: HistoryRow[]; runs: number }> => {
    const body = await request<History>("/api/backtest/history");
    const rows = body.rows.map((row): HistoryRow => {
      const run = body.runs[row.run];
      return {
        ...row,
        name: run?.name ?? null,
        model: run?.model ?? null,
        fill: run?.fill ?? null,
        start: run?.start ?? null,
        end: run?.end ?? null,
        saved_at: run?.saved_at ?? null,
        batch_id: run?.batch_id ?? null,
        batch_index: run?.batch_index ?? null,
        batch_total: run?.batch_total ?? null,
      };
    });
    return { rows, runs: new Set(body.rows.map((row) => row.run)).size };
  },

  runs: () => request<{ runs: Run[]; paused: boolean }>("/api/backtest/runs"),

  /** A queued, running or archived run -- the server falls back to history. */
  run: (runId: string) => request<Run>(`/api/backtest/runs/${runId}`),

  /**
   * A sweep that fits under the combination ceiling queues as one Run,
   * exactly as before. One too large for that comes back bisected --
   * `{batch_id, runs}` covering every independent chunk the server
   * split it into, each already queued.
   */
  submitRun: (body: RunReq) => post<SubmitResponse>("/api/backtest/runs", body),

  /**
   * A queue control; answers with the run's new snapshot. Pause/cancel on
   * a RUNNING run are requests -- the snapshot comes back "pausing" /
   * "cancelling" until its in-flight configurations finish. 409 means the
   * op does not apply to the run's current state. Cancel discards the
   * checkpoint; there is no undo.
   */
  controlRun: (runId: string, op: RunOp) => post<Run>(`/api/backtest/runs/${runId}`, op),

  /** Pausing holds everything; the running run pauses after its batch. */
  setQueuePaused: (paused: boolean) => post<{ paused: boolean }>("/api/backtest/queue", { paused }),

  /**
   * The machines working the queue: the engine host's own worker ("local")
   * plus every `cli.py shard` that has registered. 404 from an engine host
   * that predates shards.
   */
  shards: () => request<ShardList>("/api/backtest/shards"),

  /**
   * Pausing a shard hands its sweep back to the queue once the
   * configurations in flight finish -- another shard continues it. 409
   * for forgetting a shard that is still connected.
   */
  controlShard: (name: string, op: ShardOp) =>
    post<Shard>(`/api/backtest/shards/${encodeURIComponent(name)}`, op),

  setShardsPaused: (paused: boolean) =>
    post<{ paused: boolean }>("/api/backtest/shards", { paused }),

  /**
   * Set or clear a shard's daily lockout window (server-local wall-clock
   * HH:MM). Inside it, the shard behaves as if paused: no new claim, and
   * a running sweep hands back after its in-flight configurations.
   * `{enabled: false}` with no start/end clears the window outright.
   * 400 for a missing start/end while enabling, or a malformed time.
   */
  setShardSchedule: (name: string, schedule: ShardSchedule) =>
    post<{ name: string; schedule: ShardSchedule | null }>(
      `/api/backtest/shards/${encodeURIComponent(name)}/schedule`,
      schedule,
    ),

  /**
   * Dry-run the same validation `submitRun` performs, without queuing a
   * job, so a bad argument shows under its field before Run is pressed.
   * Its own route rather than a submit flag: a server predating the flag
   * would ignore it and queue the run.
   */
  validateRun: async (body: RunReq): Promise<Validation> => {
    try {
      return await post<Validation>("/api/backtest/validate", body);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) {
        // A deployment whose backtest half predates this route -- fall
        // back to submit-time validation, do not block the form.
        return { errors: [], degraded: true };
      }
      if (cause instanceof ApiError && cause.status === 422) {
        // The body failed FastAPI's own shape checks before the handler
        // ran (e.g. more funds than the list allows). It is genuinely
        // invalid -- surface it and block Run, same as any other error.
        return { errors: [{ msg: cause.message }] };
      }
      throw cause;
    }
  },

  // -- Live (read-only, plus the one halt) ---------------------------------

  /** Ledger store paths; see types/telemetry.ts describeStore. */
  stores: () => request<string[]>("/api/live/stores"),

  liveState: (path: string) => request<LiveState>(`/api/live/state?${query({ path })}`),

  activity: (path: string, limit = 200) =>
    request<Activity[]>(`/api/live/activity?${query({ path, limit })}`),

  liveBars: (symbol: string, limit = 780) =>
    request<Bars>(`/api/live/bars?${query({ symbol, limit })}`),

  indicators: (symbol: string, period = 14) =>
    request<Rsi>(`/api/live/indicators?${query({ symbol, period })}`),

  /** Blocks new buys; answers with the store's state read back. */
  halt: (path: string, reason: string) => post<LiveState>("/api/live/halt", { path, reason }),

  // -- ML research (read-only; see server/ml_insights.py) ------------------

  mlSources: () => request<MlSeries[]>("/api/ml/sources"),

  mlDatasets: () => request<ByTicker<Dataset>>("/api/ml/datasets"),

  mlLabels: () => request<string[]>("/api/ml/labels"),

  /** Throws ApiError 404 when nobody has run the tool for this label yet --
   * the message names the command to run. */
  mlEvaluation: (label: string) => request<ByTicker<Eval>>(`/api/ml/evaluation?${query({ label })}`),

  mlAblation: (label: string) => request<ByTicker<Ablation>>(`/api/ml/ablation?${query({ label })}`),

  /**
   * The static export, for looking at a run without the server running.
   * Returns null rather than throwing when absent: no export is a normal
   * state on a fresh checkout, not a failure.
   *
   * A file left over from before the wire contract was condensed has
   * funds shaped like the OLD MultiFundBacktestReport (`executions`,
   * `equity_curve`, no `cells`) -- this fetch bypasses server/contract.py
   * entirely, so nothing translates it. Rather than let every consumer
   * crash on a missing field, treat a shape that isn't current the same
   * as no export at all.
   */
  staticReport: async (): Promise<Report | null> => {
    try {
      const response = await fetch("/data/backtest_report.json");
      if (!response.ok) return null;
      const body = (await response.json()) as Report;
      const funds = Object.values(body.funds ?? {});
      if (funds.length === 0 || funds.some((fund) => !Array.isArray(fund.cells))) {
        return null;
      }
      return body;
    } catch {
      return null;
    }
  },
};
