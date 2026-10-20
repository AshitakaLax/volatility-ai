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
  Fill,
  FillsPage,
  FillsQuery,
  HistoryFacets,
  HistoryFund,
  HistoryPage,
  HistoryQuery,
  Report,
  Run,
  RunOp,
  RunReq,
  RunSummary,
  Shard,
  ShardList,
  ShardOp,
  ShardSchedule,
  SubmitResponse,
  Validation,
} from "@/types/backtest";
import type { Ablation, ByTicker, Dataset, Eval, MlSeries } from "@/types/ml";
import type {
  AlgorithmView,
  ChangeCheck,
  ChangeRequest,
  CommandRequest,
  CommandRow,
  DeploymentDetail,
  DeploymentSummary,
  QueuedCommand,
  TraderFill,
} from "@/types/control";
import type { Activity, Rsi } from "@/types/telemetry";
import type { SystemStatus, WarehouseStatus } from "@/types/warehouse";

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
 * server rather than compiled in. `control` is the Live page's commands
 * (server/live_control.py); what each deployment takes is its own config's
 * live.control. Liquidation is never listed, by design.
 */
export interface Health {
  caps: ("live" | "control" | "backtest" | "ml")[];
  /** Where sweeps run; null when this server runs them itself. */
  upstream: string | null;
  build: {
    commit: string | null;
    branch: string | null;
    /** null means "could not tell", which is different from false. */
    dirty: boolean | null;
    /** A fingerprint of the code this process runs -- the same one a trader
     * reports (engine/core/build_info.py), so the two can be compared. */
    code?: string | null;
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

  /** Funds with stored results -- Run History's required Fund picker. */
  historyFunds: () => request<HistoryFund[]>("/api/backtest/history/funds"),

  /** One fund's filter options: algorithms, fill models, numeric fields. */
  historyFacets: (ticker: string) =>
    request<HistoryFacets>(`/api/backtest/history/facets?${query({ ticker })}`),

  /** One page of one fund's history, filtered and sorted server-side.
   * History is never downloaded whole: it is uncapped and unbounded. */
  historyQuery: (body: HistoryQuery) => post<HistoryPage>("/api/backtest/history/query", body),

  /** One page of a fund's fills (or buy/sell cycles), filtered the way the
   * result page filters them, with counts over the whole filtered set.
   * Reports never carry fills inline -- a busy run's are ~850k rows. */
  fills: <Row = Fill>(runId: string, params: FillsQuery) =>
    request<FillsPage<Row>>(
      `/api/backtest/runs/${runId}/fills?${query({ ...params })}`,
    ),

  /** Every filtered fill as CSV, streamed by the server. */
  fillsCsvUrl: (runId: string, params: Omit<FillsQuery, "view" | "cycles" | "offset" | "limit">) =>
    `/api/backtest/runs/${runId}/fills.csv?${query({ ...params })}`,

  runs: () => request<{ runs: RunSummary[]; paused: boolean }>("/api/backtest/runs"),

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

  // -- Live: deployments by id (read-only) and their commands ---------------

  /** Every deployment in config/deployments.yaml, for the strip. */
  deployments: () => request<DeploymentSummary[]>("/api/live/deployments"),

  /** One deployment: its summary, its ledger's LiveState, its commands. */
  deployment: (id: string) =>
    request<DeploymentDetail>(`/api/live/deployments/${encodeURIComponent(id)}`),

  /** The ledger's revision log, newest first. */
  activity: (id: string, limit = 200) =>
    request<Activity[]>(
      `/api/live/deployments/${encodeURIComponent(id)}/activity?${query({ limit })}`,
    ),

  /** The minute bars the deployment's trader traded on -- its own feed,
   * not the warehouse's -- for the last `sessions` sessions. */
  deploymentBars: (id: string, sessions = 2) =>
    request<Bars>(
      `/api/live/deployments/${encodeURIComponent(id)}/bars?${query({ sessions })}`,
    ),

  /** Every fill the trader booked in the last `sessions` sessions, oldest
   * first, each sale with what it fetched against what its lot cost. */
  deploymentFills: (id: string, sessions = 1) =>
    request<TraderFill[]>(
      `/api/live/deployments/${encodeURIComponent(id)}/fills?${query({ sessions })}`,
    ),

  liveBars: (symbol: string, limit = 780) =>
    request<Bars>(`/api/live/bars?${query({ symbol, limit })}`),

  indicators: (symbol: string, period = 14) =>
    request<Rsi>(`/api/live/indicators?${query({ symbol, period })}`),

  /** Queue a command for the deployment's trader (server/live_control.py).
   * Accepted is not applied: the returned command's status says when. */
  sendCommand: (id: string, body: CommandRequest) =>
    post<QueuedCommand>(`/api/live/deployments/${encodeURIComponent(id)}/commands`, body),

  /** What the deployment trades, its profiles and every strategy's live
   * capability here. */
  algorithm: (id: string) =>
    request<AlgorithmView>(`/api/live/deployments/${encodeURIComponent(id)}/algorithm`),

  /** Dry-run a switch: the trader's reasons to refuse it, or its impact. */
  checkAlgorithm: (id: string, body: ChangeRequest) =>
    post<ChangeCheck>(`/api/live/deployments/${encodeURIComponent(id)}/algorithm/check`, body),

  /** Withdraw a queued command; 409 once its trader has taken it. */
  cancelCommand: (id: string, commandId: string, operator: string) =>
    post<CommandRow>(
      `/api/live/deployments/${encodeURIComponent(id)}/commands/${encodeURIComponent(commandId)}/cancel`,
      { operator },
    ),

  // -- ML research (read-only; see server/ml_insights.py) ------------------

  mlSources: () => request<MlSeries[]>("/api/ml/sources"),

  mlDatasets: () => request<ByTicker<Dataset>>("/api/ml/datasets"),

  mlLabels: () => request<string[]>("/api/ml/labels"),

  /** Throws ApiError 404 when nobody has run the tool for this label yet --
   * the message names the command to run. */
  mlEvaluation: (label: string) => request<ByTicker<Eval>>(`/api/ml/evaluation?${query({ label })}`),

  mlAblation: (label: string) => request<ByTicker<Ablation>>(`/api/ml/ablation?${query({ label })}`),

  // -- The Warehouse tab (read-only; see server/warehouse_status.py) --------

  /** Funds and their freshness, sweeps and simulations, storage. Cached
   * server-side: polling it is cheap. */
  warehouse: () => request<WarehouseStatus>("/api/backtest/warehouse"),

  /** The machine and the queue, read fresh on every call. */
  system: () => request<SystemStatus>("/api/backtest/system"),

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
