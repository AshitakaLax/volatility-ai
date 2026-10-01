/**
 * The "View full detail" request. Each case below is one where the wrong
 * answer still submits fine and still draws a plausible chart -- it just
 * re-runs a different backtest than the cell it is labelled as.
 */
import { describe, expect, it } from "vitest";

import type { Cell, Metrics } from "@/types/backtest";

import { buildDetailRequest } from "./detailRun";

const metrics = {
  net_yield_pct: 0,
  cagr_pct: 0,
  max_drawdown_pct: 0,
  sharpe_ratio: 0,
  sortino_ratio: 0,
  profit_factor: 0,
  win_rate_pct: 0,
  max_consecutive_losses: 0,
  stuck_capital_value: 0,
  capital_velocity_index: 0,
  harvest_to_stuck_ratio: 0,
  avg_hold_duration: 0,
  total_trades: 0,
  closed_trades: 0,
  open_trades: 0,
  signal_exits: 0,
  final_equity: 0,
} satisfies Metrics;

function cell(over: Partial<Cell> = {}): Cell {
  return { grid: 0.01, target: 0.005, params: { period: 14 }, m: metrics, ...over };
}

const REPORT = { model: "rsi", fill: "intrabar", no_loss: true };
const FUND = {
  bars: {
    start: "2024-03-01T14:30:00+00:00",
    end: "2024-03-27T19:59:00+00:00",
    count: 7800,
  },
};

describe("buildDetailRequest", () => {
  it("ends on the last bar's UTC DATE, not its timestamp", () => {
    // window() keeps bars < end + 1 day. The full timestamp would have
    // pulled in up to a day of bars past the original's last one.
    const request = buildDetailRequest(REPORT, "TQQQ", FUND, cell(), undefined)!;
    expect(request.end).toBe("2024-03-27");
  });

  it("starts on the first bar's exact timestamp", () => {
    const request = buildDetailRequest(REPORT, "TQQQ", FUND, cell(), undefined)!;
    expect(request.start).toBe("2024-03-01T14:30:00+00:00");
  });

  it("sends no bar cap -- the server refuses one under 500, which blocked short runs", () => {
    const short = { bars: { ...FUND.bars, count: 390 } };
    const request = buildDetailRequest(REPORT, "TQQQ", short, cell(), undefined)!;
    expect(request).not.toHaveProperty("limit");
  });

  it("carries the original's cash yield, including an explicit 0 (accrual off)", () => {
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell(), 0.033)!.cash_yield_pct).toBe(0.033);
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell(), 0)!.cash_yield_pct).toBe(0);
  });

  it("omits the cash yield when unknown, leaving the smart historical default", () => {
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell(), undefined)).not.toHaveProperty(
      "cash_yield_pct",
    );
    // An archived request can carry null for "not set".
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell(), null)).not.toHaveProperty(
      "cash_yield_pct",
    );
  });

  it("reproduces exactly one configuration on one fund", () => {
    const request = buildDetailRequest(
      REPORT,
      "QQQ",
      FUND,
      cell({ grid: 0.0075, target: 0.03, params: { period: 7, oversold_threshold: 25 } }),
      undefined,
    )!;
    expect(request.tickers).toEqual(["QQQ"]);
    expect(request.grid_steps).toEqual([0.0075]);
    expect(request.targets).toEqual([0.03]);
    expect(request.params).toEqual({ period: 7, oversold_threshold: 25 });
    expect(request.model).toBe("rsi");
    expect(request.fill).toBe("intrabar");
    expect(request.no_loss).toBe(true);
  });

  it("is null for a cell with no grid step or target to submit", () => {
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell({ grid: null }), undefined)).toBeNull();
    expect(buildDetailRequest(REPORT, "TQQQ", FUND, cell({ target: null }), undefined)).toBeNull();
  });

  it("falls back to close fills and the server's default model when the report has neither", () => {
    const request = buildDetailRequest(
      { model: null, fill: null, no_loss: true },
      "TQQQ",
      FUND,
      cell(),
      undefined,
    )!;
    expect(request.fill).toBe("close");
    expect(request).not.toHaveProperty("model");
  });
});
