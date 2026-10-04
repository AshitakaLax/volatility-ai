"""research/strategies/ultimate_sizing.py -- calm is the champion sleeve
exactly, turbulent buys only capitulation closes, the flip liquidates calm
lots only, and the internal regime equals the injected causal map."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.optimization.optimization_controller import OptimizationController
from research.strategies.natr_regime import calm_by_date, daily_bars, debounce
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing
from research.strategies.ultimate_sizing import UltimateSizing

HF = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 20}
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")


def _sessions(n: int = 300, seed: int = 1) -> pd.DataFrame:
    """n sessions of 20 one-minute bars (minutes 0-9 and 380-389, so the
    closing window exists); volatility regimes switch every 30 sessions
    and the turbulent ones trend down with big down days."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2020-01-02", periods=n)):
        turbulent = (k // 30) % 2 == 1
        vol = 0.012 if turbulent else 0.002
        drift = -0.004 if turbulent else 0.0015
        for minute in [*range(10), *range(380, 390)]:
            ts = pd.Timestamp(day).tz_localize("UTC") + pd.Timedelta(hours=14, minutes=30 + minute)
            o = price
            price = price * np.exp(drift / 20 + vol * rng.standard_normal())
            rows.append((ts, o, max(o, price) * 1.0005, min(o, price) * 0.9995, price, 10_000))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


def _run(df, cls, params, target=0.01, full=False):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[{**HF, **params}],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=True,
        return_full_results=full,
    )


def test_all_calm_is_the_calm_regime_sleeve_exactly():
    df = _sessions(60)
    days = sorted({t.date() for t in df.index})
    calm = dict.fromkeys(days, True)
    a = _run(df, RegimeSleeveSizing, {"sleeve": "calm", "regime_by_date": calm}).iloc[0]
    b = _run(df, UltimateSizing, {"regime_by_date": calm}).iloc[0]
    assert a["Trade Count"] > 0
    for col in OUTCOMES:
        assert b[col] == a[col], col


def test_internal_regime_equals_the_injected_causal_map():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    injected = _run(df, UltimateSizing, {"regime_by_date": reg, "reversal_threshold": -0.02}).iloc[
        0
    ]
    internal = _run(
        df,
        UltimateSizing,
        {"natr_period": 5, "natr_lookback": 20, "regime_min_hold": 3, "reversal_threshold": -0.02},
    ).iloc[0]
    for col in OUTCOMES:
        assert internal[col] == injected[col], col


def test_turbulent_buys_only_reversal_lots_with_their_own_target_and_flip_liquidates_calm():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    _, full = _run(
        df,
        UltimateSizing,
        {
            "regime_by_date": reg,
            "reversal_threshold": -0.02,
            "reversal_target": 0.02,
            "reversal_lot_pct": 0.05,
            "reversal_max_lots": 2,
        },
        target=0.30,
        full=True,
    )
    blot = full[0].trade_blotter
    buys = blot[blot["side"] == "buy"].copy()
    buys["day"] = buys["timestamp"].dt.date
    turbulent_days = {d for d, calm in reg.items() if not calm}
    tb = buys[buys["day"].isin(turbulent_days)]
    assert len(tb) > 0
    minute = tb["timestamp"].dt.hour * 60 + tb["timestamp"].dt.minute - (14 * 60 + 30)
    assert (minute >= 380).all()  # only in the closing window
    assert tb.groupby("day").size().max() == 1  # one per session
    notional = (tb["price"] * tb["qty"]).to_numpy()
    assert np.allclose(notional, 100_000 * 0.05, rtol=0.02)
    sells = blot[blot["side"] == "sell"]
    targets = sells[sells["sell_reason"].str.lower().str.contains("profit_target")]
    signal = sells[sells["sell_reason"].str.lower().str.contains("signal_exit")]
    reversal_ids = set(tb["lot_id"])
    assert set(signal["lot_id"]).isdisjoint(reversal_ids)  # flips liquidate calm lots only
    rev_sells = targets[targets["lot_id"].isin(reversal_ids)]
    assert len(rev_sells) > 0
    paid = buys.set_index("lot_id").loc[rev_sells["lot_id"], "price"].to_numpy()
    gain = rev_sells["price"].to_numpy() / paid - 1
    assert (gain < 0.05).all()  # sold near the 2% reversal target, not the 30% grid target
    assert (targets["profit_realized"] >= -1e-8).all()


def test_cash_mode_buys_nothing_while_turbulent():
    df = _sessions(300)
    reg = debounce(calm_by_date(daily_bars(df), period=5, lookback=20, lag=1), 3)
    _, full = _run(df, UltimateSizing, {"regime_by_date": reg, "turbulent_mode": "cash"}, full=True)
    buys = full[0].trade_blotter.query("side == 'buy'")
    turbulent_days = {d for d, calm in reg.items() if not calm}
    assert not buys["timestamp"].dt.date.isin(turbulent_days).any()


@pytest.mark.parametrize(
    "bad",
    [
        {"turbulent_mode": "short"},
        {"reversal_lot_pct": 0.0},
        {"reversal_target": 0.0},
        {"reversal_threshold": 0.01},
    ],
)
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        UltimateSizing(**HF, **bad)
