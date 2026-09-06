#!/usr/bin/env python
"""Export a MultiFundBacktestReport as JSON, for the web UI.

--------------------------------------------------------------------
WHY THIS EXISTS BEFORE THE SERVER DOES

The React app needs realistic data to be built against, and the API in
server/ is Phase 2. Writing the same payload to disk first means the
frontend is developed against real numbers from the real engine rather
than hand-made fixtures that agree with nothing -- and it stays useful
afterwards, since a static export is the one way to look at a run on a
machine that is not running the server.

The shape here IS the wire contract. server/backtest.py serialises the
same structure from the same helpers, so the two cannot drift into
disagreeing about what a BacktestExecution looks like.

--------------------------------------------------------------------
WHERE matched_buy_id COMES FROM

The engine's blotter carries `lot_id` on BOTH sides -- the buy row gets
the id register_buy is about to assign, the sell row gets the id of the
lot it closed. They are the same value, and that is the entire mechanism
behind cycle connectors, the open-vs-closed filter, and per-trade
metrics.

The published contract names it `matched_buy_id` on sells, so the
mapping happens HERE rather than by storing a redundant column in the
engine: one join key in the data, one contract name on the wire.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.strategy_registry import resolve_strategy

# Every instrument with a full-history minute file in data/. Kept here
# rather than discovered by glob so a half-downloaded file cannot
# silently become a fund in the comparison view.
KNOWN_DATA = {
    "TQQQ": "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv",
    "QQQ": "data/QQQ_1Min_sip_all_rth_2016-01-01_2026-09-05.csv",
    "RSP": "data/RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv",
    "SOXL": "data/SOXL_1Min_sip_all_rth_2016-01-01_2026-09-03.csv",
    "SQQQ": "data/SQQQ_1Min_sip_all_ext_2016-01-01_2026-09-01.csv",
}


def executions(blotter: pd.DataFrame, ticker: str) -> list[dict]:
    """Blotter rows as BacktestExecution objects.

    Returns [] for an empty blotter rather than raising: a run that
    never traded is a real result, and the UI should render "no
    executions" rather than an error.
    """
    if blotter is None or blotter.empty:
        return []

    out: list[dict] = []
    for row in blotter.itertuples():
        side = str(row.side).upper()
        lot_id = getattr(row, "lot_id", None)
        record = {
            # The lot id is not unique across a lot's rows -- one buy and
            # possibly several partial sells share it -- so the order id
            # is qualified by side and bar to stay a real key.
            "order_id": f"{lot_id}-{side.lower()}-{getattr(row, 'bar_index', 0)}",
            "ticker": getattr(row, "ticker", ticker),
            "type": side,
            "price": round(float(row.price), 6),
            "shares": round(float(row.qty), 6),
            "timestamp": pd.Timestamp(row.timestamp).isoformat(),
        }
        # OMITTED, not zeroed, while the 14-period window is seeding. A
        # zero would filter as "extremely oversold" and put the run's
        # first trades in every RSI<30 query -- exactly backwards.
        rsi = getattr(row, "rsi", None)
        if rsi is not None and not pd.isna(rsi):
            record["rsi_at_entry"] = round(float(rsi), 2)
        if side == "SELL":
            record["matched_buy_id"] = lot_id
            profit = getattr(row, "profit_realized", None)
            if profit is not None and not pd.isna(profit):
                record["profit_realized"] = round(float(profit), 6)
            reason = getattr(row, "sell_reason", None)
            if reason is not None and not pd.isna(reason):
                record["sell_reason"] = str(reason)
        out.append(record)
    return out


def fund_metrics(metrics: dict, ticker: str) -> dict:
    """The engine's metrics dict as a FundPerformanceMetrics object.

    Read by .get with defaults so an older result file -- one produced
    before the UI metrics were added -- still renders, with the missing
    figures as zero rather than crashing the page.
    """
    return {
        "ticker": ticker,
        "net_yield_pct": round(float(metrics.get("Total Return %", 0.0)), 4),
        "cagr_pct": round(float(metrics.get("CAGR %", 0.0)), 4),
        "max_drawdown_pct": round(float(metrics.get("Max Drawdown %", 0.0)), 4),
        "sharpe_ratio": round(float(metrics.get("Sharpe", 0.0)), 4),
        "sortino_ratio": round(float(metrics.get("Sortino", 0.0)), 4),
        "profit_factor": round(float(metrics.get("Profit Factor", 0.0)), 4),
        "win_rate_pct": round(float(metrics.get("Win Rate %", 0.0)), 4),
        "max_consecutive_losses": int(metrics.get("Max Consecutive Losses", 0)),
        "stuck_capital_value": round(float(metrics.get("Stuck Capital Value", 0.0)), 2),
        "capital_velocity_index": round(float(metrics.get("Capital Velocity Index", 0.0)), 4),
        "harvest_to_stuck_ratio": round(float(metrics.get("Harvest to Stuck Ratio", 0.0)), 4),
        "avg_hold_duration": round(float(metrics.get("Average Hold Duration", 0.0)), 2),
        # CALENDAR-YEAR EXTREMES. The worst year is the one this project
        # keeps coming back to: a strategy is judged on what it does in
        # the year it does worst, not on a ten-year average that a single
        # 2020 can carry. It is also the metric a ranking most needs and
        # the one an average hides.
        "worst_year_pct": round(float(metrics.get("Worst Year Return %", 0.0)), 4),
        "best_year_pct": round(float(metrics.get("Best Year Return %", 0.0)), 4),
        "avg_annual_pct": round(float(metrics.get("Average Annual Return %", 0.0)), 4),
        "return_over_drawdown": round(
            float(metrics.get("Return/Drawdown", 0.0)),
            4,
        ),
        "total_trades": int(metrics.get("Trade Count", 0)),
        "closed_trades": int(metrics.get("Closed Trade Count", 0)),
        "open_trades": int(metrics.get("Open Trade Count", 0)),
        "signal_exits": int(metrics.get("Signal Exit Count", 0)),
        "final_equity": round(float(metrics.get("Final Equity", 0.0)), 2),
    }


def equity_series(curve: pd.Series) -> dict:
    """Daily equity, plus its normalised form for the overlay chart.

    Normalised to 100 at the first bar, which is what makes two funds
    with different starting prices comparable on one axis -- the
    multi-fund view's whole purpose.
    """
    if curve is None or len(curve) == 0:
        return {"dates": [], "equity": [], "normalized": []}
    try:
        daily = curve.resample("1D").last().dropna()
    except (TypeError, ValueError):
        daily = curve.dropna()
    first = float(daily.iloc[0]) or 1.0
    return {
        "dates": [pd.Timestamp(ts).strftime("%Y-%m-%d") for ts in daily.index],
        "equity": [round(float(v), 2) for v in daily.to_numpy()],
        "normalized": [round(float(v) / first * 100.0, 4) for v in daily.to_numpy()],
    }


def run_one(ticker: str, path: str, config: BacktestConfig, limit: int | None) -> dict:
    frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    if limit:
        frame = frame.tail(limit)
    kwargs = config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
    kwargs["return_full_results"] = True
    kwargs["symbol"] = ticker
    _, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)
    result = full[0]
    return {
        "metrics": fund_metrics(result.metrics, ticker),
        "executions": executions(result.trade_blotter, ticker),
        "equity_curve": equity_series(result.equity_curve),
        "bars": {
            "start": pd.Timestamp(frame.index[0]).isoformat(),
            "end": pd.Timestamp(frame.index[-1]).isoformat(),
            "count": len(frame),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="config/staging.yaml")
    parser.add_argument("--tickers", nargs="+", default=["TQQQ"])
    parser.add_argument("--out", default="web/public/data/backtest_report.json")
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Use only the last N bars. One full run is ~23s on 10y of minute data.",
    )
    args = parser.parse_args(argv)

    config = BacktestConfig.from_yaml(args.config)
    config.validate()

    funds: dict[str, dict] = {}
    for ticker in args.tickers:
        path = KNOWN_DATA.get(ticker)
        if path is None or not Path(path).exists():
            print(f"[export] SKIP {ticker}: no data file (see KNOWN_DATA)", flush=True)
            continue
        print(f"[export] {ticker} ...", flush=True)
        funds[ticker] = run_one(ticker, path, config, args.limit)
        print(f"[export]   {len(funds[ticker]['executions'])} executions", flush=True)

    report = {
        "run_id": args.run_id or f"local-{pd.Timestamp.now('UTC'):%Y%m%d-%H%M%S}",
        "parameters": {
            "grid_step_pct": config.grid.steps[0] if config.grid.steps else None,
            "profit_target_pct": (
                config.grid.profit_targets[0] if config.grid.profit_targets else None
            ),
            "sizing_model": config.strategy.strategy_id,
            "fill_model": config.execution.fill_model,
            "enforce_no_loss": config.execution.enforce_no_loss,
        },
        "timeframe": {
            "start": min((f["bars"]["start"] for f in funds.values()), default=None),
            "end": max((f["bars"]["end"] for f in funds.values()), default=None),
            "interval": "1Min",
        },
        "funds": funds,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[export] {len(funds)} fund(s) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
