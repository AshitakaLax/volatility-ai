#!/usr/bin/env python
"""
The Forecast Harvest sweep (docs/research/forecast-harvest.md): a TQQQ book
in whole shares that takes most of its profit day by day, its reward set by
the nightly risk report, and how to start it $250,000 into a fall of 43%.

    python tools/probe_forecast_harvest.py --stage design   --out DIR [--jobs N]
    python tools/probe_forecast_harvest.py --stage forecast --out DIR --proxy PROXY
    python tools/probe_forecast_harvest.py --stage entry    --out DIR --proxy PROXY
    python tools/probe_forecast_harvest.py --report DIR

PROXY is tools/build_proxy_reports.py's archive for TQQQ (one JSON a session).
Every run is measured as tools/probe_daily_ultimate.py measures (its run_one):
intrabar fills booked causally, dynamic slippage, no cash yield, bars from
2016-01-04, scored from 2017-01-03. A run in DIR/results.jsonl is skipped.

--------------------------------------------------------------------
THE STAGES

  design    no report: the day part's level comes from the fund's own
            volatility. day_fraction x day_k x the swing target x lot size,
            plus Daily Ultimate itself (fractional and whole shares) and the
            fund held. Chooses the design (THE CHOICE).
  forecast  the chosen design read from reports of differing quality:
              none        the fund's own volatility (the design stage's)
              proxy       the causal proxy reports (VXN and realised
                          volatility; research/risk_overlay/proxy.py)
              rho R       synthetic reports at accuracy R, 6 seeds each
            each with the report setting the day level only, and also the
            lot size (forecast_size_exponent, forecast_tilt).
  entry     the start: $250,000 from the first session TQQQ closed 43%
            below its high (2018-12-17, 2020-03-09, 2022-02-18, 2025-04-03,
            and the same crossing on tools/stress_paths.py's deeper bears),
            with no opening seed, or seed ladders of differing size, depth
            and target.

--------------------------------------------------------------------
SYNTHETIC REPORTS (lookahead by design)

A ruler for what accuracy is worth, never evidence a source has it. For a
session t with the proxy's one-day sigma s_t (its 5-95 spread / 3.29) and
the session's real close-to-close return r_t, z_t = r_t / s_t. A report at
accuracy rho draws e_t ~ N(0, 1) from its seed and forms the signal
x_t = rho z_t + sqrt(1 - rho^2) e_t, so corr(x, z) = rho. The report then
states the forecast a forecaster believing its signal has skill |rho| would:

    quantile q = s_t (|rho| x_t + sqrt(1 - rho^2) Phi^-1(q))

so for rho >= 0 the report is calibrated (rho = 0 is the proxy's sigma and
nothing more; rho = 1 knows the close), and for rho < 0 it is as confident
as |rho| and wrong: it leans up before the down days.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import probe_daily_ultimate as pdu

TZ = "America/New_York"
FUND = "TQQQ"
CAPITAL = 250_000.0
DD_BUDGET = 30.0
DAILY_SHARE = 50.0  # THE CHOICE: at least half the invested sessions bank a profit
SPLIT = "2022-01-01"
FALL = 0.43
CROSSINGS = ("2018-12-17", "2020-03-09", "2022-02-18", "2025-04-03")
RHOS = (-0.3, 0.0, 0.1, 0.2, 0.3, 0.5, 1.0)
SEEDS = 6
NORMAL_Z = {"p05": -1.6449, "p25": -0.6745, "p50": 0.0, "p75": 0.6745, "p95": 1.6449}

# Daily Ultimate's pinned buy (config/daily_ultimate_tqqq.yaml).
STEP, TARGET, LOT = 0.002, 0.12, 0.008


def base_params(lot: float = LOT, target: float = TARGET) -> tuple[dict, float, float]:
    params, step, target = pdu.daily_ultimate(FUND, 1.0, target, lot, "hold", compound=False)
    return params, step, target


def config(strategy_id: str, params: dict, step: float, target: float) -> dict:
    cfg = pdu._config(FUND, strategy_id, params, step, target)
    cfg["backtest"]["initial_cash"] = CAPITAL
    return cfg


def spec(
    stage: str, name: str, strategy_id: str, params: dict, step: float, target: float, **meta
) -> dict:
    out = pdu._spec(stage, name, FUND, config(strategy_id, params, step, target), **meta)
    for key in ("start", "end", "stress"):
        if key in meta:
            out[key] = meta[key]
    return out


# --------------------------------------------------------------- the plan


def plan_design() -> list[dict]:
    specs = []
    for lot in (0.008, 0.016):
        for target in (0.08, 0.12, 0.2):
            params, step, tgt = base_params(lot, target)
            specs.append(
                spec(
                    "design",
                    pdu._name("daily_ultimate frac", lot, target),
                    "daily_ultimate",
                    params,
                    step,
                    tgt,
                    lot=lot,
                    swing=target,
                    whole=False,
                    frac=0.0,
                )
            )
            for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
                for k in (0.5, 1.0, 1.5) if frac else (1.0,):
                    p = {**params, "whole_shares": True, "day_fraction": frac, "day_k": k}
                    specs.append(
                        spec(
                            "design",
                            pdu._name("fh lot", lot, "swing", target, "frac", frac, "k", k),
                            "forecast_harvest",
                            p,
                            step,
                            tgt,
                            lot=lot,
                            swing=target,
                            whole=True,
                            frac=frac,
                            k=k,
                        )
                    )
    return specs


def plan_design2() -> list[dict]:
    """The day part's reach and its closing sale, at design's best lot and
    swing target: lower levels and a closing sale bank more sessions."""
    specs = []
    params, step, tgt = base_params(0.008, 0.2)
    for frac in (0.5, 0.75, 1.0):
        for k in (0.25, 0.5, 1.0):
            for low in (0.002, 0.004):
                for close in (None, 375):
                    p = {
                        **params,
                        "whole_shares": True,
                        "day_fraction": frac,
                        "day_k": k,
                        "day_target_min": low,
                        "day_close_minute": close,
                    }
                    name = pdu._name("fh2 frac", frac, "k", k, "min", low, "close", close)
                    specs.append(
                        spec(
                            "design",
                            name,
                            "forecast_harvest",
                            p,
                            step,
                            tgt,
                            lot=0.008,
                            swing=0.2,
                            whole=True,
                            frac=frac,
                            k=k,
                            low=low,
                            close=close,
                        )
                    )
    return specs


def _design_choice(out_dir: Path) -> dict:
    rows = [
        r
        for r in pdu.load_results(out_dir)
        if r["stage"] == "design" and r["meta"].get("whole") and pdu._ok(r)
    ]
    chosen = choose(rows)
    if chosen is None:
        raise SystemExit("run --stage design first")
    return chosen


def forecast_variants() -> list[tuple[str, dict]]:
    """(label, forecast-driven params) for each use of the report."""
    return [
        ("level", {}),
        ("level k1", {"day_k": 1.0}),
        ("level+size", {"forecast_size_exponent": 1.0}),
        ("level+tilt", {"forecast_tilt": 0.5}),
        ("level k1+tilt", {"day_k": 1.0, "forecast_tilt": 0.5}),
    ]


def plan_forecast(out_dir: Path) -> list[dict]:
    base = _design_choice(out_dir)
    params, step, target = base["params"], base["step"], base["target"]
    specs = [
        spec(
            "forecast", "none", "forecast_harvest", params, step, target, source="none", use="level"
        ),
        spec(
            "forecast",
            "none k1",
            "forecast_harvest",
            {**params, "day_k": 1.0},
            step,
            target,
            source="none",
            use="level k1",
        ),
    ]
    for label, extra in forecast_variants():
        p = {**params, **extra}
        specs.append(
            spec(
                "forecast",
                pdu._name("proxy", label),
                "forecast_harvest",
                p,
                step,
                target,
                source="proxy",
                use=label,
            )
        )
        for rho in RHOS:
            for seed in range(SEEDS if rho < 1 else 1):
                specs.append(
                    spec(
                        "forecast",
                        pdu._name("rho", rho, label, "seed", seed),
                        "forecast_harvest",
                        p,
                        step,
                        target,
                        source="synthetic",
                        rho=rho,
                        seed=seed,
                        use=label,
                    )
                )
    return specs


SEED_PLANS: dict[str, dict] = {
    "no seed": {},
    "seed 20% at 0": {"seed_levels": "0", "seed_lot_pct": 0.2},
    "seed 40% at 0": {"seed_levels": "0", "seed_lot_pct": 0.4},
    "ladder 3x10% 0/15/30": {"seed_levels": "0,0.15,0.3", "seed_lot_pct": 0.1},
    "ladder 3x20% 0/15/30": {"seed_levels": "0,0.15,0.3", "seed_lot_pct": 0.2},
    "ladder 4x10% 0/10/20/30": {"seed_levels": "0,0.1,0.2,0.3", "seed_lot_pct": 0.1},
    "ladder 3x15% 0/20/40": {"seed_levels": "0,0.2,0.4", "seed_lot_pct": 0.15},
    "deep 3x15% 10/25/40": {"seed_levels": "0.1,0.25,0.4", "seed_lot_pct": 0.15},
}
SEED_TARGETS = (0.5, 1.0)


def stressed_crossings() -> dict[str, str]:
    """The first session each deeper bear closes FALL below its high."""
    import pandas as pd

    from engine.warehouse.bars import load_frame
    from tools import stress_paths

    out = {}
    raw = load_frame(FUND)
    raw = raw[raw.index >= pd.Timestamp(pdu.START, tz="UTC")]
    for scenario in ("deeper", "grind", "fast"):
        bars = stress_paths.stressed(raw, scenario)
        ny = bars.index.tz_convert(TZ)
        minutes = ny.hour * 60 + ny.minute
        bars = bars[(minutes >= 570) & (minutes < 960)]
        idx = bars.index.tz_convert(TZ).tz_localize(None)
        closes = pd.Series(bars["close"].to_numpy(float), index=idx).groupby(idx.normalize()).last()
        start = "2020-01-01" if scenario == "fast" else "2021-06-01"
        c = closes[closes.index >= pd.Timestamp(start)]
        dd = c / closes.cummax().reindex(c.index) - 1
        out[scenario] = str(dd[dd <= -FALL].index[0].date())
    return out


def plan_entry(out_dir: Path) -> list[dict]:
    base = _design_choice(out_dir)
    params, step, target = base["params"], base["step"], base["target"]
    starts = [(day, None) for day in CROSSINGS]
    starts += [(day, scenario) for scenario, day in stressed_crossings().items()]
    specs = []
    for day, scenario in starts:
        for plan, seed in SEED_PLANS.items():
            for seed_target in SEED_TARGETS if seed else (None,):
                p = {**params, "trade_from": day, **seed}
                if seed_target is not None:
                    p["seed_target"] = seed_target
                meta = {
                    "entry": day,
                    "plan": plan,
                    "seed_target": seed_target,
                    "scenario": scenario or "real",
                }
                if scenario:
                    meta["stress"] = scenario
                name = pdu._name(
                    "entry", scenario or "real", day, plan, f"t{seed_target}" if seed_target else ""
                )
                specs.append(spec("entry", name, "forecast_harvest", p, step, target, **meta))
    return specs


REVERSALS = ((0.05, 2), (0.05, 4), (0.1, 2), (0.1, 4), (0.2, 2))


def plan_entry2(out_dir: Path) -> list[dict]:
    """The entry stage's finding: the book's own reversal lots, not a seed,
    are its opening and its tail. Their size and count, from every crossing
    with no seed, and over the whole history."""
    base = _design_choice(out_dir)
    params, step, target = base["params"], base["step"], base["target"]
    starts = [(day, None) for day in CROSSINGS]
    starts += [(day, scenario) for scenario, day in stressed_crossings().items()]
    specs = []
    for pct, most in REVERSALS:
        p = {**params, "reversal_lot_pct": pct, "reversal_max_lots": most}
        label = f"rev {pct:g} x{most}"
        specs.append(
            spec(
                "design",
                pdu._name("fh3", label),
                "forecast_harvest",
                p,
                step,
                target,
                whole=True,
                frac=params.get("day_fraction"),
                reversal=label,
            )
        )
        for day, scenario in starts:
            meta = {
                "entry": day,
                "plan": f"no seed, {label}",
                "seed_target": None,
                "scenario": scenario or "real",
            }
            if scenario:
                meta["stress"] = scenario
            specs.append(
                spec(
                    "entry",
                    pdu._name("entry", scenario or "real", day, "no seed", label),
                    "forecast_harvest",
                    {**p, "trade_from": day},
                    step,
                    target,
                    **meta,
                )
            )
    return specs


# The aggressive profile: the pinned book reading the report boldly, its day
# parts reaching for more of the profit.
AGGRESSIVE_SHARE = (22.0, 30.0)  # the day parts' share of target-sale profit, in percent
PINNED = _REPO_ROOT / "config" / "forecast_harvest_tqqq.yaml"


def pinned() -> tuple[dict, float, float]:
    """(strategy_params, step, target) of config/forecast_harvest_tqqq.yaml."""
    from engine.core.config import BacktestConfig

    config = BacktestConfig.from_yaml(PINNED)
    return (
        dict(config.strategy.strategy_params),
        config.grid.steps[0],
        config.grid.profit_targets[0],
    )


def plan_aggressive() -> list[dict]:
    """The day level at 1-2x the report's p75, a higher cap and floor on the
    day target, with and without the closing sale, the report's tilt on --
    all read from the causal proxy reports."""
    params, step, target = pinned()
    specs = []
    for k in (1.0, 1.5, 2.0):
        for top in (0.04, 0.08):
            for low in (0.002, 0.005):
                for close in (375, None):
                    p = {
                        **params,
                        "day_k": k,
                        "day_target_max": top,
                        "day_target_min": low,
                        "day_close_minute": close,
                        "forecast_tilt": 0.5,
                    }
                    name = pdu._name("agg k", k, "max", top, "min", low, "close", close)
                    specs.append(
                        spec(
                            "aggressive",
                            name,
                            "forecast_harvest",
                            p,
                            step,
                            target,
                            source="proxy",
                            use="aggressive",
                            k=k,
                            top=top,
                            low=low,
                            close=close,
                        )
                    )
    # Between the grid's two cells either side of a 25% share (k 2, closing
    # sale: a floor of 0.2% gives 22%, 0.5% gives 27%).
    for k, top, low in (
        (2.0, 0.04, 0.003),
        (2.0, 0.04, 0.0035),
        (2.0, 0.04, 0.004),
        (2.0, 0.08, 0.0035),
        (2.5, 0.08, 0.003),
    ):
        p = {
            **params,
            "day_k": k,
            "day_target_max": top,
            "day_target_min": low,
            "day_close_minute": 375,
            "forecast_tilt": 0.5,
        }
        name = pdu._name("agg k", k, "max", top, "min", low, "close", 375)
        specs.append(
            spec(
                "aggressive",
                name,
                "forecast_harvest",
                p,
                step,
                target,
                source="proxy",
                use="aggressive",
                k=k,
                top=top,
                low=low,
                close=375,
            )
        )
    return specs


def choose_aggressive(rows: list[dict]) -> dict | None:
    """The highest daily return within DD_BUDGET whose day parts make
    AGGRESSIVE_SHARE of the target profit, preferring those that still bank
    a profit on DAILY_SHARE of invested sessions; the share nearest 25%
    if none is in range."""
    ok = [r for r in rows if r.get("metrics") and r.get("daily") and r["stage"] == "aggressive"]
    lo, hi = AGGRESSIVE_SHARE

    def share(r):
        return r["daily"].get("day_part_share", 0.0)

    inside = [r for r in ok if lo <= share(r) <= hi and r["metrics"]["max_dd"] <= DD_BUDGET]
    banking = [r for r in inside if r["daily"]["pct_invested_sessions_profit"] >= DAILY_SHARE]
    for pool in (banking, inside):
        if pool:
            return max(pool, key=lambda r: r["metrics"]["geo_daily"])
    return min(ok, key=lambda r: abs(share(r) - 25.0), default=None)


def plan_aggressive2(out_dir: Path) -> list[dict]:
    """The chosen aggressive book against reports of every quality, and
    started from every -43% crossing."""
    chosen = choose_aggressive(pdu.load_results(out_dir))
    if chosen is None:
        raise SystemExit("run --stage aggressive first")
    params, step, target = chosen["params"], chosen["step"], chosen["target"]
    specs = [
        spec(
            "aggressive2",
            "agg none",
            "forecast_harvest",
            params,
            step,
            target,
            source="none",
            use="aggressive",
        )
    ]
    for rho in (-0.3, 0.0, 0.2, 0.5, 1.0):
        for seed in range(3 if rho < 1 else 1):
            specs.append(
                spec(
                    "aggressive2",
                    pdu._name("agg rho", rho, "seed", seed),
                    "forecast_harvest",
                    params,
                    step,
                    target,
                    source="synthetic",
                    rho=rho,
                    seed=seed,
                    use="aggressive",
                )
            )
    starts = [(day, None) for day in CROSSINGS]
    starts += [(day, scenario) for scenario, day in stressed_crossings().items()]
    for day, scenario in starts:
        meta = {
            "entry": day,
            "plan": "aggressive, no seed",
            "seed_target": None,
            "scenario": scenario or "real",
            # a real crossing reads the proxy's reports; a stressed path has none
            "source": "none" if scenario else "proxy",
        }
        if scenario:
            meta["stress"] = scenario
        specs.append(
            spec(
                "entry",
                pdu._name("entry", scenario or "real", day, "aggressive"),
                "forecast_harvest",
                {**params, "trade_from": day},
                step,
                target,
                **meta,
            )
        )
    return specs


# --------------------------------------------------------------- reports


_PROXY: dict[date, dict] = {}


def proxy_quantiles(proxy_dir: str) -> dict[date, dict]:
    if not _PROXY:
        for path in sorted(Path(proxy_dir).glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            if "report" not in doc:  # the archive's meta.json
                continue
            q = doc["report"]["horizons"]["tomorrow"]["summary"]["quantiles_pct"]
            median = doc["report"]["horizons"]["tomorrow"]["summary"].get("median_pct", 0.0)
            _PROXY[date.fromisoformat(doc["session"])] = {
                "p05": q["p05"],
                "p25": q["p25"],
                "p50": median,
                "p75": q["p75"],
                "p95": q["p95"],
            }
    return _PROXY


def synthetic(proxy: dict[date, dict], closes, rho: float, seed: int) -> dict[date, dict]:
    """Reports at accuracy rho (module docstring)."""
    import numpy as np

    rows = []
    prev = None
    for day, close in closes.items():
        session = day.date()
        if prev is not None and session in proxy:
            sigma = (proxy[session]["p95"] - proxy[session]["p05"]) / 100 / (2 * NORMAL_Z["p95"])
            if sigma > 0:
                rows.append((session, sigma, close / prev - 1.0))
        prev = close
    rng = np.random.default_rng([seed, round((rho + 2) * 1000)])
    eps = rng.standard_normal(len(rows))
    b = abs(rho)
    rest = math.sqrt(max(0.0, 1 - rho * rho))
    out = {}
    for (session, sigma, r), e in zip(rows, eps, strict=True):
        x = rho * (r / sigma) + rest * e
        # A perfect report still states a sliver of spread (5% of sigma), so
        # the sizing levers, which divide by its sigma, can read it.
        centre, spread = sigma * b * x, sigma * max(rest, 0.05)
        out[session] = {k: round((centre + spread * z) * 100, 4) for k, z in NORMAL_Z.items()}
    return out


def _forecast_map(spec_: dict, proxy_dir: str | None):
    meta = spec_["meta"]
    source = meta.get("source", "none")
    if source == "none":
        return None
    proxy = proxy_quantiles(proxy_dir)
    if source == "proxy":
        return proxy
    return synthetic(proxy, pdu._regular_closes(FUND), meta["rho"], meta["seed"])


# --------------------------------------------------------------- measuring


def extra_metrics(sim, row, frame, out) -> None:
    """What the design asks of a run beyond probe_daily_ultimate's: how many
    of its invested sessions bank a profit, how much of the profit is the
    day parts', and that every share is whole."""
    import numpy as np
    import pandas as pd

    b = sim.trade_blotter
    curve = sim.equity_curve
    if b is None or b.empty or len(curve) != len(frame):
        out["daily"] = {}
        return
    held = np.zeros(len(frame))
    sign = np.where(b["side"].to_numpy() == "buy", 1.0, -1.0)
    np.add.at(held, b["bar_index"].to_numpy(int), sign * b["qty"].to_numpy(float))
    held = np.cumsum(held)
    day = pd.DatetimeIndex(frame.index).tz_convert(TZ).tz_localize(None).normalize()
    opening = pd.Series(held, index=day).groupby(level=0).first()
    scored_from = pd.Timestamp(out["metrics"]["start"]) if out.get("metrics") else day[0]
    sessions = opening.index[opening.index >= scored_from]
    sells = b[b["side"] == "sell"].copy()
    sells["day"] = (
        pd.to_datetime(sells["timestamp"], utc=True)
        .dt.tz_convert(TZ)
        .dt.tz_localize(None)
        .dt.normalize()
    )
    pnl = sells["profit_realized"].fillna(0.0).astype(float)
    basis = sells["qty"].astype(float) * sells["price"].astype(float) - pnl
    ret = pnl / basis.where(basis > 0)
    realized = pnl.groupby(sells["day"]).sum().reindex(sessions, fill_value=0.0)
    invested = opening.reindex(sessions) > 1e-9
    is_target = sells["sell_reason"].astype(str) == "profit_target"
    small = is_target & (ret <= 0.0405)
    target_pnl = pnl[is_target].sum()
    # A day part's sale, read from the blotter itself: a lot's FIRST sale, at
    # its target, of fewer shares than it bought (the swing part stays open).
    bought = b[b["side"] == "buy"].groupby("lot_id")["qty"].sum().astype(float)
    first = ~sells.duplicated("lot_id", keep="first")
    partial = sells["qty"].astype(float) < sells["lot_id"].map(bought).fillna(0.0) - 1e-6
    day_sale = is_target & first & partial
    q = b["qty"].astype(float)
    out["daily"] = {
        "pct_sessions_profit": float((realized > 0).mean() * 100),
        "pct_invested_sessions": float(invested.mean() * 100),
        "pct_invested_sessions_profit": float((realized[invested] > 0).mean() * 100)
        if invested.any()
        else 0.0,
        "day_part_share_of_target_pnl": float(pnl[small].sum() / target_pnl * 100)
        if target_pnl > 0
        else 0.0,
        "day_part_share": float(pnl[day_sale].sum() / target_pnl * 100) if target_pnl > 0 else 0.0,
        "day_part_share_of_all_pnl": float(pnl[day_sale].sum() / pnl.sum() * 100)
        if pnl.sum() > 0
        else 0.0,
        "signal_exit_pnl": float(
            pnl[sells["sell_reason"].astype(str).str.contains("signal")].sum()
        ),
        "max_fractional_share": float((q - q.round()).abs().max()),
        "sales": len(sells),
    }
    entry = spec_entry_day(out)
    if entry is not None:
        out["entry_metrics"] = entry_metrics(out["equity_full"], entry)


def spec_entry_day(out) -> str | None:
    return (out.get("meta") or {}).get("entry")


def entry_metrics(equity: dict, entry: str) -> dict:
    """From the entry session: equity after 1 and 2 years and at the end,
    the lowest point and the drawdown, as multiples of CAPITAL."""
    import pandas as pd

    e = pd.Series(equity)
    e.index = pd.to_datetime(e.index)
    e = e[e.index >= pd.Timestamp(entry)]
    if e.empty:
        return {}
    peak = e.cummax()
    out = {
        "sessions": len(e),
        "low": float(e.min() / CAPITAL),
        "max_dd": float(((peak - e) / peak).max() * 100),
        "end": float(e.iloc[-1] / CAPITAL),
        "end_date": str(e.index[-1].date()),
    }
    for label, n in (("y1", 252), ("y2", 504)):
        out[label] = float(e.iloc[min(n, len(e) - 1)] / CAPITAL)
    return out


def run_spec(spec_: dict, proxy_dir: str | None) -> dict:
    forecasts = _forecast_map(spec_, proxy_dir)

    def prepare(kwargs, frame):
        if forecasts is not None:
            for p in kwargs["strategy_params_grid"]:
                p["forecast_by_date"] = forecasts

    def on_result(sim, row, frame, out):
        import pandas as pd

        curve = sim.equity_curve
        idx = pd.DatetimeIndex(curve.index).tz_convert(TZ).tz_localize(None)
        daily = pd.Series(curve.to_numpy(float), index=idx).groupby(idx.normalize()).last()
        out["equity_full"] = {str(k.date()): round(float(v), 2) for k, v in daily.items()}
        extra_metrics(sim, row, frame, out)
        if spec_["stage"] != "entry":
            out.pop("equity_full", None)

    return pdu.run_one(spec_, prepare=prepare, on_result=on_result)


def run_stage(specs: list[dict], out_dir: Path, jobs: int, proxy_dir: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.jsonl"
    done = {r["name"] for r in pdu.load_results(out_dir)}
    todo = [s for s in specs if s["name"] not in done]
    print(
        f"{len(specs)} runs, {len(specs) - len(todo)} already done, {len(todo)} to run", flush=True
    )
    started = time.time()
    with ProcessPoolExecutor(max_workers=jobs) as pool, path.open("a", encoding="utf-8") as fh:
        futures = {pool.submit(run_spec, s, proxy_dir): s for s in todo}
        for n, future in enumerate(as_completed(futures), 1):
            s = futures[future]
            try:
                row = future.result()
            except Exception as exc:  # one failed run never ends the stage
                row = {k: s[k] for k in ("stage", "name", "fund", "meta")}
                row["error"] = repr(exc)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            m = row.get("metrics") or {}
            print(
                f"[{n}/{len(todo)} {time.time() - started:.0f}s] {s['name']}: "
                f"{m.get('geo_daily', float('nan')):.3f}%/session DD {m.get('max_dd', float('nan')):.1f}%",
                flush=True,
            )


# --------------------------------------------------------------- choosing


def choose(rows: list[dict]) -> dict | None:
    """THE CHOICE: the highest geometric daily return among runs within
    DD_BUDGET whose invested sessions bank a profit at least DAILY_SHARE% of
    the time; the highest daily share if none does."""
    ok = [r for r in rows if r.get("metrics") and r.get("daily")]
    fit = [
        r
        for r in ok
        if r["metrics"]["max_dd"] <= DD_BUDGET
        and r["daily"]["pct_invested_sessions_profit"] >= DAILY_SHARE
    ]
    if fit:
        return max(fit, key=lambda r: r["metrics"]["geo_daily"])
    return max(ok, key=lambda r: r["daily"]["pct_invested_sessions_profit"], default=None)


# --------------------------------------------------------------- report


def _row(r: dict) -> str:
    m, d = r.get("metrics") or {}, r.get("daily") or {}
    early = pdu.window_metrics(r, None, SPLIT)
    late = pdu.window_metrics(r, SPLIT, None)
    return (
        f"| {r['name']} | {m.get('geo_daily', 0):.3f}% | {m.get('cagr', 0):.1f}% | "
        f"{m.get('max_dd', 0):.1f}% | {m.get('calmar', 0):.2f} | {early.get('geo_daily', 0):.3f}% | "
        f"{late.get('geo_daily', 0):.3f}% | {d.get('pct_invested_sessions_profit', 0):.0f}% | "
        f"{d.get('pct_sessions_profit', 0):.0f}% | "
        f"{d.get('day_part_share', d.get('day_part_share_of_target_pnl', 0)):.0f}% |"
    )


HEAD = (
    "| run | /session | CAGR | max DD | Calmar | 2017-21 | 2022 on | invested sessions "
    "banking a profit | all sessions | day parts' share of target profit |\n"
    "|---|---|---|---|---|---|---|---|---|---|"
)


def buy_and_hold() -> dict:
    closes = pdu._regular_closes(FUND)
    scored = closes[closes.index >= __import__("pandas").Timestamp(pdu.SCORE_FROM)]
    return {
        "all": pdu.daily_metrics(scored),
        "early": pdu.daily_metrics(scored[scored.index < __import__("pandas").Timestamp(SPLIT)]),
        "late": pdu.daily_metrics(scored[scored.index >= __import__("pandas").Timestamp(SPLIT)]),
    }


def report(out_dir: Path) -> str:
    import statistics

    rows = [r for r in pdu.load_results(out_dir) if pdu._ok(r)]
    lines = ["# Forecast Harvest sweep", ""]
    bh = buy_and_hold()
    lines.append(
        f"TQQQ held: {bh['all']['geo_daily']:.3f}%/session, CAGR {bh['all']['cagr']:.1f}%, "
        f"max DD {bh['all']['max_dd']:.1f}%; 2017-21 {bh['early']['geo_daily']:.3f}%, "
        f"2022 on {bh['late']['geo_daily']:.3f}%"
    )
    design = [r for r in rows if r["stage"] == "design"]
    if design:
        chosen = choose([r for r in design if r["meta"].get("whole")])
        lines += [
            "",
            "## design",
            "",
            f"THE CHOICE: **{chosen['name'] if chosen else None}**",
            "",
            HEAD,
        ]
        lines += [_row(r) for r in sorted(design, key=lambda r: -r["metrics"]["geo_daily"])]
    forecast = [r for r in rows if r["stage"] == "forecast"]
    if forecast:
        lines += [
            "",
            "## forecast",
            "",
            "Synthetic rows: the median over seeds, then the worst and best seed.",
            "",
            "| source | use | /session median | worst seed | best seed | max DD median | "
            "worst DD | invested sessions banking a profit | 2022 on median |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        groups: dict[tuple, list] = {}
        for r in forecast:
            m = r["meta"]
            key = (m.get("source"), m.get("rho"), m.get("use", "-"))
            groups.setdefault(key, []).append(r)
        for (source, rho, use), rs in sorted(
            groups.items(),
            key=lambda kv: (str(kv[0][0]), kv[0][1] if kv[0][1] is not None else -9, kv[0][2]),
        ):
            g = [x["metrics"]["geo_daily"] for x in rs]
            dd = [x["metrics"]["max_dd"] for x in rs]
            daily = [x["daily"].get("pct_invested_sessions_profit", 0) for x in rs]
            late = [pdu.window_metrics(x, SPLIT, None).get("geo_daily", 0) for x in rs]
            label = source if rho is None else f"rho {rho}"
            lines.append(
                f"| {label} | {use} | {statistics.median(g):.3f}% | {min(g):.3f}% | "
                f"{max(g):.3f}% | {statistics.median(dd):.1f}% | {max(dd):.1f}% | "
                f"{statistics.median(daily):.0f}% | {statistics.median(late):.3f}% |"
            )
    entry = [r for r in rows if r["stage"] == "entry" and r.get("entry_metrics")]
    if entry:
        lines += [
            "",
            "## entry",
            "",
            "Multiples of the $250,000 start. B&H: the same money in TQQQ at that close.",
            "",
            "| start | plan | seed target | low | max DD | after 1y | after 2y | end | "
            "invested sessions banking a profit |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in sorted(
            entry,
            key=lambda r: (
                r["meta"]["scenario"],
                r["meta"]["entry"],
                r["meta"]["plan"],
                r["meta"]["seed_target"] or 0,
            ),
        ):
            e, m = r["entry_metrics"], r["meta"]
            lines.append(
                f"| {m['scenario']} {m['entry']} | {m['plan']} | {m['seed_target'] or '-'} | "
                f"{e['low']:.2f} | {e['max_dd']:.1f}% | {e['y1']:.2f} | {e['y2']:.2f} | "
                f"{e['end']:.2f} | {r['daily'].get('pct_invested_sessions_profit', 0):.0f}% |"
            )
    if entry:
        lines += [
            "",
            "### entry, by plan",
            "",
            "Each plan's median and worst over the four real crossings, then its worst over "
            "the three deeper bears. Multiples of the start.",
            "",
            "| plan | seed target | real: median 1y | worst 1y | median 2y | worst 2y | "
            "median low | worst low | stressed: worst 2y | worst low |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        plans: dict[tuple, dict[str, list]] = {}
        for r in entry:
            m, e = r["meta"], r["entry_metrics"]
            g = plans.setdefault((m["plan"], m["seed_target"] or 0), {"real": [], "stress": []})
            g["real" if m["scenario"] == "real" else "stress"].append(e)
        for (plan, target), g in sorted(plans.items()):
            real, stress = g["real"], g["stress"]
            if not real:
                continue

            def med(rows, key):
                return statistics.median(x[key] for x in rows)

            def worst(rows, key):
                return min(x[key] for x in rows) if rows else float("nan")

            lines.append(
                f"| {plan} | {target or '-'} | {med(real, 'y1'):.2f} | {worst(real, 'y1'):.2f} | "
                f"{med(real, 'y2'):.2f} | {worst(real, 'y2'):.2f} | {med(real, 'low'):.2f} | "
                f"{worst(real, 'low'):.2f} | {worst(stress, 'y2'):.2f} | {worst(stress, 'low'):.2f} |"
            )
        lines += [
            "",
            "TQQQ held from each real crossing (multiples of its close that day):",
            "",
            "| crossing | low | after 1y | after 2y |",
            "|---|---|---|---|",
        ]
        closes = pdu._regular_closes(FUND)
        for day in CROSSINGS:
            seg = closes[closes.index >= __import__("pandas").Timestamp(day)]
            seg = seg / seg.iloc[0]
            lines.append(
                f"| {day} | {seg.iloc[:505].min():.2f} | {seg.iloc[min(252, len(seg) - 1)]:.2f} | "
                f"{seg.iloc[min(504, len(seg) - 1)]:.2f} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--stage",
        choices=("design", "design2", "forecast", "entry", "entry2", "aggressive", "aggressive2"),
    )
    ap.add_argument("--out", type=Path)
    ap.add_argument("--proxy")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    if args.report:
        text = report(args.report)
        (args.report / "report.md").write_text(text, encoding="utf-8")
        print(text)
        return 0
    if not args.stage or not args.out:
        ap.error("--stage and --out, or --report")
    if args.stage == "design":
        specs = plan_design()
    elif args.stage == "design2":
        specs = plan_design2()
    elif args.stage == "forecast":
        specs = plan_forecast(args.out)
    elif args.stage == "entry2":
        specs = plan_entry2(args.out)
    elif args.stage == "aggressive":
        specs = plan_aggressive()
    elif args.stage == "aggressive2":
        specs = plan_aggressive2(args.out)
    else:
        specs = plan_entry(args.out)
    if args.stage not in ("design", "design2") and not args.proxy:
        ap.error("--proxy is needed from the forecast stage on")
    run_stage(specs, args.out, args.jobs, args.proxy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
