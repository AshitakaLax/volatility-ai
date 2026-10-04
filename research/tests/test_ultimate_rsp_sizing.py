"""research/strategies/ultimate_rsp_sizing.py -- the bar-by-bar target equals
an independent vectorised computation session for session, warm-up seeds
it like the bars it replaces, the book moves to the target once a session
at execute_minute (whole lots out, one lot in), and through the real
engine the internal target trades exactly like the injected map."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import talib

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.optimization_controller import OptimizationController
from research.strategies.natr_regime import daily_bars
from research.strategies.strategy_registry import resolve_strategy
from research.strategies.ultimate_rsp_sizing import RspTimingSignal, UltimateRspSizing

SMALL = {"pd_periods": "5,8", "pd_lookbacks": "20,30", "ad_params": "3/10", "ad_lookbacks": "20"}
OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")


def _sessions(n: int = 160, seed: int = 4) -> pd.DataFrame:
    """n sessions of 14 one-minute bars at minutes 0-6 and 60-66 (so the
    default execution minute exists), alternating calm and stormy
    stretches, with volume."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2021-01-04", periods=n)):
        vol = 0.003 if (k // 15) % 2 == 0 else 0.012
        for minute in [*range(7), *range(60, 67)]:
            ts = pd.Timestamp(day).tz_localize("UTC") + pd.Timedelta(hours=14, minutes=30 + minute)
            o = price
            price *= np.exp(0.0002 + vol * rng.standard_normal())
            hi, lo = max(o, price) * (1 + vol / 3), min(o, price) * (1 - vol / 3)
            rows.append((ts, o, hi, lo, price, float(rng.integers(1_000, 50_000))))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


def _daily(minutes: pd.DataFrame) -> pd.DataFrame:
    d = daily_bars(minutes)
    d["volume"] = minutes["volume"].resample("1D").sum().reindex(d.index)
    return d


def _reference_targets(daily: pd.DataFrame, w: float = 0.5) -> dict:
    """{session: target} computed vectorised (pandas rolling medians over
    full-history TA-Lib series), each keyed by the session it applies to."""
    H, L, C, V = (daily[k].to_numpy(float) for k in ("high", "low", "close", "volume"))

    def below(x: np.ndarray, lb: int) -> pd.Series:
        s = pd.Series(x, index=daily.index)
        return (s < s.rolling(lb, min_periods=lb).median()).fillna(False)

    pd_votes = [below(talib.PLUS_DM(H, L, timeperiod=p), lb) for p in (5, 8) for lb in (20, 30)]
    ad_votes = [below(talib.ADOSC(H, L, C, V, fastperiod=3, slowperiod=10), 20)]
    target = w * sum(v.astype(float) for v in pd_votes) / len(pd_votes) + (1 - w) * sum(
        v.astype(float) for v in ad_votes
    ) / len(ad_votes)
    days = [t.date() for t in daily.index]
    return {days[i + 1]: float(target.iloc[i]) for i in range(len(days) - 1)}


def _signal_targets(minutes: pd.DataFrame, signal: RspTimingSignal) -> dict:
    out, day = {}, None
    for ts, row in minutes.iterrows():
        signal.observe(ts, row["high"], row["low"], row["close"], row["volume"])
        if ts.date() != day:
            day = ts.date()
            if signal.target is not None:
                out[day] = signal.target
    return out


def _small_signal() -> RspTimingSignal:
    return RspTimingSignal(
        pd_periods=(5, 8), pd_lookbacks=(20, 30), ad_params=((3, 10),), ad_lookbacks=(20,)
    )


def test_the_incremental_target_equals_the_vectorised_reference():
    minutes = _sessions()
    ref = _reference_targets(_daily(minutes))
    got = _signal_targets(minutes, _small_signal())
    assert got == pytest.approx(ref)
    assert len(set(got.values())) > 3  # many exposure levels occur


def test_warm_up_from_session_bars_matches_replaying_the_minutes():
    minutes = _sessions()
    cut = sorted({t.date() for t in minutes.index})[100]
    history, live = minutes[minutes.index.date < cut], minutes[minutes.index.date >= cut]
    full, seeded = _small_signal(), _small_signal()
    assert seeded.warm_up(_daily(history)) == 100
    for ts, row in minutes.iterrows():
        full.observe(ts, row["high"], row["low"], row["close"], row["volume"])
        if ts.date() >= cut:
            seeded.observe(ts, row["high"], row["low"], row["close"], row["volume"])
            assert seeded.target == pytest.approx(full.target)
    assert live.index.size > 0


def test_warm_up_rejects_unordered_history():
    daily = _daily(_sessions(30))
    with pytest.raises(ConfigurationError):
        _small_signal().warm_up(daily.iloc[::-1])
    with pytest.raises(ConfigurationError):
        _small_signal().warm_up(daily.drop(columns="volume"))


def _et_minute(ts) -> int:
    et = ts.tz_convert("America/New_York")
    return et.hour * 60 + et.minute - 570


def _ctx(ts, price, *, cash, equity, lots=0, minute=None, volume=10_000.0):
    return MarketContext(
        timestamp=ts,
        open=price,
        high=price,
        low=price,
        close=price,
        cash=cash,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=0,
        time_of_day_flag=minute if minute is not None else _et_minute(ts),
        volume=volume,
    )


class _Lot:
    def __init__(self, oid, shares):
        self.order_id, self.shares = oid, shares


def test_rebalances_once_a_session_at_the_execution_minute_in_whole_lots():
    day = pd.Timestamp("2024-03-04 14:30", tz="UTC")
    s = UltimateRspSizing(exposure_by_date={day.date(): 0.5}, execute_minute=60)
    s.record_tick(_ctx(day, 100.0, cash=100_000, equity=100_000, minute=0))
    assert (
        s._grid_trigger_level(_ctx(day, 100.0, cash=1, equity=1), 0, 0) == 0.0
    )  # nothing before the minute
    s.record_tick(_ctx(day + pd.Timedelta(minutes=60), 100.0, cash=100_000, equity=100_000))
    bar = _ctx(day + pd.Timedelta(minutes=60), 100.0, cash=100_000, equity=100_000)
    assert s._grid_trigger_level(bar, 0, 0) >= bar.high  # buy this bar, at any fill model
    assert s.calculate_trade_value(_ctx(day, 100.0, cash=100_000, equity=100_000)) == pytest.approx(
        50_000
    )
    s.record_tick(_ctx(day + pd.Timedelta(minutes=61), 100.0, cash=50_000, equity=100_000, lots=1))
    assert (
        s._grid_trigger_level(_ctx(day, 100.0, cash=1, equity=1), 0, 0) == 0.0
    )  # once per session

    nxt = pd.Timestamp("2024-03-05 15:30", tz="UTC")  # minute 60
    s = UltimateRspSizing(exposure_by_date={nxt.date(): 0.25}, execute_minute=60)
    lots = [_Lot(f"L{i}", 250.0) for i in range(4)]  # four $25k lots at $100
    s.record_tick(_ctx(nxt, 100.0, cash=0.0, equity=100_000, lots=4))
    sold = s.lots_to_liquidate(lots, _ctx(nxt, 100.0, cash=0.0, equity=100_000, lots=4))
    assert [lot.order_id for lot in sold] == ["L3", "L2", "L1"]  # newest first, 75% of equity


def test_a_zero_target_sells_every_lot_and_a_small_drift_trades_nothing():
    t = pd.Timestamp("2024-03-05 15:30", tz="UTC")
    lots = [_Lot("A", 300.0), _Lot("B", 700.0)]
    s = UltimateRspSizing(exposure_by_date={t.date(): 0.0})
    s.record_tick(_ctx(t, 100.0, cash=0.0, equity=100_000, lots=2))
    assert s.lots_to_liquidate(lots, _ctx(t, 100.0, cash=0.0, equity=100_000)) == lots
    s = UltimateRspSizing(exposure_by_date={t.date(): 0.97}, rebalance_band=0.05)
    s.record_tick(_ctx(t, 100.0, cash=0.0, equity=100_000, lots=2))
    assert s.lots_to_liquidate(lots, _ctx(t, 100.0, cash=0.0, equity=100_000)) == []
    assert s._grid_trigger_level(_ctx(t, 100.0, cash=1, equity=1), 0, 0) == 0.0


def _run(df, params, allow_signal_exit=True, full=False, **sweep):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.001],
        profit_targets=[10.0],
        strategy_class=UltimateRspSizing,
        strategy_params_grid=[params],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=allow_signal_exit,
        return_full_results=full,
        **sweep,
    )


def test_through_the_engine_the_internal_target_trades_like_the_injected_map():
    minutes = _sessions()
    ref = _reference_targets(_daily(minutes))
    internal = _run(minutes, SMALL).iloc[0]
    injected = _run(minutes, {"exposure_by_date": ref}).iloc[0]
    assert internal["Trade Count"] > 10
    for col in OUTCOMES:
        assert internal[col] == pytest.approx(injected[col]), col


def test_the_exit_is_a_signal_exit_and_needs_the_flag():
    minutes = _sessions()
    _, full = _run(minutes, SMALL, full=True)
    blot = full[0].trade_blotter
    sells = blot[blot["side"] == "sell"]
    assert len(sells) > 0
    assert sells["sell_reason"].astype(str).str.lower().str.contains("signal").all()
    buys = blot[blot["side"] == "buy"]
    assert (buys["timestamp"].map(_et_minute) == 60).all()  # every rebalance at the minute
    _, held = _run(minutes, SMALL, allow_signal_exit=False, full=True)
    assert (held[0].trade_blotter["side"] == "sell").sum() == 0  # no exit without the flag


@pytest.mark.parametrize(
    "bad",
    [
        {"pd_periods": "a,b"},
        {"ad_params": "10/3"},
        {"pd_weight": 1.5},
        {"execute_minute": 400},
        {"rebalance_band": 0.0},
        {"max_exposure": 0.0},
    ],
)
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        UltimateRspSizing(**bad)


def test_every_form_parameter_is_a_plain_scalar():
    """The server builds its run form from the signature: str/float/int
    fields only (the injected map is research wiring, hidden there)."""
    sig = inspect.signature(UltimateRspSizing.__init__)
    for name, p in sig.parameters.items():
        if name in ("self", "exposure_by_date"):
            continue
        assert p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD, name
        assert isinstance(p.default, (str, int, float)), name


def test_a_sweep_handed_the_history_trades_the_window_on_the_full_history_target():
    """The server's path: run_sweep(warm_up_daily=...) on a window too short
    to compute the target itself trades exactly as if the full-history
    causal map had been injected."""
    minutes = _sessions()
    cut = sorted({t.date() for t in minutes.index})[100]
    history, live = minutes[minutes.index.date < cut], minutes[minutes.index.date >= cut]
    injected = _run(live, {"exposure_by_date": _reference_targets(_daily(minutes))}).iloc[0]
    warmed = _run(live, SMALL, warm_up_daily=_daily(history)).iloc[0]
    cold = _run(live, SMALL).iloc[0]
    assert injected["Trade Count"] > 0
    for col in OUTCOMES:
        assert warmed[col] == pytest.approx(injected[col]), col
    assert warmed["warm_up_sessions"] == 100
    assert cold["Trade Count"] < injected["Trade Count"]  # cold, it waits for its medians


def test_the_server_warm_up_history_carries_the_volume_this_strategy_needs():
    from server.backtest import warm_up_history

    minutes = _sessions(60)
    frame = minutes[minutes.index.date >= sorted({t.date() for t in minutes.index})[40]]
    daily = warm_up_history(UltimateRspSizing, minutes, frame)
    assert len(daily) == 40 and "volume" in daily
    assert UltimateRspSizing(**SMALL).warm_up(daily) == 40


def test_registered_with_server_wiring_that_matches_the_strategy():
    from server.backtest import (
        _HIDDEN_PARAMS,
        SIGNAL_EXIT_STRATEGIES,
        STRATEGY_DEFAULTS,
        describe_grid_trigger,
    )

    assert resolve_strategy("ultimate_rsp") is UltimateRspSizing
    assert "exposure_by_date" in _HIDDEN_PARAMS
    assert "ultimate_rsp" in SIGNAL_EXIT_STRATEGIES  # its only exit is a signal exit
    assert describe_grid_trigger("ultimate_rsp") == {"methods": ["exposure_target"]}
    defaults = {
        n: p.default for n, p in inspect.signature(UltimateRspSizing.__init__).parameters.items()
    }
    for name, value in STRATEGY_DEFAULTS["ultimate_rsp"].items():
        assert defaults[name] == value, name  # the committed values are the defaults
    UltimateRspSizing(**STRATEGY_DEFAULTS["ultimate_rsp"])


def test_the_pinned_config_is_the_server_default_with_the_signal_exit_on():
    from server.backtest import STRATEGY_DEFAULTS

    config = BacktestConfig.from_yaml(
        Path(__file__).resolve().parents[2] / "config" / "ultimate_rsp.yaml"
    )
    config.validate()
    assert config.strategy.strategy_id == "ultimate_rsp"
    assert dict(config.strategy.strategy_params) == STRATEGY_DEFAULTS["ultimate_rsp"]
    kwargs = config.to_run_sweep_kwargs(UltimateRspSizing)
    assert kwargs["allow_signal_exit"] is True
    assert kwargs["profit_targets"] == [10.0]  # the book holds; it does not harvest


@pytest.mark.parametrize(
    "fill", [("close", "level"), ("intrabar", "level"), ("intrabar", "open_or_level")]
)
def test_every_fill_model_books_buys_inside_the_bar(fill):
    """The buy level must be a price the bar could trade at: the legacy
    level booking fills AT the level, so a sentinel would become the price."""
    minutes = _sessions()
    _, full = OptimizationController(historical_data=minutes).run_sweep(
        grid_steps=[0.001],
        profit_targets=[10.0],
        strategy_class=UltimateRspSizing,
        strategy_params_grid=[SMALL],
        fill_model=fill[0],
        intrabar_fill=fill[1],
        allow_signal_exit=True,
        return_full_results=True,
    )
    blot = full[0].trade_blotter
    buys = blot[blot["side"] == "buy"].set_index("timestamp")
    assert len(buys) > 0
    bars = minutes.loc[buys.index]
    assert ((buys["price"] >= bars["low"] - 1e-9) & (buys["price"] <= bars["high"] + 1e-9)).all()


def test_the_incremental_indicators_are_ta_libs():
    """PLUS_DM and ADOSC recomputed one session at a time equal TA-Lib's
    full-history series value for value (TA-Lib is the reference only)."""
    from research.strategies.ultimate_rsp_sizing import _Adosc, _PlusDM

    rng = np.random.default_rng(7)
    close = 100 * np.exp(np.cumsum(0.01 * rng.standard_normal(400)))
    high = close * (1 + 0.01 * rng.random(400))
    low = close * (1 - 0.01 * rng.random(400))
    vol = rng.integers(1_000, 90_000, 400).astype(float)
    for p in (2, 5, 14, 42):
        ind, prev, got = _PlusDM(p), None, []
        for i in range(400):
            dm = 0.0
            if prev is not None:
                up, down = high[i] - high[prev], low[prev] - low[i]
                dm = up if (up > 0 and up > down) else 0.0
            got.append(ind.update(i, dm))
            prev = i
        np.testing.assert_allclose(
            got, talib.PLUS_DM(high, low, timeperiod=p), rtol=1e-12, equal_nan=True
        )
    ad = np.cumsum(np.where(high > low, ((close - low) - (high - close)) / (high - low) * vol, 0.0))
    for fast, slow in ((3, 10), (10, 40)):
        ind = _Adosc(fast, slow)
        got = [ind.update(i, ad[i]) for i in range(400)]
        want = talib.ADOSC(high, low, close, vol, fastperiod=fast, slowperiod=slow)
        np.testing.assert_allclose(got, want, rtol=1e-9, atol=1e-6, equal_nan=True)


def test_loading_the_registry_needs_no_optional_indicator_library():
    """The live loop loads the strategy registry; requirements.txt's rule is
    that it must start without TA-Lib (requirements-indicators.txt)."""
    import subprocess
    import sys

    code = (
        "import sys, research.strategies.strategy_registry; "
        "print('talib' in sys.modules, 'polars' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.split() == ["False", "False"]
