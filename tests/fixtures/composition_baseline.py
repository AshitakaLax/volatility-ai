"""
Phase 0 of docs/research/buy-sell-composition.md: today's trading behaviour,
pinned before the buy x sell composition work touches the sell path.

Every case below runs one strategy over a fixed synthetic minute-bar dataset
(composition_ohlcv.csv, committed so a change in numpy's random stream can
never move it) and records:

  * the summary row run_sweep returns, minus the per-run timing columns;
  * a digest of the FULL trade blotter, every buy and sell with its price,
    quantity, lot and reason, so a change in which lots sell, when, or for
    how much fails the test even when the headline numbers happen to agree.

The cases cover every sell path the plan changes: whole-lot harvests at a
target under both fill models, trailing and decaying targets (the
retargeting path), signal exits of every lot and of a fraction of them
(harvest_sleeve), Ultimate's regime exit with its reversal lots, the
exposure books' rebalancing exits, and the intraday-validation replay.

Regenerate ONLY when a change is meant to move these results, and say why
in the commit:

    python -m tests.fixtures.composition_baseline --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OHLCV_PATH = os.path.join(_THIS_DIR, "composition_ohlcv.csv")
BASELINE_PATH = os.path.join(_THIS_DIR, "composition_baseline.json")

SESSIONS = 300
REGIME_LENGTH = 30  # sessions per calm/stormy stretch
MINUTES = (*range(10), *range(60, 67), *range(380, 390))
BARS_PER_DAY = len(MINUTES)

# Columns that describe the run rather than its outcome.
_VOLATILE_COLUMNS = frozenset({"Elapsed ms", "elapsed_ms", "Runtime Seconds"})


def stormy(session_index: int) -> bool:
    return (session_index // REGIME_LENGTH) % 2 == 1


def generate_ohlcv(seed: int = 20261031) -> pd.DataFrame:
    """SESSIONS sessions of minute bars at MINUTES (the open, the execution
    minute the exposure books use, and the closing window Ultimate reads),
    New York time. Calm stretches drift up; stormy ones are four times as
    volatile and fall, with one deep slump so regime exits and stranded lots
    both happen."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2021-01-04", periods=SESSIONS)):
        vol = 0.008 if stormy(k) else 0.002
        drift = -0.003 if stormy(k) else 0.0012
        if 150 <= k < 170:
            drift = -0.012
        for minute in MINUTES:
            ts = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(
                hours=9, minutes=30 + minute
            )
            o = price
            price = price * math.exp(drift / BARS_PER_DAY + vol * rng.standard_normal())
            rows.append(
                (
                    ts.tz_convert("UTC").isoformat(),
                    round(o, 6),
                    round(max(o, price) * (1 + vol / 4), 6),
                    round(min(o, price) * (1 - vol / 4), 6),
                    round(price, 6),
                    int(rng.integers(1_000, 50_000)),
                )
            )
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def load_ohlcv() -> pd.DataFrame:
    df = pd.read_csv(OHLCV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.set_index("timestamp")


def calm_map(df: pd.DataFrame) -> dict:
    """{session date: calm?} from the generator's own regime labels, for the
    sleeves that take an injected regime."""
    days = sorted({ts.tz_convert("America/New_York").date() for ts in df.index})
    return {day: not stormy(k) for k, day in enumerate(days)}


def causal_regime(df: pd.DataFrame) -> dict:
    """Ultimate's own causal NATR regime, short windows so 300 sessions are
    enough (the shape research/tests/test_ultimate_sizing.py injects)."""
    from research.strategies.natr_regime import calm_by_date, daily_bars, debounce

    return debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)


HF = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": BARS_PER_DAY}
EXPOSURE = {"pd_periods": "5,8", "pd_lookbacks": "20,30", "ad_params": "3/10", "ad_lookbacks": "20"}


@dataclass(frozen=True)
class Case:
    name: str
    strategy: Callable[[], type]
    params: Callable[[pd.DataFrame], dict]
    step: float = 0.002
    target: float = 0.01
    sweep: dict = field(default_factory=dict)
    intraday: bool = False  # run through intraday_validation instead of run_sweep


def _cls(path: str) -> Callable[[], type]:
    module, name = path.rsplit(".", 1)

    def load() -> type:
        return getattr(__import__(module, fromlist=[name]), name)

    return load


HF_CLS = _cls("research.strategies.high_frequency_sizing.HighFrequencyLocalReferenceSizing")
GATED_CLS = _cls("research.strategies.gated_local_reference_sizing.GatedLocalReferenceSizing")
HARVEST_CLS = _cls("research.strategies.harvest_sleeve_sizing.HarvestSleeveSizing")
ULTIMATE_CLS = _cls("research.strategies.ultimate_sizing.UltimateSizing")
RSP_CLS = _cls("research.strategies.ultimate_rsp_sizing.UltimateRspSizing")
CATALOG_CLS = _cls("research.strategies.catalog_exposure_sizing.CatalogExposureSizing")
FIXED_CLS = _cls("research.strategies.size_calculators.FixedPortfolioPercentage")

INTRABAR = {"fill_model": "intrabar", "intrabar_fill": "causal"}
SIGNAL = {**INTRABAR, "allow_signal_exit": True}

CASES: tuple[Case, ...] = (
    Case("fixed-close", FIXED_CLS, lambda df: {"allocation_pct": 0.05}, step=0.01, target=0.005),
    Case("champion-close", HF_CLS, lambda df: dict(HF)),
    Case("champion-intrabar", HF_CLS, lambda df: dict(HF), sweep=INTRABAR),
    Case("champion-intrabar-level", HF_CLS, lambda df: dict(HF), sweep={"fill_model": "intrabar"}),
    Case("champion-trailing", HF_CLS, lambda df: {**HF, "trail_pct": 0.003}, sweep=INTRABAR),
    Case(
        "entry-gated-momentum",
        GATED_CLS,
        lambda df: {**HF, "momentum_gate": "early_negative"},
        sweep=INTRABAR,
    ),
    Case(
        "harvest-decay",
        HARVEST_CLS,
        lambda df: {**HF, "target_decay_after_bars": 200, "target_decay_span_bars": 400},
        sweep=INTRABAR,
    ),
    Case(
        "harvest-calm-sleeve-full-exit",
        HARVEST_CLS,
        lambda df: {**HF, "sleeve": "calm", "regime_by_date": calm_map(df)},
        sweep=SIGNAL,
    ),
    Case(
        "harvest-calm-sleeve-partial-exit",
        HARVEST_CLS,
        lambda df: {
            **HF,
            "sleeve": "calm",
            "regime_by_date": calm_map(df),
            "liquidate_fraction": 0.5,
            "liquidate_minute": 5,
        },
        sweep=SIGNAL,
    ),
    Case(
        "ultimate",
        ULTIMATE_CLS,
        lambda df: {
            **HF,
            "regime_by_date": causal_regime(df),
            "reversal_threshold": -0.02,
            "reversal_target": 0.02,
            "reversal_lot_pct": 0.05,
            "reversal_max_lots": 2,
        },
        target=0.05,
        sweep=SIGNAL,
    ),
    Case("ultimate-rsp", RSP_CLS, lambda df: dict(EXPOSURE), step=0.001, target=10.0, sweep=SIGNAL),
    Case(
        "catalog-exposure-sma",
        CATALOG_CLS,
        lambda df: {"catalog_signal": "sma", "catalog_params": "window=20"},
        step=0.001,
        target=10.0,
        sweep=SIGNAL,
    ),
    Case("champion-intraday-replay", HF_CLS, lambda df: dict(HF), intraday=True),
)


def _plain(value: Any) -> Any:
    """A JSON-stable form of one value: floats to 9 significant digits."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return float(f"{value:.9g}")
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def blotter_digest(blotter: pd.DataFrame) -> dict:
    """Row count, sell count and a SHA-256 over every row, columns sorted."""
    if blotter is None or blotter.empty:
        return {"rows": 0, "sells": 0, "sha256": None}
    columns = sorted(blotter.columns)
    rows = [[_plain(row[c]) for c in columns] for _, row in blotter.iterrows()]
    payload = json.dumps({"columns": columns, "rows": rows}, sort_keys=True)
    sells = int((blotter["side"] == "sell").sum()) if "side" in blotter.columns else 0
    return {
        "rows": len(rows),
        "sells": sells,
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
    }


def _summary(row: dict) -> dict:
    out = {}
    for key, value in row.items():
        if key in _VOLATILE_COLUMNS or isinstance(value, (dict, list, tuple)):
            continue
        out[str(key)] = _plain(value)
    return out


def run_case(case: Case, df: pd.DataFrame) -> dict:
    from research.optimization import intraday_validation
    from research.optimization.optimization_controller import OptimizationController

    strategy = case.strategy()
    params = case.params(df)
    if case.intraday:
        metrics = intraday_validation.simulate_single_intraday(
            intraday_data=df,
            grid_step=case.step,
            profit_target=case.target,
            strategy_class=strategy,
            strategy_params=params,
        )
        return {"summary": _summary(metrics), "blotter": None}
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[case.step],
        profit_targets=[case.target],
        strategy_class=strategy,
        strategy_params_grid=[params],
        return_full_results=True,
        **case.sweep,
    )
    if len(summary) != 1 or full[0] is None:
        raise AssertionError(f"{case.name}: the combination failed: {summary.to_dict('records')}")
    row = summary.iloc[0].to_dict()
    row = {k: v for k, v in row.items() if k not in params}  # params are inputs, not outcomes
    return {"summary": _summary(row), "blotter": blotter_digest(full[0].trade_blotter)}


def compute_all() -> dict:
    df = load_ohlcv()
    return {case.name: run_case(case, df) for case in CASES}


def load_baseline() -> dict | None:
    if not os.path.exists(BASELINE_PATH):
        return None
    with open(BASELINE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--write", action="store_true", help="write the CSV (if absent) and baseline"
    )
    parser.add_argument("--regenerate-data", action="store_true", help="rewrite the OHLCV CSV too")
    args = parser.parse_args()
    if args.regenerate_data or not os.path.exists(OHLCV_PATH):
        generate_ohlcv().to_csv(OHLCV_PATH, index=False)
    results = compute_all()
    text = json.dumps(results, indent=1, sort_keys=True) + "\n"
    if args.write:
        with open(BASELINE_PATH, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
