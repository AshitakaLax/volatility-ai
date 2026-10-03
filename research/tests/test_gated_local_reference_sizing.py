"""GatedLocalReferenceSizing (hf_entry_gated) through the real controller.

Three claims, each pinned under BOTH fill models, because the intrabar
path never calls _check_grid_trigger and a gate that only worked under
"close" would pass any close-only test:

  1. Gates off IS the champion -- identical metrics, not similar ones.
  2. A shut gate blocks buys, end to end, on the bars it should.
  3. Nothing here can realize a loss: no exit hook is overridden.
"""

from __future__ import annotations

import inspect
import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from engine.core.sizing import SizingStrategy
from research.optimization.optimization_controller import OptimizationController
from research.strategies import entry_gates
from research.strategies.gated_local_reference_sizing import (
    NO_BUY_LEVEL,
    GatedLocalReferenceSizing,
)
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.strategy_registry import STRATEGIES, resolve_strategy

FIXTURE = "tests/fixtures/regression_ohlcv.csv"
FILL_MODELS = ("close", "intrabar")

# Outcomes, not identity columns: "Strategy" names the class and the gate
# columns exist only on one side, so neither belongs in an equality check.
OUTCOMES = (
    "Final Equity",
    "Total Return %",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Max Drawdown %",
    "Return/Drawdown",
    "CAGR %",
)

HF_PARAMS = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 120}


def _fixture() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")


def _minute_sessions(gap_day: int | None = None, days: int = 6) -> pd.DataFrame:
    """`days` sessions of 120 one-minute bars from 09:30 EST, oscillating
    +/-0.6% on a 12-minute cycle so the local-reference grid buys and
    sells all day. On `gap_day`, the session opens 3% below the previous
    session's low and oscillates there -- a gap-down the prior_low gate
    must block from the first bar."""
    frames = []
    base = 100.0
    prev_low = None
    for day in range(days):
        start = pd.Timestamp("2024-01-02 14:30", tz="UTC") + pd.offsets.BDay(day)
        index = pd.date_range(start, periods=120, freq="1min")
        level = base if day != gap_day else prev_low * 0.97
        wave = level * (1 + 0.006 * np.sin(np.arange(120) * 2 * math.pi / 12))
        opens = np.r_[level, wave[:-1]]
        highs = np.maximum(opens, wave) * 1.001
        lows = np.minimum(opens, wave) * 0.999
        frames.append(
            pd.DataFrame(
                {"open": opens, "high": highs, "low": lows, "close": wave, "volume": 10_000},
                index=index,
            )
        )
        prev_low = lows.min()
    return pd.concat(frames)


def _run(df, cls, fill_model, extra=None, full=False):
    controller = OptimizationController(historical_data=df)
    out = controller.run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.004],
        strategy_class=cls,
        strategy_params_grid=[{**HF_PARAMS, **(extra or {})}],
        fill_model=fill_model,
        return_full_results=full,
    )
    return out


# --------------------------------------------------------------------
# 1. Off is the champion


@pytest.mark.parametrize("fill_model", FILL_MODELS)
@pytest.mark.parametrize("data", ["fixture", "minutes"])
def test_gates_off_reproduces_the_champion_exactly(fill_model, data):
    df = _fixture() if data == "fixture" else _minute_sessions(gap_day=4)
    champion = _run(df, HighFrequencyLocalReferenceSizing, fill_model).iloc[0]
    gated = _run(df, GatedLocalReferenceSizing, fill_model).iloc[0]
    assert champion["Trade Count"] > 0, "a run with no trades would prove nothing"
    for column in OUTCOMES:
        assert gated[column] == champion[column], column


def test_signature_mirrors_the_parent():
    """Every parent parameter, same name, default, annotation and kind,
    in the same order, as a prefix. A parameter added to the champion
    and not here would be silently unreachable through this strategy --
    from YAML, from the run form, and from analyze_annual."""
    parent = list(inspect.signature(HighFrequencyLocalReferenceSizing.__init__).parameters.values())
    child = list(inspect.signature(GatedLocalReferenceSizing.__init__).parameters.values())
    assert [(p.name, p.default, p.annotation, p.kind) for p in parent] == [
        (p.name, p.default, p.annotation, p.kind) for p in child[: len(parent)]
    ]
    gate_params = list(child[len(parent) :])
    assert all(p.default is not inspect.Parameter.empty for p in gate_params), (
        "a gate parameter without a default would make existing champion configs fail"
    )


def test_every_parent_argument_is_passed_through():
    """The mirror above is only half of it: a parameter accepted here
    but not forwarded would be silently ignored."""
    kwargs = {
        **HF_PARAMS,
        "event_day_boost_multiplier": 2.5,
        "vol_scale_exponent": -1.5,
        "vol_measure": "range",
        "trail_pct": 0.05,
        "dd_throttle_start": 0.3,
        "implied_vol_exponent": 0.4,
    }
    gated = GatedLocalReferenceSizing(**kwargs)
    champion = HighFrequencyLocalReferenceSizing(**kwargs)
    for name in inspect.signature(HighFrequencyLocalReferenceSizing.__init__).parameters:
        if name != "self" and hasattr(champion, name):
            assert getattr(gated, name) == getattr(champion, name), name


# --------------------------------------------------------------------
# 2. A shut gate blocks buys


def _context(price: float) -> MarketContext:
    return MarketContext(
        timestamp=pd.Timestamp("2024-01-02 14:30", tz="UTC"),
        open=price,
        high=price,
        low=price,
        close=price,
        cash=1e5,
        equity=1e5,
        peak_equity=1e5,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


def test_a_shut_gate_returns_an_unreachable_level():
    strategy = GatedLocalReferenceSizing(**HF_PARAMS, breakdown_gate="prior_low")
    ctx = _context(10.0)
    strategy.record_tick(ctx)
    open_level = strategy._grid_trigger_level(ctx, last_buy_price=10.0, step=0.01)
    assert open_level > 0

    strategy._entry_suppressed = True
    assert strategy._grid_trigger_level(ctx, 10.0, 0.01) == NO_BUY_LEVEL
    # The default boolean routes through the level -- the close path.
    assert strategy._check_grid_trigger(_context(1e-9), 10.0, 0.01) is False


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_prior_low_gate_blocks_every_buy_on_the_gap_day(fill_model):
    gap_day = 4
    df = _minute_sessions(gap_day=gap_day)
    gap_date = (pd.Timestamp("2024-01-02") + pd.offsets.BDay(gap_day)).date()

    def buys_on_gap_day(cls, extra=None):
        _, full = _run(df, cls, fill_model, extra, full=True)
        blotter = full[0].trade_blotter
        buys = blotter[blotter["side"] == "buy"]
        stamps = pd.to_datetime(buys["timestamp"], utc=True)
        return int((stamps.dt.date == gap_date).sum()), len(buys)

    ungated_gap, ungated_all = buys_on_gap_day(HighFrequencyLocalReferenceSizing)
    gated_gap, gated_all = buys_on_gap_day(
        GatedLocalReferenceSizing, {"breakdown_gate": "prior_low", "breakdown_release": "session"}
    )
    assert ungated_gap > 0, "the champion must buy on the gap day, or this proves nothing"
    assert gated_gap == 0
    assert 0 < gated_all < ungated_all


@pytest.mark.parametrize("fill_model", FILL_MODELS)
def test_gated_runs_are_deterministic(fill_model):
    df = _minute_sessions(gap_day=4)
    extra = {
        "breakdown_gate": "dual_thrust",
        "dt_lookback_days": 2,
        "pattern_gate": "shooting_star",
    }
    a = _run(df, GatedLocalReferenceSizing, fill_model, extra).iloc[0]
    b = _run(df, GatedLocalReferenceSizing, fill_model, extra).iloc[0]
    for column in OUTCOMES:
        assert a[column] == b[column], column


# --------------------------------------------------------------------
# 3. No new way to lose money


def test_no_exit_hook_is_overridden_here():
    """A gate governs new exposure only. lots_to_liquidate -- the one
    hook that may realize a loss -- must be the base no-op, and the
    retargeting hooks must be the champion's own."""
    assert GatedLocalReferenceSizing.lots_to_liquidate is SizingStrategy.lots_to_liquidate
    for hook in ("adjust_profit_target", "retain_lots", "wants_lot_retargeting"):
        assert getattr(GatedLocalReferenceSizing, hook) is getattr(
            HighFrequencyLocalReferenceSizing, hook
        ), hook


# --------------------------------------------------------------------
# Construction and wiring


def test_a_disabled_gate_is_still_validated():
    with pytest.raises(ConfigurationError):
        GatedLocalReferenceSizing(**HF_PARAMS, breakdown_gate="off", dt_k=-1.0)
    with pytest.raises(ConfigurationError):
        GatedLocalReferenceSizing(**HF_PARAMS, pattern_gate="hammer")


def test_registered_and_constructible_from_the_committed_defaults():
    from server.backtest import STRATEGY_DEFAULTS

    assert resolve_strategy("hf_entry_gated") is GatedLocalReferenceSizing
    assert STRATEGY_DEFAULTS["hf_entry_gated"] == STRATEGY_DEFAULTS["hf_local_reference"]
    strategy = GatedLocalReferenceSizing(**STRATEGY_DEFAULTS["hf_entry_gated"])
    assert strategy.diagnostics()["entry_suppressed"] is False


def test_the_server_enums_match_the_guards():
    """The run form's dropdowns and the constructor's guards are two
    lists of the same thing; one changing without the other is drift."""
    from server.backtest import _PARAM_ENUMS

    assert _PARAM_ENUMS["breakdown_gate"] == list(entry_gates.BREAKDOWN_MODES)
    assert _PARAM_ENUMS["breakdown_release"] == list(entry_gates.RELEASE_MODES)
    assert _PARAM_ENUMS["pattern_gate"] == list(entry_gates.PATTERN_MODES)


def test_class_names_resolve_uniquely_for_analyze_annual():
    """analyze_annual maps a row's Strategy column (the class __name__)
    back to a class. Two DIFFERENT classes sharing a name would make
    that ambiguous."""
    by_name: dict[str, set[type]] = {}
    for cls in STRATEGIES.values():
        by_name.setdefault(cls.__name__, set()).add(cls)
    assert all(len(classes) == 1 for classes in by_name.values())
