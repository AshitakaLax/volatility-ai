"""Tests for cash_yield_pct in OptimizationController (money-market
idle-cash accrual -- see ExecutionConfig.cash_yield_pct in
engine/core/config.py for the full rationale).

The claim being pinned: cash NOT tied up in an open lot compounds daily
at the configured annual rate, and this changes nothing about WHICH
trades fire -- only the cash balance sitting idle between them. A test
fixture that could not tell the difference between "yield changed the
final number" and "yield changed a trading decision" would not actually
prove the isolation this feature depends on.

Also pins the invariant that matters most: omitting cash_yield_pct (or
run_sweep()'s own bare default) is unchanged. tests/fixtures/
regression_baseline.py already guards that globally; the test here
states it locally for this parameter, mirroring
test_intrabar_fill_model.py's test_close_model_is_the_unchanged_default.
"""

from __future__ import annotations

import pandas as pd
import pytest

from research.optimization.optimization_controller import OptimizationController
from research.strategies.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE, load_fixture_data

GRID_STEP = BASELINE["Grid Step"]
PROFIT_TARGET = BASELINE["Profit Target"]
STRATEGY_PARAMS = {"allocation_pct": BASELINE["allocation_pct"]}


def _flat_price_fixture(days: int) -> pd.DataFrame:
    """A price series that never moves, so the grid never triggers a
    single buy -- every dollar of initial_cash stays idle for the whole
    run, which is what makes the exact closed-form comparison in
    test_idle_cash_compounds_at_the_configured_rate possible.
    """
    ts = pd.date_range("2024-01-01", periods=days * 24 * 60, freq="1min", tz="UTC")
    close = [100.0] * len(ts)
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": [1_000] * len(ts)},
        index=ts,
    )


def _run(df: pd.DataFrame, **kw):
    controller = OptimizationController(historical_data=df)
    return controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[STRATEGY_PARAMS],
        **kw,
    ).iloc[0]


def test_omitting_cash_yield_pct_reproduces_the_baseline():
    """No cash_yield_pct argument at all must still match the pinned
    baseline exactly -- run_sweep()'s own default parameter is 0.0."""
    row = _run(load_fixture_data())
    assert row["cash_yield_pct"] == 0.0
    assert row["Final Equity"] == pytest.approx(BASELINE["Final Equity"], abs=1e-6)


def test_explicit_zero_matches_omitted():
    """Stating 0.0 explicitly must be indistinguishable from leaving it
    out -- the guard in _simulate_single's per-bar loop is `if
    cash_yield_pct`, not `if cash_yield_pct is not None`."""
    row = _run(load_fixture_data(), cash_yield_pct=0.0)
    assert row["Final Equity"] == pytest.approx(BASELINE["Final Equity"], abs=1e-6)


def test_idle_cash_compounds_at_the_configured_rate():
    """A fixture engineered so NOTHING ever trades: every dollar of
    initial_cash is idle cash for the run's entire span, so the final
    equity must match the closed-form daily-compounding formula exactly
    -- not approximately, since there is no trading noise to blur it."""
    days = 30
    rate = 0.05
    df = _flat_price_fixture(days)
    row = _run(df, cash_yield_pct=rate)

    assert row["Trade Count"] == 0, "fixture must never trigger a trade, or this proves nothing"
    daily_rate = (1.0 + rate) ** (1.0 / 365.0) - 1.0
    expected = 100_000.0 * (1.0 + daily_rate) ** days
    assert row["Final Equity"] == pytest.approx(expected, rel=1e-9)
    assert row["Final Equity"] > 100_000.0


def test_zero_rate_on_the_flat_fixture_earns_nothing():
    """Same untraded fixture, rate off: equity must not move at all --
    isolates that the gain above comes from the rate, not from the
    fixture somehow trading anyway."""
    df = _flat_price_fixture(30)
    row = _run(df, cash_yield_pct=0.0)
    assert row["Trade Count"] == 0
    assert row["Final Equity"] == pytest.approx(100_000.0, abs=1e-9)


def _write_effr_fixture(tmp_path, monkeypatch, rows: list[tuple[str, float]]) -> None:
    """Point research.ml.sources.default_directory at tmp_path and drop
    a synthetic fred_EFFR.csv there, in fetch_fred's own output shape
    (timestamp,close, percentage points) -- so
    OptimizationController._smart_cash_yield_series loads exactly this
    instead of whatever is really on disk, making the test deterministic
    regardless of when data/external/ was last refreshed."""
    import research.ml.sources as sources_module

    frame = pd.DataFrame({"timestamp": [r[0] for r in rows], "close": [r[1] for r in rows]})
    frame.to_csv(tmp_path / "fred_EFFR.csv", index=False)
    monkeypatch.setattr(sources_module, "default_directory", lambda: tmp_path)


def test_smart_mode_varies_with_the_injected_history(monkeypatch, tmp_path):
    """cash_yield_pct=None (smart) on a fixture spanning a LOW-rate era
    then a HIGH-rate era must land strictly between what a flat run at
    each fixed rate would produce -- a single flat number, smart or
    not, could not do this."""
    days = 60
    df = _flat_price_fixture(days)
    # The fixture runs 2024-01-01 through ~2024-03-01: the first
    # observation covers days 1-15 (as-of, nothing later exists yet),
    # the second covers day 16 onward -- a genuine low-then-high mix
    # inside one run, not two separately-run fixed rates.
    _write_effr_fixture(tmp_path, monkeypatch, [("2023-01-01", 0.50), ("2024-01-16", 6.00)])

    from research.optimization.money_market_yield import SPAXX_EXPENSE_RATIO_PCT

    smart_row = _run(df, cash_yield_pct=None)
    low_row = _run(df, cash_yield_pct=(0.50 - SPAXX_EXPENSE_RATIO_PCT) / 100)
    high_row = _run(df, cash_yield_pct=(6.00 - SPAXX_EXPENSE_RATIO_PCT) / 100)

    assert low_row["Final Equity"] < smart_row["Final Equity"] < high_row["Final Equity"]


def test_smart_mode_falls_back_to_the_floor_when_the_file_is_missing(monkeypatch, tmp_path):
    """No fred_EFFR.csv on disk at all -- a Pi, a shard, a fresh clone --
    must not crash the sweep, and must match an explicit fixed run at
    exactly FLOOR_PCT."""
    import research.ml.sources as sources_module
    from research.optimization.money_market_yield import FLOOR_PCT

    monkeypatch.setattr(sources_module, "default_directory", lambda: tmp_path)  # empty dir

    df = _flat_price_fixture(10)
    smart_row = _run(df, cash_yield_pct=None)
    floor_row = _run(df, cash_yield_pct=FLOOR_PCT / 100)
    assert smart_row["Final Equity"] == pytest.approx(floor_row["Final Equity"], rel=1e-9)
    assert smart_row["Final Equity"] > 100_000.0, "the floor is a positive rate, not zero"


def test_yield_does_not_change_which_trades_fire():
    """Real trades, on the pinned fixture: whether a trigger fires, and
    which side of it wins, must agree whether idle cash earns yield or
    not -- the grid trigger compares PRICE against last_buy_price, never
    equity, so trade count and win/loss classification are invariant.

    Dollar-denominated columns (Realized PnL, Max Drawdown %) are
    DELIBERATELY not compared here: FixedPortfolioPercentage sizes a lot
    as allocation_pct * current EQUITY, so once idle cash earns
    something, equity is very slightly higher at every buy and the next
    lot is very slightly bigger -- a real and correct consequence of
    modelling the cash, not a leak into trigger logic. Trade Count is
    the invariant that actually isolates "did yield change a decision".
    """
    df = load_fixture_data()
    row_a = _run(df, cash_yield_pct=0.0)
    row_b = _run(df, cash_yield_pct=0.05)
    for key in ("Trade Count", "Closed Trade Count", "Open Trade Count", "Win Rate %"):
        assert row_a[key] == pytest.approx(row_b[key], rel=1e-9, abs=1e-9), key

    # And the whole point of the feature: equity DOES differ once idle
    # cash exists to earn something on.
    assert row_b["Final Equity"] > row_a["Final Equity"]
