"""Proves a downloaded CSV is actually consumable by a real sweep.

Every other test in the downloader's suite checks one transform step.
This one checks the thing that matters: that the file the downloader
writes survives the exact path cli.py's `backtest` takes to load it,
passes validation, and drives a real OptimizationController sweep to
completion.

The trap it guards is specific. data_validation.REQUIRED_COLUMNS is
only {"close"}, but optimization_controller._simulate_single reads
row.open/high/low/close through itertuples. A CSV missing OHLC
therefore passes validation cleanly and then dies with an
AttributeError partway through a sweep -- long after the download
looked successful.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from alpaca.data.models import BarSet

from optimization_controller import OptimizationController
from src import data_validation
from src.historical_data import to_backtest_frame, write_csv
from src.size_calculators import FixedPortfolioPercentage


def synthetic_session_bars(minutes: int = 360, seed: int = 7):
    """A realistic intraday session in Alpaca's wire shape.

    Random-walked rather than flat so the grid actually triggers --
    a constant price would make the sweep trivially trade nothing and
    the test would pass without exercising anything.
    """
    rng = np.random.default_rng(seed)
    price = 70.0
    rows = []
    ts = pd.Timestamp("2026-03-02 09:30", tz="America/New_York")
    for _ in range(minutes):
        price *= 1.0 + rng.normal(0, 0.0012)
        high = price * (1 + abs(rng.normal(0, 0.0004)))
        low = price * (1 - abs(rng.normal(0, 0.0004)))
        rows.append(
            {
                "t": ts.tz_convert("UTC").isoformat(),
                "o": round(price, 4),
                "h": round(max(high, price), 4),
                "l": round(min(low, price), 4),
                "c": round(price, 4),
                "v": int(rng.integers(1000, 50_000)),
                "n": 10,
                "vw": round(price, 4),
            }
        )
        ts += pd.Timedelta(minutes=1)
    return rows


@pytest.fixture
def written_csv(tmp_path):
    df, _, _ = to_backtest_frame(BarSet(raw_data={"TQQQ": synthetic_session_bars()}).df, "TQQQ")
    return write_csv(df, tmp_path / "TQQQ_1Min.csv")


def load_like_cli(path):
    """Byte-for-byte the load cli.py:cmd_backtest performs."""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_a_written_csv_reloads_through_the_real_cli_path(written_csv):
    df = load_like_cli(written_csv)
    assert not df.empty
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.is_monotonic_increasing
    assert not df.index.duplicated().any()


def test_a_written_csv_passes_data_validation(written_csv):
    data_validation.validate(load_like_cli(written_csv))


def test_ohlc_survive_the_round_trip_as_itertuples_attributes(written_csv):
    """The specific failure this whole test file exists for: validation
    only requires 'close', but the sweep reads all four."""
    df = load_like_cli(written_csv)
    row = next(df.itertuples())
    for field in ("open", "high", "low", "close"):
        assert hasattr(row, field), f"_simulate_single would AttributeError on row.{field}"


def test_volume_reloads_as_an_integer(written_csv):
    assert pd.api.types.is_integer_dtype(load_like_cli(written_csv)["volume"])


def test_timestamps_reload_as_utc_aware(written_csv):
    df = load_like_cli(written_csv)
    assert df.index.tz is not None, "naive timestamps would misalign against Alpaca's UTC bars"


def test_a_real_sweep_runs_to_completion_on_the_downloaded_file(written_csv):
    """End-to-end proof. If this passes, a downloaded file is usable."""
    controller = OptimizationController(historical_data=load_like_cli(written_csv))
    results = controller.run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.001],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert len(results) == 1
    assert "Capital Velocity Index" in results.columns


def test_the_downloaded_shape_matches_the_committed_fixture(written_csv):
    """Guards against drift between what the downloader emits and the
    one committed example of this format."""
    fixture = pd.read_csv(
        "tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]
    ).set_index("timestamp")
    downloaded = load_like_cli(written_csv)
    assert list(downloaded.columns) == list(fixture.columns)
    assert downloaded.index.name == fixture.index.name
