"""--lag on the stage harnesses: lag 1 must make IndicatorRegime apply the
PREVIOUS session's flag at each open; lag 0 reproduces the same-session
reading plan.md's engine stages were measured with."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.natr_regime import apply_lag, shift_to_next_session
from tools.probe_stage3_engine import IndicatorRegime

DAYS = [datetime(2024, 1, 2, 14, 30, tzinfo=UTC) + timedelta(days=i) for i in range(5)]
# Alternates every session, so a same-session read and a prior-session
# read can never agree after the first day.
FLAGS = {d.date(): i % 2 == 0 for i, d in enumerate(DAYS)}


def _regime_at_each_open(regime_by_date) -> dict:
    params = dict(
        yaml.safe_load(Path("config/paper_aggressive.yaml").read_text())["strategy"][
            "strategy_params"
        ]
    )
    params.update(
        per_lot_pct=0.002,
        bull_step=0.00075,
        bear_step=0.10,
        max_mult=400.0,
        dd_ref=0.75,
        regime_days=200,
        daily_signal=True,
        stand_aside_until_warm=True,
    )
    s = IndicatorRegime(regime_by_date=regime_by_date, **params)
    seen = {}
    for day in DAYS:
        for minute in range(3):
            ts = day + timedelta(minutes=minute)
            s.record_tick(
                MarketContext(
                    timestamp=ts,
                    open=50,
                    high=50.1,
                    low=49.9,
                    close=50,
                    cash=1e5,
                    equity=1e5,
                    peak_equity=1e5,
                    drawdown=0.0,
                    open_lot_count=0,
                    bar_index=0,
                )
            )
            if minute == 0:
                seen[day.date()] = s._is_bull
    return seen


def test_lag0_applies_each_flag_on_its_own_session():
    seen = _regime_at_each_open(apply_lag(FLAGS, 0))
    for day in DAYS[1:]:
        assert seen[day.date()] == FLAGS[day.date()]


def test_lag1_applies_the_previous_sessions_flag():
    seen = _regime_at_each_open(apply_lag(FLAGS, 1))
    for prev, day in itertools.pairwise(DAYS):
        assert seen[day.date()] == FLAGS[prev.date()]


def test_shift_drops_the_last_flag_and_keys_by_the_next_session():
    shifted = shift_to_next_session(FLAGS)
    assert sorted(shifted) == [d.date() for d in DAYS[1:]]


def test_only_lag_0_or_1():
    with pytest.raises(ConfigurationError):
        apply_lag(FLAGS, 2)
