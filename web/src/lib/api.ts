/**
 * Typed access to the Python API.
 *
 * Everything goes through the Vite dev proxy (`/api`, `/ws`), so the
 * browser only ever talks to one origin. That is why there is no base
 * URL here: introducing one would make development and production
 * differ in exactly the way CORS bugs hide in.
 */
import type {
  BacktestRunRequest,
  BarSeries,
  BacktestRunState,
  HistoryRow,
  MultiFundBacktestReport,
} from "@/types/backtest";
import type { DeploymentState, HaltResponse, IndicatorReading } from "@/types/telemetry";

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

export interface Capabilities {
  live_read: boolean;
  halt: boolean;
  liquidate: boolean;
  parameter_override: boolean;
  backtest_submit: boolean;
}

export interface DeploymentInfo {
  git_commit: string | null;
  git_branch: string | null;
  /** null means "could not tell", which is different from false. */
  git_dirty: boolean | null;
  started_at: number;
  uptime_seconds: number;
  python: string;
  pid: number;
  /** null outside a container -- cgroup is the only place these are true. */
  memory_mb: number | null;
  memory_limit_mb: number | null;
  cpu_pct: number | null;
  containerised: boolean;
}

/** What a sizing model needs, and a working starting point. */
export interface SizingDetail {
  /** Constructor arguments with no default. Sending none of these is
   * what made every non-`fixed` model fail. */
  required: string[];
  defaults: Record<string, number | string | boolean>;
}

export interface FundAvailability {
  ticker: string;
  path: string;
  available: boolean;
}

export const api = {
  health: () => request<{ status: string; capabilities: Capabilities }>("/api/health"),

  deployment: () => request<DeploymentInfo>("/api/deployment"),

  funds: () =>
    request<{
      funds: FundAvailability[];
      sizing_models: string[];
      sizing_details: Record<string, SizingDetail>;
    }>("/api/backtest/funds"),

  bars: (ticker: string, start?: string | null, end?: string | null, maxPoints = 3000) => {
    const query = new URLSearchParams({ ticker, max_points: String(maxPoints) });
    if (start) query.set("start", start);
    if (end) query.set("end", end);
    return request<BarSeries>(`/api/backtest/bars?${query.toString()}`);
  },

  history: () => request<{ rows: HistoryRow[]; runs: number }>("/api/backtest/history"),

  historyRun: (runId: string) =>
    request<BacktestRunState>(`/api/backtest/history/${runId}`),

  runs: () => request<{ runs: BacktestRunState[] }>("/api/backtest/runs"),

  run: (runId: string) => request<BacktestRunState>(`/api/backtest/runs/${runId}`),

  submitRun: (body: BacktestRunRequest) =>
    request<BacktestRunState>("/api/backtest/runs", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  liveState: (path: string) =>
    request<DeploymentState>(`/api/live/state?path=${encodeURIComponent(path)}`),

  indicators: (symbol: string, period = 14) =>
    request<IndicatorReading>(
      `/api/live/indicators?symbol=${encodeURIComponent(symbol)}&period=${period}`,
    ),

  stores: () =>
    request<{ stores: { path: string; label: string; paper: boolean }[] }>("/api/live/stores"),

  halt: (path: string, reason: string) =>
    request<HaltResponse>("/api/live/halt", {
      method: "POST",
      body: JSON.stringify({ path, reason }),
    }),

  /**
   * The static export, for looking at a run without the server running.
   * Returns null rather than throwing when absent: no export is a
   * normal state on a fresh checkout, not a failure.
   */
  staticReport: async (): Promise<MultiFundBacktestReport | null> => {
    try {
      const response = await fetch("/data/backtest_report.json");
      if (!response.ok) return null;
      return (await response.json()) as MultiFundBacktestReport;
    } catch {
      return null;
    }
  },
};
