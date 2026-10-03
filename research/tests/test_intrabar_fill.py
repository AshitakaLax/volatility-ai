"""execution.intrabar_fill: "level" (default, unchanged) vs "open_or_level".

The claim being pinned: under "open_or_level" every booked fill is a
price the bar traded. A resting buy at L fills at the open when the bar
opens at or below L; a resting sell at T fills at the open when the bar
opens at or above T; otherwise both fill at their order price, exactly
as "level" does. And "level" must reproduce today's results exactly,
since every recorded intrabar sweep was booked that way.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.optimization.optimization_controller import OptimizationController
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.size_calculators import FixedPortfolioPercentage
from research.tests.test_gated_local_reference_sizing import HF_PARAMS, OUTCOMES, _minute_sessions


def _bars(start: str, prices) -> pd.DataFrame:
    prices = np.asarray(prices, dtype=float)
    opens = np.r_[prices[0], prices[:-1]]
    index = pd.date_range(start, periods=len(prices), freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "open": opens,
            "high": np.maximum(opens, prices) + 0.02,
            "low": np.minimum(opens, prices) - 0.02,
            "close": prices,
            "volume": 1e4,
        },
        index=index,
    )


def _gap_down() -> pd.DataFrame:
    """A calm session near 100, then one that opens 5% lower."""
    day1 = _bars("2024-01-02 14:30", 100 + 0.3 * np.sin(np.arange(120) / 3))
    day2 = _bars("2024-01-03 14:30", 95 + 0.05 * np.sin(np.arange(120) / 3))
    day2.iloc[0, day2.columns.get_loc("open")] = 95.0  # the gap itself
    return pd.concat([day1, day2])


def _run(
    df,
    intrabar_fill=None,
    fill_model="intrabar",
    cls=HighFrequencyLocalReferenceSizing,
    params=None,
    step=0.00075,
    target=0.3,
    full=False,
):
    kwargs = {} if intrabar_fill is None else {"intrabar_fill": intrabar_fill}
    out = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[dict(params or HF_PARAMS)],
        fill_model=fill_model,
        return_full_results=full,
        **kwargs,
    )
    return out if full else out.iloc[0]


def _out_of_range(df, blotter) -> tuple[int, int]:
    """(buys booked above their bar's high, sells booked below its low)."""
    stamps = pd.to_datetime(blotter["timestamp"], utc=True)
    high = df["high"].reindex(stamps).to_numpy()
    low = df["low"].reindex(stamps).to_numpy()
    price = blotter["price"].to_numpy()
    buy = (blotter["side"] == "buy").to_numpy()
    return int((buy & (price > high + 1e-9)).sum()), int((~buy & (price < low - 1e-9)).sum())


# --------------------------------------------------------------------
# "level" is today's behaviour, exactly


@pytest.mark.parametrize("data", ["minutes", "gap"])
def test_omitted_and_level_are_identical(data):
    df = _minute_sessions(gap_day=4) if data == "minutes" else _gap_down()
    omitted, level = _run(df), _run(df, "level")
    assert omitted["Trade Count"] > 0
    for column in OUTCOMES:
        assert omitted[column] == level[column], column
    assert level["intrabar_fill"] == "level"


def test_the_close_model_ignores_the_flag():
    df = _gap_down()
    a, b = _run(df, "level", "close"), _run(df, "open_or_level", "close")
    for column in OUTCOMES:
        assert a[column] == b[column], column


# --------------------------------------------------------------------
# "open_or_level" books only prices the bar traded


def test_level_books_buys_above_the_bar_and_open_or_level_does_not():
    """The discriminating case: the same run, two bookings. If "level"
    stopped producing out-of-range buys this test would no longer prove
    the fix does anything, so that half is asserted too."""
    df = _gap_down()
    _, level = _run(df, "level", full=True)
    _, fixed = _run(df, "open_or_level", full=True)
    assert _out_of_range(df, level[0].trade_blotter)[0] > 0
    assert _out_of_range(df, fixed[0].trade_blotter) == (0, 0)


def test_a_gap_down_buy_fills_at_the_open():
    df = _gap_down()
    _, full = _run(df, "open_or_level", full=True)
    buys = full[0].trade_blotter[lambda b: b["side"] == "buy"]
    first_on_day2 = buys[pd.to_datetime(buys["timestamp"], utc=True).dt.day == 3].iloc[0]
    assert first_on_day2["price"] == pytest.approx(95.0)


def test_a_gap_up_sell_fills_at_the_open():
    """Buy on a dip, then the next bar opens far above the target."""
    df = _bars("2024-01-02 14:30", [100.0, 100.0, 99.0, 99.0, 99.0])
    df.loc[df.index[3], ["open", "high", "low", "close"]] = [105.0, 105.5, 104.5, 105.0]
    df.loc[df.index[4], ["open", "high", "low", "close"]] = [105.0, 105.2, 104.8, 105.0]
    common = dict(
        cls=FixedPortfolioPercentage,
        params={"allocation_pct": 0.05},
        step=0.005,
        target=0.01,
        full=True,
    )
    _, level = _run(df, "level", **common)
    _, fixed = _run(df, "open_or_level", **common)
    sells = {
        name: r[0].trade_blotter[lambda b: b["side"] == "sell"].iloc[0]["price"]
        for name, r in (("level", level), ("fixed", fixed))
    }
    assert sells["fixed"] == pytest.approx(105.0)  # the open
    assert sells["level"] < 104.5  # the target: below anything that bar traded


def test_bars_that_open_inside_the_order_book_identically():
    """Wicks pierce the levels but every bar OPENS between them: both
    bookings must agree to the last cent."""
    n = 40
    index = pd.date_range("2024-01-02 14:30", periods=n, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1e4}, index=index
    )
    # Two buys (99.5, then 99.0025) whose 1.2% targets (100.694, 100.19)
    # both sit ABOVE the 100.0 open and below the 101 wick. A smaller
    # target would put a target below the open -- a bar opening through
    # the order, which is exactly the case where the two modes differ.
    common = dict(
        cls=FixedPortfolioPercentage, params={"allocation_pct": 0.05}, step=0.005, target=0.012
    )
    a, b = _run(df, "level", **common), _run(df, "open_or_level", **common)
    assert a["Trade Count"] > 0
    for column in OUTCOMES:
        assert a[column] == b[column], column


# --------------------------------------------------------------------
# Config plumbing


def test_yaml_round_trip_and_validation(tmp_path):
    base = Path("config/best_known_2026-08-24.yaml").read_text()
    path = tmp_path / "c.yaml"
    path.write_text(
        base.replace(
            "enforce_no_loss: true}", "enforce_no_loss: true, intrabar_fill: open_or_level}"
        )
    )
    cfg = BacktestConfig.from_yaml(str(path))
    cfg.validate()
    assert cfg.execution.intrabar_fill == "open_or_level"
    assert (
        cfg.to_run_sweep_kwargs(HighFrequencyLocalReferenceSizing)["intrabar_fill"]
        == "open_or_level"
    )

    default = BacktestConfig.from_yaml("config/best_known_2026-08-24.yaml")
    assert default.execution.intrabar_fill == "level"

    path.write_text(
        base.replace("enforce_no_loss: true}", "enforce_no_loss: true, intrabar_fill: open}")
    )
    with pytest.raises(ConfigurationError):
        BacktestConfig.from_yaml(str(path)).validate()


def test_run_sweep_rejects_an_unknown_mode():
    with pytest.raises(ConfigurationError):
        _run(_gap_down(), "midpoint")
