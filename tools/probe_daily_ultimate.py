#!/usr/bin/env python
"""
The daily-ultimate sweep (docs/research/daily-ultimate.md): which fund, buy
and sell reach the owner's goal of +0.1% of equity a session -- measured the
way the goal is stated, per session, against holding the same fund.

    python tools/probe_daily_ultimate.py --stage funds  --out DIR [--jobs N]
    python tools/probe_daily_ultimate.py --stage grid   --fund TQQQ --out DIR
    python tools/probe_daily_ultimate.py --stage pairs  --fund TQQQ --out DIR
    python tools/probe_daily_ultimate.py --stage robust --fund TQQQ --out DIR
    python tools/probe_daily_ultimate.py --report DIR

Stages run in that order: `pairs` and `robust` start from the configuration
`grid` chose (read from DIR). `--report` prints every stage and writes
DIR/report.md. A run whose name is already in DIR/results.jsonl is skipped,
so re-running a stage resumes it.

--------------------------------------------------------------------
HOW EVERY RUN IS MEASURED

  fills      intrabar, CAUSAL booking (engine and within-bar lookahead both
             fixed) -- the server's runs and the warehouse's sim_results use
             `level`, which the algorithm ledger records as biased
  costs      config/ultimate_tqqq.yaml's dynamic slippage (0.5 bp + 0.3 x
             the bar's range); slippage x4 and x10 in the robust stage
  cash       no yield on idle cash (cash_yield_pct 0.0): the conservative
             case -- Fidelity's core position would pay a money-market rate
  history    each fund's whole warehouse history from 2016-01-04, one
             process per configuration, nothing written to the warehouse or
             Run History
  scored     from the later of 2017-01-03 and the fund's 253rd session: the
             regime buys nothing for its first ~250 sessions, so a year of
             warm-up would count against it. Buy-and-hold is scored over
             the same window.

The goal, GOAL = 0.001 a session, is 28.6% a year over 252 sessions. Each run
reports its geometric daily return (the CAGR as a per-session rate), the
share of sessions that made the goal and the share that made money, its
drawdown, worst day and month, and the same for buy-and-hold.

--------------------------------------------------------------------
THE CHOICE

The highest geometric daily return among the configurations whose maximum
drawdown stays within DD_BUDGET (30%), ties broken by the share of sessions
at the goal; the shallowest drawdown if none does. The same rule is applied
to 2017-2021 alone and scored on 2022 onward (`walk-forward` in the report):
a choice that only holds with hindsight shows up there.

The first rule tried -- among configurations reaching GOAL, the shallowest
drawdown -- is still reported beside it ("steadiest"), because it failed that
check: on TQQQ it picked a fixed-lot cell that barely cleared the goal in
2017-2021 and made 0.046% a session afterwards, 184th of 300. A rule that
rewards clearing a bar by the least margin picks the cell that falls short.

--------------------------------------------------------------------
THE DESIGN BEING SCALED

TQQQ's: the validated Ultimate shape (step 0.2%, NATR(14) regime against its
100-session median, bear filter 50% / 250 sessions, reversal lots after a
-8% session with a +8% target), lots compounded from each session's opening
equity. On another fund every price distance -- step, target, reversal
threshold and target -- is multiplied by that fund's daily volatility over
TQQQ's, measured from the warehouse.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

TZ = "America/New_York"
GOAL = 0.001
START = "2016-01-04"
SCORE_FROM = "2017-01-03"
SPLIT = "2022-01-01"  # walk-forward: choose before, score from
FLAT = 1e-4  # a session within 1 bp of flat is flat (cash days are not "up")
DD_BUDGET = 30.0  # THE CHOICE's drawdown budget, in percent

FUNDS = ("TQQQ", "SOXL", "QQQ", "SPY", "IWM", "RSP", "XBI", "SPYD", "COWZ", "EEM", "URSP_SIM")

SLIPPAGE = {
    "model_type": "dynamic_slippage",
    "commission_per_trade": 0.0,
    "base_bps": 0.5,
    "vol_multiplier": 0.3,
}

# TQQQ's design (module docstring). Distances are scaled per fund.
BUY = {
    "bars_per_day": 387,
    "lookback_days": 0.02,
    "event_day_boost_multiplier": 2.5,
    "earnings_day_boost_multiplier": 1.5,
    "vol_scale_exponent": -1.5,
    "vol_fast_days": 0.25,
    "vol_slow_days": 10.0,
    "vol_scale_min": 0.25,
    "vol_scale_max": 3.0,
    "vol_measure": "stdev",
    "volume_scale_exponent": -1.0,
    "natr_period": 14,
    "natr_lookback": 100,
    "regime_min_hold": 5,
    "bear_dd": 0.5,
    "bear_window": 250,
    "turbulent_mode": "reversal",
    "reversal_lot_pct": 0.2,
    "reversal_max_lots": 4,
    "liquidate_minute": 60,
}
STEP, REVERSAL_THRESHOLD, REVERSAL_TARGET = 0.002, -0.08, 0.08
HARVEST_MIN_GAIN, EOD_MINUTE = 0.002, 380

TARGETS = (0.02, 0.04, 0.08, 0.12)
LOTS = (0.002, 0.004, 0.008)
# How lots leave besides their own target and the regime exit.
SELL_MODES: dict[str, dict] = {
    "hold": {},
    "eod": {"eod_harvest_minute": EOD_MINUTE},
    "lock": {"goal_lock": True},
    "eod+lock": {"eod_harvest_minute": EOD_MINUTE, "goal_lock": True},
}
# What the book does while the regime is turbulent. Compounded, Ultimate's
# reversal lots (20% of equity each, up to four) carry most of 2022's loss
# -- the fixed-dollar original shrank them to a sliver of a grown account --
# so their size is an axis of its own.
TURBULENT: dict[str, dict] = {
    "cash": {"turbulent_mode": "cash"},
    "rev5": {"turbulent_mode": "reversal", "reversal_lot_pct": 0.05},
    "rev10": {"turbulent_mode": "reversal", "reversal_lot_pct": 0.10},
    "rev20": {"turbulent_mode": "reversal", "reversal_lot_pct": 0.20},
}


# --------------------------------------------------------------- the plan


def _name(*parts: Any) -> str:
    return " ".join(str(p) for p in parts if p not in (None, ""))


def _config(fund: str, strategy_id: str, params: dict, step: float, target: float, **over) -> dict:
    from research.strategies.strategy_registry import may_realize_loss

    return {
        "strategy": {"strategy_id": strategy_id, "strategy_params": params},
        "grid": {"steps": [step], "profit_targets": [target]},
        "backtest": {"symbol": fund, "initial_cash": 100_000.0},
        "costs": over.get("costs", SLIPPAGE),
        "risk": over.get("risk", {}),
        "search": {"strategy": "grid", "rank_by": "Total Return %"},
        "execution": {
            "on_flat_reentry": "stale_reference",
            "intrabar_priority": "sell_first",
            "fill_model": "intrabar",
            "intrabar_fill": "causal",
            "enforce_no_loss": True,
            "allow_signal_exit": may_realize_loss(strategy_id, params),
            "cash_yield_pct": 0.0,
        },
        "output": {"return_full_results": False},
    }


def daily_ultimate(
    fund: str,
    scale: float,
    target: float,
    lot: float,
    mode: str,
    pause: bool = False,
    compound: bool = True,
    turbulent: str = "rev20",
    **over,
) -> tuple[dict, float, float]:
    """(strategy_params, step, target) for daily_ultimate on `fund`."""
    params = {
        **BUY,
        **TURBULENT[turbulent],
        "per_lot_pct": lot,
        "reversal_threshold": round(REVERSAL_THRESHOLD * scale, 6),
        "reversal_target": round(REVERSAL_TARGET * scale, 6),
        "compound_lots": compound,
        "daily_goal": GOAL,
        "goal_pause_buys": pause,
        "harvest_min_gain": HARVEST_MIN_GAIN,
        **SELL_MODES[mode],
    }
    params.update(over.pop("params", {}))
    step = over.pop("step", round(STEP * scale, 6))
    return params, step, round(target * scale, 6)


def _spec(stage: str, name: str, fund: str, config: dict, **meta) -> dict:
    return {"stage": stage, "name": name, "fund": fund, "config": config, "meta": meta}


def plan_funds(scales: dict[str, float]) -> list[dict]:
    """Every fund, the design scaled to it: three targets, three lot sizes,
    lots held or harvested at the close, a cash or small reversal sleeve."""
    out = []
    for fund in FUNDS:
        for target in TARGETS[:3]:
            for lot in LOTS:
                for mode in ("hold", "eod"):
                    for turbulent in ("cash", "rev5"):
                        params, step, tgt = daily_ultimate(
                            fund, scales[fund], target, lot, mode, turbulent=turbulent
                        )
                        out.append(
                            _spec(
                                "funds",
                                _name("funds", fund, f"t{target}", f"lot{lot}", mode, turbulent),
                                fund,
                                _config(fund, "daily_ultimate", params, step, tgt),
                                target=target,
                                lot=lot,
                                mode=mode,
                                turbulent=turbulent,
                                scale=scales[fund],
                            )
                        )
    return out


def plan_grid(fund: str, scale: float) -> list[dict]:
    """One fund in depth: target x lot size x turbulent sleeve x how lots
    leave x the goal pausing buys, all compounded; and Ultimate itself
    (fixed-dollar lots, its 20% reversal sleeve, held) at each target and
    lot size, as the control."""
    out = []
    for target in TARGETS:
        for lot in LOTS:
            cells = [
                (mode, pause, True, turbulent)
                for turbulent in ("cash", "rev5", "rev10")
                for mode in SELL_MODES
                for pause in (False, True)
            ]
            cells.append(("hold", False, False, "rev20"))
            for mode, pause, compound, turbulent in cells:
                params, step, tgt = daily_ultimate(
                    fund, scale, target, lot, mode, pause, compound, turbulent=turbulent
                )
                name = _name(
                    "grid",
                    fund,
                    f"t{target}",
                    f"lot{lot}",
                    turbulent,
                    mode,
                    "pause" if pause else "",
                    "" if compound else "fixed-lots (ultimate)",
                )
                out.append(
                    _spec(
                        "grid",
                        name,
                        fund,
                        _config(fund, "daily_ultimate", params, step, tgt),
                        target=target,
                        lot=lot,
                        turbulent=turbulent,
                        mode=mode,
                        pause=pause,
                        compound=compound,
                    )
                )
    return out


def _split(params: dict) -> tuple[dict, dict]:
    """daily_ultimate's params as the daily_ultimate buy and the
    daily_ultimate_exit sell (entries.py and book_exits.py): the buy refuses
    what sells, the sell takes what its constructor names. daily_goal is
    both's -- the buy pauses on it, the sell locks on it."""
    import inspect

    from research.composition import entries
    from research.composition.book_exits import DailyUltimateExit

    selling = entries.sell_params("daily_ultimate")
    exit_params = set(inspect.signature(DailyUltimateExit.__init__).parameters) - {"self"}
    buy = {k: v for k, v in params.items() if k not in selling}
    sell = {k: v for k, v in params.items() if k in exit_params}
    return buy, sell


def plan_pairs(fund: str, base: dict) -> list[dict]:
    """The buy x sell alternatives at the grid's choice: its buy, the same
    buy compounded, Ultimate's and the champion's (no regime on the buy
    side); its sell, that sell with the closing harvest or the goal lock
    added, Ultimate's regime exit, the daily take-profits alone (no regime
    exit) and the plain target."""
    params, step, target = base["params"], base["step"], base["target"]
    buy_daily, sell_daily = _split(params)
    daily_keys = {"compound_lots", "daily_goal", "goal_pause_buys"}
    buy_ultimate = {k: v for k, v in buy_daily.items() if k not in daily_keys}
    daily_sell_keys = {"daily_goal", "goal_lock", "eod_harvest_minute", "harvest_min_gain"}
    regime = {k: v for k, v in sell_daily.items() if k not in daily_sell_keys}
    min_gain = params.get("harvest_min_gain", HARVEST_MIN_GAIN)
    champion = {
        k: params[k]
        for k in (
            "bars_per_day",
            "per_lot_pct",
            "lookback_days",
            "event_day_boost_multiplier",
            "earnings_day_boost_multiplier",
            "vol_scale_exponent",
            "vol_fast_days",
            "vol_slow_days",
            "vol_scale_min",
            "vol_scale_max",
            "volume_scale_exponent",
        )
    }
    buys = {
        "daily_ultimate": buy_daily,
        "daily_ultimate compounded": {**buy_daily, "compound_lots": True},
        "ultimate": buy_ultimate,
        "hf_local_reference": champion,
    }
    sells = {
        "daily_ultimate_exit": sell_daily,
        "daily_ultimate_exit +eod": {
            **sell_daily,
            "eod_harvest_minute": EOD_MINUTE,
            "harvest_min_gain": min_gain,
        },
        "daily_ultimate_exit +lock": {
            **sell_daily,
            "daily_goal": GOAL,
            "goal_lock": True,
            "harvest_min_gain": min_gain,
        },
        "ultimate_exit": regime,
        "daily_harvest": {
            "daily_goal": GOAL,
            "goal_lock": True,
            "eod_harvest_minute": EOD_MINUTE,
            "harvest_min_gain": min_gain,
        },
        "fixed_target": {},
    }
    out = []
    for buy_label, buy in buys.items():
        for sell_label, sell in sells.items():
            buy_id, sell_id = buy_label.split()[0], sell_label.split()[0]
            composed = {
                "buy": {"id": buy_id, "params": buy},
                "sell": {"id": sell_id, "params": sell},
            }
            out.append(
                _spec(
                    "pairs",
                    _name("pairs", fund, buy_label, "x", sell_label),
                    fund,
                    _config(fund, "composed", composed, step, target),
                    buy=buy_label,
                    sell=sell_label,
                )
            )
    return out


def plan_robust(fund: str, base: dict) -> list[dict]:
    """The grid's choice with one thing changed at a time."""
    params, step, target = base["params"], base["step"], base["target"]
    variants: list[tuple[str, dict, float, float, dict]] = [
        ("step x0.5", params, step / 2, target, {}),
        ("step x2", params, step * 2, target, {}),
        ("lots x0.5", {**params, "per_lot_pct": params["per_lot_pct"] / 2}, step, target, {}),
        ("lots x1.5", {**params, "per_lot_pct": params["per_lot_pct"] * 1.5}, step, target, {}),
        ("target x0.75", params, step, round(target * 0.75, 6), {}),
        ("target x1.5", params, step, round(target * 1.5, 6), {}),
        ("lots x2", {**params, "per_lot_pct": params["per_lot_pct"] * 2}, step, target, {}),
        ("target x2", params, step, round(target * 2, 6), {}),
        ("compounded", {**params, "compound_lots": True}, step, target, {}),
        ("cash while turbulent", {**params, "turbulent_mode": "cash"}, step, target, {}),
        ("slippage x4", params, step, target, {"costs": {**SLIPPAGE, "base_bps": 2.0}}),
        ("slippage x10", params, step, target, {"costs": {**SLIPPAGE, "base_bps": 5.0}}),
        (
            "regime natr10 -9%/+6%",
            {**params, "natr_period": 10, "reversal_threshold": -0.09, "reversal_target": 0.06},
            step,
            target,
            {},
        ),
        ("bear_window 125", {**params, "bear_window": 125}, step, target, {}),
    ]
    if params.get("eod_harvest_minute") is not None or params.get("goal_lock"):
        variants += [
            ("harvest min gain 0.1%", {**params, "harvest_min_gain": 0.001}, step, target, {}),
            ("harvest min gain 0.5%", {**params, "harvest_min_gain": 0.005}, step, target, {}),
        ]
    if params.get("eod_harvest_minute") is not None:
        variants += [
            ("eod minute 370", {**params, "eod_harvest_minute": 370}, step, target, {}),
            ("eod minute 385", {**params, "eod_harvest_minute": 385}, step, target, {}),
        ]
    if params.get("goal_lock") or params.get("goal_pause_buys"):
        variants += [
            ("goal 0.05%", {**params, "daily_goal": 0.0005}, step, target, {}),
            ("goal 0.2%", {**params, "daily_goal": 0.002}, step, target, {}),
        ]
    return [
        _spec(
            "robust",
            _name("robust", fund, label),
            fund,
            _config(fund, "daily_ultimate", p, s, t, **over),
            variant=label,
        )
        for label, p, s, t, over in variants
    ]


# --------------------------------------------------------------- running one


def _regular_closes(fund: str):
    import pandas as pd

    from engine.warehouse.bars import load_frame

    bars = load_frame(fund)
    bars = bars[bars.index >= pd.Timestamp(START, tz="UTC")]
    ny = bars.index.tz_convert(TZ)
    minutes = ny.hour * 60 + ny.minute
    bars = bars[(minutes >= 570) & (minutes < 960)]
    idx = bars.index.tz_convert(TZ).tz_localize(None)
    return pd.Series(bars["close"].to_numpy(float), index=idx).groupby(idx.normalize()).last()


def score_start(sessions) -> str:
    """The later of SCORE_FROM and the fund's 253rd session."""
    first_year = sessions[min(252, len(sessions) - 1)]
    return max(SCORE_FROM, str(first_year.date()))


def daily_metrics(equity, goal: float = GOAL) -> dict:
    """Per-session statistics of a daily equity (or price) series."""
    import numpy as np

    if len(equity) < 3:
        return {}
    r = equity.pct_change().dropna()
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    growth = float(equity.iloc[-1] / equity.iloc[0])
    cagr = growth ** (1 / years) - 1 if years > 0 and growth > 0 else float("nan")
    peak = equity.cummax()
    dd = float(((peak - equity) / peak).max())
    monthly = equity.resample("ME").last().pct_change().dropna()
    yearly = equity.resample("YE").last()
    yearly = (
        np.concatenate([[equity.iloc[0]], yearly.to_numpy()])[1:]
        / np.concatenate([[equity.iloc[0]], yearly.to_numpy()])[:-1]
        - 1
    )
    per_session = growth ** (1 / len(r)) - 1 if growth > 0 else float("nan")
    return {
        "start": str(equity.index[0].date()),
        "end": str(equity.index[-1].date()),
        "cagr": cagr * 100,
        "geo_daily": per_session * 100,
        "mean_daily": float(r.mean() * 100),
        "max_dd": dd * 100,
        "calmar": cagr / dd if dd else float("nan"),
        "sharpe": float(r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else float("nan"),
        "pct_goal_days": float((r >= goal - 1e-12).mean() * 100),
        "pct_up_days": float((r > FLAT).mean() * 100),
        "pct_flat_days": float((r.abs() <= FLAT).mean() * 100),
        "pct_down_days": float((r < -FLAT).mean() * 100),
        "pct_up_months": float((monthly > FLAT).mean() * 100) if len(monthly) else float("nan"),
        "worst_day": float(r.min() * 100),
        "worst_month": float(monthly.min() * 100) if len(monthly) else float("nan"),
        "years": {
            str(y.year): round(float(v) * 100, 2)
            for y, v in zip(equity.resample("YE").last().index, yearly, strict=True)
        },
    }


def trading_metrics(blotter, sessions, equity, goal: float = GOAL) -> dict:
    """How often it trades, and how often a session's REALISED profit made
    the goal on the session's opening equity."""
    import pandas as pd

    if blotter is None or blotter.empty:
        return {"buys_per_day": 0.0, "sells_per_day": 0.0}
    b = blotter.assign(
        day=pd.to_datetime(blotter["timestamp"], utc=True)
        .dt.tz_convert(TZ)
        .dt.tz_localize(None)
        .dt.normalize()
    )
    b = b[b["day"] >= sessions[0]]
    buys, sells = b[b["side"] == "buy"], b[b["side"] == "sell"]
    pnl = sells["profit_realized"].fillna(0.0).astype(float)
    realized = pnl.groupby(sells["day"]).sum().reindex(sessions, fill_value=0.0)
    opening = equity.shift(1).reindex(sessions)
    n = len(sessions)
    out = {
        "buys_per_day": len(buys) / n,
        "sells_per_day": len(sells) / n,
        "pct_days_selling": float(
            sells.groupby("day").size().reindex(sessions).notna().mean() * 100
        ),
        "pct_days_realized_goal": float((realized >= goal * opening).mean() * 100),
        "pct_days_realized_loss": float((realized < 0).mean() * 100),
        "signal_exit_pnl": float(
            pnl[sells["sell_reason"].astype(str).str.contains("signal")].sum()
        ),
    }
    if "lot_id" in b and len(sells):
        pos = pd.Series(range(n), index=sessions)
        span = (
            sells.groupby("lot_id")["day"].max().map(pos)
            - buys.groupby("lot_id")["day"].min().map(pos)
        ).dropna()
        if len(span):
            out["hold_sessions_median"] = float(span.median())
            out["pct_lots_same_session"] = float((span == 0).mean() * 100)
            out["pct_lots_within_5"] = float((span <= 5).mean() * 100)
    return out


def exposure_metrics(blotter, close, equity, scored_from) -> dict:
    """How much of the account is in the fund: shares held (from the
    blotter) x each bar's close over its equity, from `scored_from` on."""
    import numpy as np
    import pandas as pd

    eq = np.asarray(equity, dtype=float)
    held = np.zeros(len(eq))
    if blotter is not None and not blotter.empty:
        sign = np.where(blotter["side"].to_numpy() == "buy", 1.0, -1.0)
        at = blotter["bar_index"].to_numpy(int)
        np.add.at(held, at, sign * blotter["qty"].to_numpy(float))
    held = np.cumsum(held)
    exposure = np.where(eq > 0, held * np.asarray(close, dtype=float) / np.where(eq > 0, eq, 1), 0)
    day = pd.DatetimeIndex(equity.index).tz_convert(TZ).tz_localize(None).normalize()
    keep = day >= pd.Timestamp(scored_from)
    exposure, day = exposure[keep], day[keep]
    if not len(exposure):
        return {}
    closing = pd.Series(exposure, index=day).groupby(level=0).last()
    return {
        "avg_exposure": float(exposure.mean() * 100),
        "p95_exposure": float(np.percentile(exposure, 95) * 100),
        "max_exposure": float(exposure.max() * 100),
        "pct_sessions_closing_in_cash": float((closing < 1e-6).mean() * 100),
    }


def run_one(spec: dict) -> dict:
    """One configuration, reduced to its metrics. `spec` may name a
    `stress` scenario (tools/stress_paths.py), a `start` other than START,
    and an `end`, the last session it loads."""
    import pandas as pd

    from engine.core.config import BacktestConfig
    from engine.warehouse.bars import load_frame
    from research.optimization.optimization_controller import OptimizationController
    from research.strategies.strategy_registry import resolve_strategy, session_bars
    from tools import stress_paths

    started = time.time()
    config = BacktestConfig.from_dict(spec["config"])
    cls = resolve_strategy(config.strategy.strategy_id)
    bars = load_frame(spec["fund"])
    bars = bars[bars.index >= pd.Timestamp(spec.get("start") or START, tz="UTC")]
    if spec.get("end"):
        bars = bars[bars.index < pd.Timestamp(spec["end"], tz="UTC") + pd.Timedelta(days=1)]
    bars = stress_paths.stressed(bars, spec.get("stress"))
    frame = session_bars(cls, bars, config.strategy.strategy_params)
    kwargs = config.to_run_sweep_kwargs(cls)
    kwargs.update(n_jobs=1, return_full_results=False)
    out: dict[str, Any] = {k: spec[k] for k in ("stage", "name", "fund", "meta")}
    out["stress"], out["start"], out["end"] = spec.get("stress"), spec.get("start"), spec.get("end")
    out["params"] = config.strategy.strategy_params
    out["step"], out["target"] = kwargs["grid_steps"][0], kwargs["profit_targets"][0]

    class Sink:  # the one finished configuration, reduced, then let go
        def open_sweep(self, **_):
            return "probe_daily_ultimate"

        def record(self, *, row, sim_result, elapsed_ms):
            curve = sim_result.equity_curve
            idx = pd.DatetimeIndex(curve.index).tz_convert(TZ).tz_localize(None)
            daily = pd.Series(curve.to_numpy(float), index=idx).groupby(idx.normalize()).last()
            if len(daily) and row.get("Final Equity") is not None:
                daily.iloc[-1] = float(row["Final Equity"])
            start = score_start(daily.index)
            scored = daily[daily.index >= pd.Timestamp(start)]
            out["metrics"] = daily_metrics(scored)
            out["trading"] = trading_metrics(sim_result.trade_blotter, scored.index, daily)
            if len(curve) == len(frame):
                out["exposure"] = exposure_metrics(
                    sim_result.trade_blotter, frame["close"].to_numpy(float), curve, start
                )
            out["engine"] = {
                k: row.get(k)
                for k in ("CAGR %", "Max Drawdown %", "Trade Count", "Signal Exit Count")
            }
            out["equity"] = {str(k.date()): round(float(v), 2) for k, v in scored.items()}

        def close_sweep(self):
            pass

    OptimizationController(historical_data=frame).run_sweep(**kwargs, result_sink=Sink())
    out["elapsed_s"] = round(time.time() - started, 1)
    return out


# --------------------------------------------------------------- choosing


def _ok(row: dict) -> bool:
    return bool(row.get("metrics")) and not row.get("error")


def choose(rows: list[dict], key: str = "metrics", rule: str = "budget") -> dict | None:
    """THE CHOICE (module docstring). rule "budget": the highest daily return
    within DD_BUDGET; "steadiest": the first rule tried, kept for the report."""
    rows = [r for r in rows if r.get(key)]
    if not rows:
        return None
    if rule == "steadiest":
        hit = [r for r in rows if r[key]["geo_daily"] >= GOAL * 100]
        if hit:
            return min(hit, key=lambda r: (r[key]["max_dd"], -r[key]["pct_goal_days"]))
        return max(rows, key=lambda r: r[key]["geo_daily"])
    within = [r for r in rows if r[key]["max_dd"] <= DD_BUDGET]
    if not within:
        return min(rows, key=lambda r: r[key]["max_dd"])
    return max(within, key=lambda r: (r[key]["geo_daily"], r[key]["pct_goal_days"]))


def window_metrics(row: dict, start: str | None, end: str | None) -> dict:
    import pandas as pd

    equity = pd.Series(row["equity"])
    equity.index = pd.to_datetime(equity.index)
    if start:
        equity = equity[equity.index >= pd.Timestamp(start)]
    if end:
        equity = equity[equity.index < pd.Timestamp(end)]
    return daily_metrics(equity)


def load_results(out_dir: Path) -> list[dict]:
    path = out_dir / "results.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def chosen_base(out_dir: Path, fund: str) -> dict:
    grid = [
        r for r in load_results(out_dir) if r["stage"] == "grid" and r["fund"] == fund and _ok(r)
    ]
    best = choose(grid)
    if best is None:
        raise SystemExit(f"no grid results for {fund} in {out_dir}: run --stage grid first")
    return best


# --------------------------------------------------------------- the report


def buy_and_hold(out_dir: Path, funds) -> dict[str, dict]:
    """Each fund held over the scored window, whole and split, cached."""
    import pandas as pd

    cache = out_dir / "buy_and_hold.json"
    known = json.loads(cache.read_text()) if cache.exists() else {}
    for fund in funds:
        if fund in known:
            continue
        closes = _regular_closes(fund)
        scored = closes[closes.index >= pd.Timestamp(score_start(closes.index))]
        split = pd.Timestamp(SPLIT)
        known[fund] = {
            "all": daily_metrics(scored),
            "in": daily_metrics(scored[scored.index < split]),
            "out": daily_metrics(scored[scored.index >= split]),
        }
    cache.write_text(json.dumps(known, indent=1))
    return known


def _fmt(row: dict, bh: dict | None = None) -> str:
    m, t = row["metrics"], row.get("trading", {})
    beat = ""
    if bh:
        beat = " beats" if m["cagr"] > bh["cagr"] else " trails"
    return (
        f"{m['geo_daily']:6.3f}%/d  CAGR {m['cagr']:6.1f}%{beat}  DD {m['max_dd']:5.1f}%  "
        f"Sharpe {m['sharpe']:4.2f}  goal-days {m['pct_goal_days']:4.1f}%  "
        f"up {m['pct_up_days']:4.1f}% flat {m['pct_flat_days']:4.1f}%  "
        f"worst day {m['worst_day']:6.1f}%  2022 {m['years'].get('2022', float('nan')):6.1f}%  "
        f"sells/d {t.get('sells_per_day', 0):5.1f}  hold {t.get('hold_sessions_median', float('nan')):4.0f}"
    )


def report(out_dir: Path) -> str:
    rows = [r for r in load_results(out_dir) if _ok(r)]
    failed = [r for r in load_results(out_dir) if r.get("error")]
    funds = sorted({r["fund"] for r in rows})
    bh = buy_and_hold(out_dir, funds)
    lines = [f"# daily-ultimate sweep: {len(rows)} runs ({len(failed)} failed)", ""]
    lines.append(f"Goal: {GOAL:.1%} of equity a session ({(1 + GOAL) ** 252 - 1:.1%} a year).")
    for fund in funds:
        b = bh[fund]["all"]
        lines.append(
            f"- {fund} buy-and-hold {b['start']}..{b['end']}: {b['geo_daily']:.3f}%/d, "
            f"CAGR {b['cagr']:.1f}%, DD {b['max_dd']:.1f}%, Sharpe {b['sharpe']:.2f}, "
            f"goal-days {b['pct_goal_days']:.1f}%, worst day {b['worst_day']:.1f}%"
        )
    for stage in ("funds", "grid", "pairs", "robust"):
        stage_rows = [r for r in rows if r["stage"] == stage]
        if not stage_rows:
            continue
        lines += ["", f"## {stage}", ""]
        if stage == "funds":
            for fund in funds:
                fund_rows = [r for r in stage_rows if r["fund"] == fund]
                best = choose(fund_rows)
                if best:
                    lines.append(f"- {fund:8s} {best['name']}: {_fmt(best, bh[fund]['all'])}")
            continue
        for fund in sorted({r["fund"] for r in stage_rows}):
            fund_rows = sorted(
                (r for r in stage_rows if r["fund"] == fund),
                key=lambda r: -r["metrics"]["geo_daily"],
            )
            best = choose(fund_rows)
            for r in fund_rows:
                mark = "**" if r is best else "  "
                lines.append(f"{mark}{r['name']:58s} {_fmt(r, bh[fund]['all'])}")
            if stage == "grid" and best is not None:
                lines += ["", f"Chosen: {best['name']}", ""]
                for r in fund_rows:
                    r["in"] = window_metrics(r, None, SPLIT)
                    r["out"] = window_metrics(r, SPLIT, None)
                ranked = sorted(fund_rows, key=lambda r: -r["out"]["geo_daily"])
                lines.append("Walk-forward (choose on 2017-2021, score 2022 on):")
                for rule in ("budget", "steadiest"):
                    picked = choose(fund_rows, key="in", rule=rule)
                    i, o = picked["in"], picked["out"]
                    lines += [
                        f"  {rule}: picked {picked['name']}",
                        f"    2017-2021 {i['geo_daily']:.3f}%/d CAGR {i['cagr']:.1f}% DD {i['max_dd']:.1f}%"
                        f" (buy-and-hold {bh[fund]['in']['cagr']:.1f}%)",
                        f"    2022 on   {o['geo_daily']:.3f}%/d CAGR {o['cagr']:.1f}% DD {o['max_dd']:.1f}%"
                        f" (buy-and-hold {bh[fund]['out']['cagr']:.1f}%), "
                        f"rank {ranked.index(picked) + 1} of {len(ranked)} out of sample",
                    ]
                both = [
                    r
                    for r in fund_rows
                    if min(r["in"]["geo_daily"], r["out"]["geo_daily"]) >= GOAL * 100
                ]
                lines.append(
                    f"  configurations at the goal in BOTH halves: {len(both)} of {len(fund_rows)}"
                )
    text = "\n".join(lines) + "\n"
    (out_dir / "report.md").write_text(text)
    return text


# --------------------------------------------------------------- main


def fund_scales(out_dir: Path) -> dict[str, float]:
    """Each fund's daily volatility over TQQQ's (regular-session closes)."""
    import numpy as np

    cache = out_dir / "scales.json"
    if cache.exists():
        return json.loads(cache.read_text())
    vols = {}
    for fund in FUNDS:
        closes = _regular_closes(fund)
        vols[fund] = float(np.log(closes).diff().dropna().std())
    scales = {fund: round(vol / vols["TQQQ"], 3) for fund, vol in vols.items()}
    cache.write_text(json.dumps(scales, indent=1))
    return scales


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--stage", choices=("funds", "grid", "pairs", "robust"))
    parser.add_argument("--fund", default="TQQQ")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path, help="print and write DIR/report.md")
    parser.add_argument("--jobs", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.report:
        print(report(args.report))
        return 0
    if not args.stage or not args.out:
        parser.error("--stage and --out are required (or --report DIR)")
    args.out.mkdir(parents=True, exist_ok=True)
    if args.stage == "funds":
        specs = plan_funds(fund_scales(args.out))
    elif args.stage == "grid":
        specs = plan_grid(args.fund, fund_scales(args.out)[args.fund])
    elif args.stage == "pairs":
        specs = plan_pairs(args.fund, chosen_base(args.out, args.fund))
    else:
        specs = plan_robust(args.fund, chosen_base(args.out, args.fund))
    done = {r["name"] for r in load_results(args.out)}
    todo = [s for s in specs if s["name"] not in done]
    print(f"{args.stage}: {len(specs)} runs, {len(specs) - len(todo)} done, {len(todo)} to run")
    if args.dry_run or not todo:
        return 0
    with (
        ProcessPoolExecutor(max_workers=args.jobs) as pool,
        (args.out / "results.jsonl").open("a") as sink,
    ):
        futures = {pool.submit(run_one, spec): spec for spec in todo}
        for n, future in enumerate(as_completed(futures), 1):
            spec = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # one failed configuration never stops the stage
                result = {k: spec[k] for k in ("stage", "name", "fund", "meta")}
                result["error"] = repr(exc)[:2000]
            sink.write(json.dumps(result, default=str) + "\n")
            sink.flush()
            m = result.get("metrics") or {}
            status = result.get("error", "")[:120] or (
                f"{m.get('geo_daily', float('nan')):.3f}%/d CAGR {m.get('cagr', float('nan')):.1f}% "
                f"DD {m.get('max_dd', float('nan')):.1f}%"
            )
            print(f"[{n}/{len(todo)}] {spec['name']}: {status}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
