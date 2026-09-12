"""cli.py's `_apply_backtest_window`: BacktestConfig.backtest.start_date/
end_date actually filtering the DataFrame `cmd_backtest`/`cmd_search`
hand to OptimizationController.

FOUND BY RUNNING A REAL SWEEP, NOT BY READING THE SCHEMA. `start_date`/
`end_date` round-trip through BacktestConfig.from_dict/to_dict
(src/core/config.py) but, before this module existed, nothing in the
CLI path read them back -- config/search_soxl_regime_bayesian.yaml's
`start_date: "2024-01-01"` silently searched all 10.6 years of history.
The tell was every threshold candidate in an 80-trial sweep producing
IDENTICAL trade counts: the search was running over the whole file
regardless of what any trial's parameters were, which is what a config
field being silently inert looks like from the outside.

Imported directly from `cli.py` rather than driven through a subprocess
-- this is a small pure function, and tests/CLAUDE.md's subprocess rule
is for exit codes and argument parsing, not for business logic that
happens to live in this module. See test_historical_data_roundtrip.py's
own `load_like_cli` for the sibling case (a helper too small to be
worth invoking a subprocess for, replicated/imported rather than
shelled out to).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cli import _apply_backtest_window, _to_utc_timestamp


@dataclass
class _FakeBacktest:
    start_date: str | None = None
    end_date: str | None = None


@dataclass
class _FakeConfig:
    backtest: _FakeBacktest


def make_df(dates: list[str]) -> pd.DataFrame:
    index = pd.DatetimeIndex([pd.Timestamp(d, tz="UTC") for d in dates])
    return pd.DataFrame({"close": range(len(dates))}, index=index)


DATES = ["2023-06-01", "2023-12-31", "2024-01-01", "2024-06-15", "2024-12-31", "2025-01-01"]


def test_neither_bound_set_is_a_no_op():
    df = make_df(DATES)
    out = _apply_backtest_window(df, _FakeConfig(_FakeBacktest()))
    assert len(out) == len(df)
    pd.testing.assert_frame_equal(out, df)


def test_start_date_excludes_everything_before_it():
    df = make_df(DATES)
    out = _apply_backtest_window(df, _FakeConfig(_FakeBacktest(start_date="2024-01-01")))
    assert list(out.index.strftime("%Y-%m-%d")) == [
        "2024-01-01",
        "2024-06-15",
        "2024-12-31",
        "2025-01-01",
    ]


def test_end_date_includes_the_whole_day_it_names():
    """The exact bug class start_date/end_date exists to prevent: an end
    bound sliced on the bare midnight timestamp would drop every bar
    from the day itself, since a 14:30 UTC bar is not < 00:00 UTC that
    same day."""
    df = make_df(["2024-12-31", "2024-12-31T23:59:00", "2025-01-01"])
    out = _apply_backtest_window(df, _FakeConfig(_FakeBacktest(end_date="2024-12-31")))
    assert len(out) == 2
    assert "2025-01-01" not in out.index.strftime("%Y-%m-%d").tolist()


def test_both_bounds_together():
    df = make_df(DATES)
    out = _apply_backtest_window(
        df, _FakeConfig(_FakeBacktest(start_date="2024-01-01", end_date="2024-06-15"))
    )
    assert list(out.index.strftime("%Y-%m-%d")) == ["2024-01-01", "2024-06-15"]


def test_a_window_with_no_bars_in_it_returns_empty_not_an_error():
    df = make_df(DATES)
    out = _apply_backtest_window(df, _FakeConfig(_FakeBacktest(start_date="2030-01-01")))
    assert out.empty


class TestToUtcTimestamp:
    def test_naive_date_localizes_to_utc(self):
        ts = _to_utc_timestamp("2024-01-01")
        assert ts.tzinfo is not None
        assert str(ts.tz) == "UTC"

    def test_an_already_aware_value_converts_rather_than_erroring(self):
        ts = _to_utc_timestamp("2024-01-01T00:00:00-05:00")
        assert str(ts.tz) == "UTC"
        assert ts.hour == 5  # -05:00 -> UTC


class TestCliBacktestConfigsActuallyHonorTheWindow:
    """The regression this whole module guards: a real BacktestConfig
    parsed from YAML, not a fake, must produce a filtered frame -- not
    just the hand-rolled dataclass above."""

    def test_real_backtest_config_start_date_filters(self):
        from src.core.config import BacktestConfig

        raw = {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.03]},
            "backtest": {"symbol": "TEST", "start_date": "2024-01-01"},
        }
        config = BacktestConfig.from_dict(raw)
        df = make_df(DATES)
        out = _apply_backtest_window(df, config)
        assert list(out.index.strftime("%Y-%m-%d")) == [
            "2024-01-01",
            "2024-06-15",
            "2024-12-31",
            "2025-01-01",
        ]
