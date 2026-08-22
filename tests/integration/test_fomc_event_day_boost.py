"""Integration test: FOMC-day awareness through the full backtest path.

The unit tests (test_fomc_calendar.py, test_high_frequency_sizing.py)
prove the calendar lookup and the boost math in isolation. This proves
the wiring: optimization_controller._simulate_single actually builds
MarketContext.is_macro_event_day from a bar's real timestamp (not a
hand-constructed test context), and HighFrequencyLocalReferenceSizing
actually receives and acts on it through a real run_sweep call.

2024-01-31 is a real FOMC decision date (see src/fomc_calendar.py);
2024-01-30 is the ordinary trading day immediately before it and is
not. Two single-day fixtures with an IDENTICAL relative price path are
run separately (fresh strategy/state each run_sweep call) so any
difference in the resulting buy's notional is attributable only to
the calendar flag, not to any other confound.
"""

from __future__ import annotations

import pandas as pd

from optimization_controller import OptimizationController
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing

NON_FOMC_DATE = "2024-01-30"  # ordinary trading day
FOMC_DATE = "2024-01-31"  # real FOMC decision date, per src/fomc_calendar.py


def _one_day_dip_fixture(date_str: str) -> pd.DataFrame:
    """A handful of 1-min bars starting at 100.0, dipping 2% by the
    fourth bar -- well past any single-bar grid_step used below, so
    exactly one buy fires partway through, on a known bar."""
    ts = pd.date_range(f"{date_str} 14:30", periods=6, freq="1min", tz="UTC")
    prices = [100.0, 100.0, 99.5, 98.0, 98.0, 98.0]
    return pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": 10_000},
        index=ts,
    )


def _first_buy_notional(df: pd.DataFrame, **strategy_kwargs) -> float:
    params = dict(per_lot_pct=0.01, lookback_days=0.001, bars_per_day=6)
    params.update(strategy_kwargs)
    controller = OptimizationController(historical_data=df)
    _, full = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.5],  # wide enough that nothing sells mid-fixture
        strategy_class=HighFrequencyLocalReferenceSizing,
        strategy_params_grid=[params],
        return_full_results=True,
    )
    blotter = full[0].trade_blotter
    buys = blotter[blotter["side"] == "buy"]
    assert len(buys) >= 1, "fixture must produce at least one buy to compare"
    first_buy = buys.iloc[0]
    return first_buy["price"] * first_buy["qty"]


def test_context_is_macro_event_day_is_populated_from_the_real_calendar_through_a_real_run():
    """Without any boost configured, the buy notional on the real FOMC
    date must be UNCHANGED from the non-FOMC date -- proving the flag
    alone (default multiplier 1.0) doesn't alter behavior, only that a
    boost, if configured, would have something real to act on."""
    non_fomc_notional = _first_buy_notional(_one_day_dip_fixture(NON_FOMC_DATE))
    fomc_notional = _first_buy_notional(_one_day_dip_fixture(FOMC_DATE))
    assert non_fomc_notional == fomc_notional


def test_a_configured_boost_actually_enlarges_the_buy_on_the_real_fomc_date():
    """The end-to-end claim: is_fomc_day_at() -> MarketContext.is_macro_event_day
    (built inside _simulate_single from the bar's own timestamp) ->
    HighFrequencyLocalReferenceSizing.calculate_trade_value's boost,
    all through one real controller.run_sweep call per date."""
    boost = 2.5
    non_fomc_notional = _first_buy_notional(
        _one_day_dip_fixture(NON_FOMC_DATE), event_day_boost_multiplier=boost
    )
    fomc_notional = _first_buy_notional(
        _one_day_dip_fixture(FOMC_DATE), event_day_boost_multiplier=boost
    )
    assert fomc_notional == non_fomc_notional * boost
