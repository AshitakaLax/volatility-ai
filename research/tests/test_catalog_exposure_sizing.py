"""research/strategies/catalog_exposure_sizing.py -- every catalog signal
computes from completed sessions only, the windowed ones equal the catalog
function run over the whole history, the strategy trades the target of
the sessions before each day exactly like Ultimate-RSP's book handed that
map, and the registration and server wiring agree."""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.optimization.optimization_controller import OptimizationController
from research.strategies.catalog_exposure_sizing import (
    SIGNALS,
    CatalogExposureSizing,
    CatalogTimingSignal,
    parse_signal_params,
)
from research.strategies.strategy_registry import SIGNAL_EXIT_STRATEGIES, resolve_strategy
from research.strategies.ultimate_rsp_sizing import UltimateRspSizing

OUTCOMES = ("Final Equity", "Realized PnL", "Trade Count", "Closed Trade Count", "Max Drawdown %")

# Small windows, so the parity checks run in seconds.
SMALL = {
    "tsmom": "lookback=40",
    "multi_timeframe": "horizons=5/10/20",
    "supertrend": "n=5",
    "macd": "fast=5;slow=12;signal=4",
    "awesome": "fast=3;slow=10",
    "sma": "window=20",
    "l1_trend": "window=30",
    "kama": "n=5;slow=10",
    "cycle_momentum": "fast=5;slow=20",
    "spectral_trend": "window=32",
    "robust_momentum": "lookback=20",
    "arfima": "window=20",
    "tail_budget": "window=80",
    "wavelet_var": "window=60;levels=3",
    "early_warning": "window=30;trend_window=15",
    "state_momentum": "lookback=40;skip=5;state_lookback=80;vol_days=10",
    "high_52w": "window=60",
    "ema_ribbon": "short=3/5;long=20/30",
    "random_forest": "trees=20;train=60;refit_days=14",
    "jump_stress": "fit_sessions=240;jump_window=30;multiple=1.5",
}


def _rows(n: int = 400, seed: int = 3, bursts: bool = False) -> list[tuple]:
    """Session OHLCV with an up leg, a slump and a recovery (and, with
    `bursts`, clusters of jumps every 60 sessions)."""
    rng = np.random.default_rng(seed)
    drift = np.r_[np.full(n // 3, 0.002), np.full(n // 3, -0.003), np.full(n - 2 * (n // 3), 0.002)]
    shocks = rng.normal(0, 0.012, n)
    if bursts:
        for start in range(30, n, 60):
            shocks[start : start + 8] += np.where(rng.random(8) < 0.6, rng.normal(0, 0.08, 8), 0)
    close = 100 * np.exp(np.cumsum(drift + shocks))
    open_ = close * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.01, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.01, n))
    volume = rng.uniform(1e5, 1e6, n)
    days = [d.toordinal() for d in pd.bdate_range("2015-01-02", periods=n).date]
    return list(zip(open_, high, low, close, volume, days, strict=True))


def _signal(name: str) -> CatalogTimingSignal:
    return CatalogTimingSignal(name, parse_signal_params(name, SMALL.get(name, "")))


@pytest.mark.parametrize("name", sorted(SIGNALS))
def test_every_signal_is_undefined_until_its_history_then_a_number(name):
    signal = _signal(name)
    rows = _rows(signal.history_sessions + 40)
    assert np.isnan(signal.evaluate(rows[: signal.history_sessions - 1]))
    values = [signal.evaluate(rows[:k]) for k in range(signal.history_sessions, len(rows), 7)]
    assert all(np.isfinite(v) or np.isnan(v) for v in values)
    assert any(np.isfinite(v) for v in values)


@pytest.mark.parametrize("name", sorted(SIGNALS))
def test_a_target_never_depends_on_a_later_session(name):
    """The target for session k is computed from sessions before k: changing
    every later session leaves it as it was."""
    signal = _signal(name)
    rows = _rows(signal.history_sessions + 30)
    k = signal.history_sessions + 10
    shocked = rows[:k] + [(o / 2, h / 2, lo / 2, c / 2, v, d) for o, h, lo, c, v, d in rows[k:]]
    assert signal.evaluate(rows[:k]) == pytest.approx(signal.evaluate(shocked[:k]), nan_ok=True)


def _closes(rows):
    return np.array([r[3] for r in rows])


# The windowed signals: their value on the trailing window is the catalog
# function's value at the same session over the whole history.
def _full_l1(rows, p):
    from research.catalog.concepts import l1_trend_positions

    return l1_trend_positions(_closes(rows), p["window"], p["lam"])


def _full_spectral(rows, p):
    from research.catalog.concepts import spectral_trend_positions

    return spectral_trend_positions(_closes(rows), p["window"], p["keep"])


def _full_robust(rows, p):
    from research.catalog.concepts import robust_momentum

    return robust_momentum(_closes(rows), p["lookback"], p["method"])


def _full_multi(rows, p):
    from research.catalog.technical_ml import multi_timeframe_trend

    return multi_timeframe_trend(_closes(rows), p["horizons"], p["mode"])


def _full_sma(rows, p):
    c = pd.Series(_closes(rows))
    return (c > c.rolling(p["window"]).mean()).astype(float).to_numpy()


def _full_tsmom(rows, p):
    from research.catalog.trend_following import tsmom_weights

    c = _closes(rows)
    r = pd.DataFrame({"r": np.r_[np.nan, np.diff(c) / c[:-1]]})
    # The catalog's weight for session t+1 is its row t+1 (data through t).
    return tsmom_weights(r, p["lookback"], p["vol_target"], p["com"])["r"].shift(-1).to_numpy()


@pytest.mark.parametrize(
    ("name", "full"),
    [
        ("l1_trend", _full_l1),
        ("spectral_trend", _full_spectral),
        ("robust_momentum", _full_robust),
        ("multi_timeframe", _full_multi),
        ("sma", _full_sma),
        ("tsmom", _full_tsmom),
    ],
)
def test_a_windowed_signal_equals_the_catalog_function_over_the_whole_history(name, full):
    signal = _signal(name)
    rows = _rows(signal.history_sessions + 60)
    reference = full(rows, signal.params)
    for k in range(signal.history_sessions, len(rows), 5):
        assert signal.evaluate(rows[:k]) == pytest.approx(reference[k - 1], abs=1e-9), k


# ------------------------------------------------------------ the strategy


def _sessions(n: int = 160, seed: int = 7) -> pd.DataFrame:
    """Minute bars (minutes 0-6 and 60-66), a rally, a slump, a rally."""
    rng = np.random.default_rng(seed)
    rows, price = [], 100.0
    for k, day in enumerate(pd.bdate_range("2022-01-03", periods=n)):
        drift = -0.01 if 60 <= k < 95 else 0.004
        for minute in [*range(7), *range(60, 67)]:
            ts = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(
                hours=9, minutes=30 + minute
            )
            o = price
            price *= np.exp(drift / 14 + 0.004 * rng.standard_normal())
            rows.append(
                (
                    ts.tz_convert("UTC"),
                    o,
                    max(o, price) * 1.001,
                    min(o, price) * 0.999,
                    price,
                    float(rng.integers(1_000, 40_000)),
                )
            )
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


def _reference_map(minutes: pd.DataFrame, name: str, params: str) -> dict:
    """{session: target} from the session aggregates, each from the
    sessions strictly before it."""
    et = minutes.index.tz_convert("America/New_York")
    g = minutes.groupby(et.date)
    daily = pd.DataFrame(
        {
            "open": g["open"].first(),
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
            "volume": g["volume"].sum(),
        }
    )
    daily["day"] = [d.toordinal() for d in daily.index]
    signal = CatalogTimingSignal(name, parse_signal_params(name, params))
    rows = list(daily.itertuples(index=False, name=None))
    out = {}
    for k, day in enumerate(daily.index):
        if k == 0:
            continue
        raw = signal.evaluate(rows[max(0, k - signal.history_sessions) : k])
        out[day] = 0.0 if not np.isfinite(raw) else max(0.0, raw)
    return out


def _run(df, strategy, params, allow_signal_exit=True):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.001],
        profit_targets=[10.0],
        strategy_class=strategy,
        strategy_params_grid=[params],
        fill_model="intrabar",
        intrabar_fill="causal",
        allow_signal_exit=allow_signal_exit,
    )


@pytest.mark.parametrize(("name", "params"), [("sma", "window=20"), ("awesome", SMALL["awesome"])])
def test_through_the_engine_it_trades_like_ultimate_rsp_handed_the_same_map(name, params):
    minutes = _sessions()
    internal = _run(
        minutes, CatalogExposureSizing, {"catalog_signal": name, "catalog_params": params}
    )
    injected = _run(
        minutes, UltimateRspSizing, {"exposure_by_date": _reference_map(minutes, name, params)}
    )
    assert internal.iloc[0]["Trade Count"] > 4
    for col in OUTCOMES:
        assert internal.iloc[0][col] == pytest.approx(injected.iloc[0][col]), col


def test_without_the_signal_exit_flag_it_never_sells():
    minutes = _sessions()
    params = {"catalog_signal": "sma", "catalog_params": "window=20"}
    held = _run(minutes, CatalogExposureSizing, params, allow_signal_exit=False).iloc[0]
    assert held["Closed Trade Count"] == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"catalog_signal": "nope"},
        {"catalog_signal": "sma", "catalog_params": "length=20"},
        {"catalog_signal": "sma", "catalog_params": "window"},
        {"catalog_signal": "robust_momentum", "catalog_params": "method=3"},
        {"catalog_signal": "sma", "rebalance_band": 0.0},
    ],
)
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        CatalogExposureSizing(**bad)


def test_signal_params_parse_lists_and_numbers():
    p = parse_signal_params("multi_timeframe", "horizons=10/30;mode=average")
    assert p == {"horizons": (10, 30), "mode": "average"}
    assert parse_signal_params("tsmom", "vol_target=1")["vol_target"] == 1.0


def test_every_form_parameter_is_a_plain_scalar():
    for name, p in inspect.signature(CatalogExposureSizing.__init__).parameters.items():
        if name == "self":
            continue
        assert isinstance(p.default, (str, int, float)), name


def test_a_live_process_replays_the_signals_history():
    assert CatalogExposureSizing(catalog_signal="kalman_trend").live_history_sessions() == 500
    assert CatalogExposureSizing(catalog_signal="sma").live_history_sessions() == 201


def test_registered_with_server_wiring_that_matches_the_strategy():
    from server.backtest import STRATEGY_DEFAULTS, describe_grid_trigger

    assert resolve_strategy("catalog_exposure") is CatalogExposureSizing
    assert "catalog_exposure" in SIGNAL_EXIT_STRATEGIES
    assert describe_grid_trigger("catalog_exposure") == {"methods": ["exposure_target"]}
    defaults = {
        n: p.default
        for n, p in inspect.signature(CatalogExposureSizing.__init__).parameters.items()
    }
    for name, value in STRATEGY_DEFAULTS["catalog_exposure"].items():
        assert defaults[name] == value, name
    CatalogExposureSizing(**STRATEGY_DEFAULTS["catalog_exposure"])


def test_the_run_form_lists_exactly_the_signals():
    from research.strategies.param_schema import _PARAM_ENUMS, CATALOG_SIGNALS

    assert list(CATALOG_SIGNALS) == sorted(SIGNALS)
    assert _PARAM_ENUMS["catalog_signal"] == sorted(SIGNALS)


def test_loading_the_registry_imports_no_catalog_dependency():
    """The live loop loads the registry: scipy and scikit-learn, which the
    catalog modules need, must stay out until a signal is computed."""
    code = (
        "import sys, research.strategies.strategy_registry; "
        "print(any(m.split('.')[0] in ('scipy', 'sklearn', 'lightgbm') for m in sys.modules))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"


@pytest.mark.parametrize(
    ("name", "params"),
    [("random_forest", SMALL["random_forest"]), ("jump_stress", SMALL["jump_stress"])],
)
def test_a_cold_start_holds_the_model_a_continuous_run_holds(name, params):
    """Live starts every session cold: a fresh signal handed the same
    trailing window must answer exactly what one running through every
    session answers, because refits are keyed by dates, not by calls."""
    continuous = CatalogTimingSignal(name, parse_signal_params(name, params))
    rows = _rows(continuous.history_sessions + 90, seed=11, bursts=True)
    need = continuous.history_sessions
    seen = set()
    for k in range(need, len(rows)):
        window = rows[k - need : k]
        cold = CatalogTimingSignal(name, parse_signal_params(name, params))
        value = continuous.evaluate(window)
        assert value == pytest.approx(cold.evaluate(window), nan_ok=True), k
        seen.add(value)
    assert {0.0, 1.0} <= seen  # both answers occur, so the check is not vacuous


# ------------------------------------------------------------ the road to live


def _live_config(allow_signal_exit=True, **live):
    from engine.core.config import BacktestConfig

    return BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "catalog_exposure",
                "strategy_params": {"catalog_signal": "kalman_trend", "rebalance_band": 0.05},
            },
            "grid": {"steps": [0.001], "profit_targets": [10.0]},
            "backtest": {"symbol": "RSP", "initial_cash": 10_000.0},
            "execution": {"allow_signal_exit": allow_signal_exit},
            "live": {"enabled": True, "step": 0.001, "profit_target": 10.0, **live},
        }
    )


def test_a_live_config_builds_it_and_needs_the_signal_exit_flag():
    from research.strategies.live_algorithm import build_strategy
    from research.strategies.strategy_registry import STRATEGIES

    strategy = build_strategy(_live_config(), STRATEGIES)
    assert isinstance(strategy, CatalogExposureSizing)
    assert strategy.live_history_sessions() == 500
    with pytest.raises(ConfigurationError, match="allow_signal_exit"):
        build_strategy(_live_config(allow_signal_exit=False), STRATEGIES)
    with pytest.raises(ConfigurationError, match="regular-session"):
        build_strategy(_live_config(extended_hours=True), STRATEGIES)


def test_a_cold_live_start_replaying_its_history_casts_the_continuous_target():
    """What the live loop does every session: a fresh strategy fed
    live_history_sessions() sessions of bars before today reaches today's
    target exactly as a run through every session did."""
    minutes = _sessions(200)
    params = {"catalog_signal": "sma", "catalog_params": "window=20"}
    days = sorted({t.date() for t in minutes.index})
    today = days[-1]

    def target_on(strategy, bars):
        for ts, row in bars.iterrows():
            ctx = SimpleNamespace(
                timestamp=ts.tz_convert("America/New_York"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                time_of_day_flag=-1,
                equity=0.0,
                cash=0.0,
            )
            strategy.record_tick(ctx)
        return strategy._signal.target

    continuous = target_on(CatalogExposureSizing(**params), minutes)
    cold = CatalogExposureSizing(**params)
    start = days[-1 - cold.live_history_sessions()]
    replay = minutes[[d >= start for d in minutes.index.date]]
    assert target_on(cold, replay) == pytest.approx(continuous)
    assert today in set(replay.index.date)
