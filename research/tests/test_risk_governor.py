"""The risk governor (research/strategies/risk_governor.py) and its switch
on Daily Ultimate: each warning is raised by its rule and by nothing a
session could not have read; a consensus pauses, stale data abstains, a
missing input refuses; and the pause stops calm buying for the session
without touching the regime or the book."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from engine.core.trading_calendar import next_session, sessions_between
from research.strategies import param_schema
from research.strategies.daily_ultimate_sizing import DailyUltimateSizing
from research.strategies.gated_local_reference_sizing import NO_BUY_LEVEL
from research.strategies.risk_governor import (
    CORE_MIN_VOTES,
    CORE_SIGNALS,
    EXTERNAL_DIR_ENV,
    SESSION_CUTOFF_UTC,
    SIGNALS,
    RiskGovernor,
    external_directory,
    parse_signals,
)
from research.strategies.strategy_registry import resolve_strategy
from research.strategies.ultimate_sizing import CALM

FIRST, LAST = date(2023, 1, 3), date(2024, 6, 28)
SESSIONS = sessions_between(FIRST - timedelta(days=1), LAST)
CORE_INPUTS = sorted({key for name in CORE_SIGNALS for key in SIGNALS[name].inputs})


def stamped(values, sessions=SESSIONS, lag_days: int = 0) -> pd.Series:
    """A daily series stamped at each session's close (21:00 UTC), as
    research/ml/sources.py stamps a same-day source."""
    index = pd.DatetimeIndex(pd.to_datetime(sessions)).tz_localize("UTC") + pd.Timedelta(
        days=lag_days, hours=21
    )
    return pd.Series(np.asarray(values, dtype=float), index=index)


def flat(level: float = 100.0) -> pd.Series:
    return stamped(np.full(len(SESSIONS), level))


def stepped(before: float, after: float, at: date) -> pd.Series:
    return stamped([after if day >= at else before for day in SESSIONS])


def calm_world() -> dict[str, pd.Series]:
    """Every core input flat: no warning is ever raised."""
    return {key: flat() for key in CORE_INPUTS}


STEP = date(2024, 3, 4)
# Each core warning, raised from the session after STEP's close.
RAISED = {
    "vxn_hi": {"cboe_VXN": stepped(20, 40, STEP)},
    "sox_weak": {"yahoo_SOX": stepped(100, 80, STEP)},
    "credit": {"yahoo_HYG": stepped(100, 90, STEP)},
    "trend100": {"yahoo_QQQ": stepped(100, 85, STEP)},
    "fsi_rising": {"ofr_FSI": stepped(-1.0, 1.0, STEP)},
}


def world(*names: str) -> dict[str, pd.Series]:
    series = calm_world()
    for name in names:
        series.update(RAISED[name])
    return series


# -- the signals -----------------------------------------------------------------


@pytest.mark.parametrize("name", CORE_SIGNALS)
def test_each_core_warning_is_raised_by_its_own_input_and_only_after_it_was_readable(name):
    governor = RiskGovernor(world(name), min_votes=1)
    after = next_session(STEP)
    # STEP's value is stamped at STEP's close: STEP itself cannot have read it.
    assert governor.reading(STEP).raised == ()
    assert governor.reading(after).raised == (name,)
    assert governor.reading(after).paused


def test_a_value_is_read_only_from_the_session_after_its_stamp():
    series = world("trend100")
    governor = RiskGovernor(series, signals=("trend100",), min_votes=1)
    table = governor.table(LAST)
    first_raised = table.index[table["trend100"] == 1.0][0].date()
    assert first_raised == next_session(STEP)
    # The cutoff is the session's own date at SESSION_CUTOFF_UTC, before
    # that day's 21:00 stamp and after the previous day's.
    assert 0 <= SESSION_CUTOFF_UTC < 21


def test_nothing_before_a_session_changes_when_later_data_arrives():
    """No lookahead: the readings up to a day are the same whether or not
    the series run on past it."""
    full = world(*CORE_SIGNALS)
    cut = pd.Timestamp(STEP + timedelta(days=30), tz="UTC")
    early = {key: s[s.index <= cut] for key, s in full.items()}
    through = (cut - pd.Timedelta(days=1)).date()
    a = RiskGovernor(full).table(LAST).loc[: pd.Timestamp(through)]
    b = RiskGovernor(early).table(through)
    pd.testing.assert_frame_equal(a, b)


def test_a_lagged_stamp_delays_the_warning_by_its_lag():
    late = world()
    late["ofr_FSI"] = stamped(
        [1.0 if day >= STEP else -1.0 for day in SESSIONS], lag_days=4
    )
    governor = RiskGovernor(late, signals=("fsi_rising",), min_votes=1)
    table = governor.table(LAST)
    first = table.index[table["fsi_rising"] == 1.0][0].date()
    assert first > next_session(STEP)
    assert first == next(d for d in SESSIONS if d > STEP + timedelta(days=4))


def test_a_warning_has_no_vote_until_its_window_has_filled():
    governor = RiskGovernor(world("trend100"), signals=("trend100",), min_votes=1)
    # The first value is readable on the session after the data's first.
    table = governor.table(LAST).loc[pd.Timestamp(next_session(FIRST)) :]
    assert table["trend100"].iloc[:99].isna().all()
    assert table["trend100"].iloc[99:].notna().all()
    assert not table["paused"].iloc[:99].any()
    assert governor.table(LAST)["known"].loc[: pd.Timestamp(FIRST)].eq(0).all()


def test_every_signal_names_inputs_a_registered_source_writes():
    from research.ml.sources import manifest_key, registry

    written = {manifest_key(source) for source in registry()}
    for signal in SIGNALS.values():
        assert set(signal.inputs) <= written, signal.name
    assert set(CORE_SIGNALS) <= set(SIGNALS) and 1 <= CORE_MIN_VOTES <= len(CORE_SIGNALS)


# -- the vote --------------------------------------------------------------------


def test_the_pause_needs_the_consensus():
    after = next_session(STEP)
    three = RiskGovernor(world("vxn_hi", "sox_weak", "credit"))
    assert three.reading(after).votes == 3 and not three.paused(after)
    four = RiskGovernor(world("vxn_hi", "sox_weak", "credit", "trend100"))
    reading = four.reading(after)
    assert reading.votes == 4 and reading.known == 5 and reading.paused
    assert four.paused_by_date(through=LAST).get(after) is True
    assert STEP not in four.paused_by_date(through=LAST)


def until(series: dict[str, pd.Series], last: date) -> dict[str, pd.Series]:
    """`series` as a feed that stopped after `last`'s close."""
    end = pd.Timestamp(last, tz="UTC") + pd.Timedelta(hours=21)
    return {key: s[s.index <= end] for key, s in series.items()}


# A week after the step every warning is still raised (the slowest windows
# have not caught up), and the feed stops there.
STOPPED = date(2024, 3, 11)


def test_stale_data_abstains_so_a_dead_feed_cannot_hold_the_pause():
    governor = RiskGovernor(until(world(*CORE_SIGNALS), STOPPED))
    fresh = governor.reading(next_session(STOPPED))
    assert fresh.votes == 5 and fresh.paused and fresh.stale == ()
    week = governor.reading(next_session(STOPPED + timedelta(days=5)))
    assert week.paused  # a long weekend and a missed run are not "stale"
    later = governor.reading(next_session(STOPPED + timedelta(days=30)))
    assert later.votes == 0 and later.known == 0 and not later.paused
    assert set(later.stale) == set(CORE_SIGNALS)


def test_one_stale_input_silences_only_its_own_warning():
    series = until(world(*CORE_SIGNALS), STOPPED)
    series["ofr_FSI"] = until(series, STEP - timedelta(days=20))["ofr_FSI"]
    day = next_session(STOPPED)
    reading = RiskGovernor(series).reading(day)
    assert reading.stale == ("fsi_rising",) and reading.votes == 4 and reading.paused
    assert not RiskGovernor(series, min_votes=5).paused(day)
    # A wider limit lets the old reading vote again: it reads "clear".
    lenient = RiskGovernor(series, stale_days=60).reading(day)
    assert lenient.stale == () and lenient.votes == 4 and lenient.known == 5


def test_a_day_that_is_not_a_session_reads_as_the_next_one():
    governor = RiskGovernor(world(*CORE_SIGNALS))
    saturday = date(2024, 3, 9)
    assert governor.reading(saturday).raised == governor.reading(date(2024, 3, 11)).raised


# -- configuration ---------------------------------------------------------------


def test_a_missing_input_refuses_and_names_it():
    series = calm_world()
    del series["ofr_FSI"]
    with pytest.raises(ConfigurationError, match="ofr_FSI"):
        RiskGovernor(series)


@pytest.mark.parametrize(
    ("options", "match"),
    [
        ({"signals": "vxn_hi,nope"}, "unknown governor signal"),
        ({"signals": "vxn_hi,vxn_hi"}, "distinct"),
        ({"min_votes": 0}, "min_votes"),
        ({"min_votes": 6}, "min_votes"),
        ({"stale_days": 0}, "stale_days"),
    ],
)
def test_bad_options_are_refused(options, match):
    with pytest.raises(ConfigurationError, match=match):
        RiskGovernor(calm_world(), **options)


def test_signals_parse_from_the_string_a_config_carries():
    assert parse_signals(" vxn_hi, credit ") == ("vxn_hi", "credit")
    assert parse_signals(",".join(CORE_SIGNALS)) == CORE_SIGNALS


def _write(directory, series: dict[str, pd.Series]) -> None:
    for key, s in series.items():
        pd.DataFrame({"timestamp": s.index, "close": s.to_numpy()}).to_csv(
            directory / f"{key}.csv", index=False
        )


def test_it_reads_the_files_the_refresh_writes(tmp_path, monkeypatch):
    _write(tmp_path, world(*CORE_SIGNALS))
    governor = RiskGovernor.from_directory(tmp_path)
    assert governor.reading(next_session(STEP)).votes == 5
    monkeypatch.setenv(EXTERNAL_DIR_ENV, str(tmp_path))
    assert external_directory() == tmp_path
    assert RiskGovernor.from_directory().paused(next_session(STEP))
    (tmp_path / "cboe_VXN.csv").unlink()
    with pytest.raises(ConfigurationError, match=r"cboe_VXN.*looked in"):
        RiskGovernor.from_directory(tmp_path)


# -- the switch on Daily Ultimate ------------------------------------------------

UNIT = {"per_lot_pct": 0.01, "lookback_days": 1.0, "bars_per_day": 390}


def _ctx(day: date, minute: int = 0, equity: float = 100_000.0) -> MarketContext:
    ts = pd.Timestamp(f"{day} 14:30", tz="UTC") + pd.Timedelta(minutes=max(minute, 0))
    return MarketContext(
        timestamp=ts,
        open=100.0,
        high=100.0,
        low=100.0,
        close=100.0,
        cash=equity,
        equity=equity,
        peak_equity=equity,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
        time_of_day_flag=minute,
    )


def test_off_by_default_and_then_it_is_daily_ultimate_as_it_was():
    strategy = DailyUltimateSizing(**UNIT)
    assert strategy._governor is None and strategy._caution_map is None
    assert not any(key.startswith("caution") for key in strategy.diagnostics())


def test_a_paused_session_buys_nothing_and_changes_nothing_else():
    day, after = date(2024, 1, 2), date(2024, 1, 3)
    strategy = DailyUltimateSizing(
        **UNIT, regime_by_date={day: True, after: True}, caution_by_date={day: True}
    )
    strategy.record_tick(_ctx(day))
    assert strategy.mode == CALM and strategy.cautious
    assert strategy._grid_trigger_level(_ctx(day), 100.0, 0.002) == NO_BUY_LEVEL
    assert strategy.lots_to_liquidate([], _ctx(day)) == []
    assert strategy.flips_to_turbulent == 0
    strategy.record_tick(_ctx(after))
    assert strategy.mode == CALM and not strategy.cautious
    assert strategy._grid_trigger_level(_ctx(after), 100.0, 0.002) > 0
    assert strategy.diagnostics()["caution_sessions"] == 1


def test_the_strategy_reads_its_governor_from_the_directory(tmp_path):
    _write(tmp_path, world(*CORE_SIGNALS))
    before, after = STEP, next_session(STEP)
    strategy = DailyUltimateSizing(
        **UNIT,
        regime_by_date={before: True, after: True},
        caution_min_votes=CORE_MIN_VOTES,
        caution_dir=str(tmp_path),
    )
    strategy.record_tick(_ctx(before))
    assert not strategy.cautious
    assert strategy._grid_trigger_level(_ctx(before), 100.0, 0.002) > 0
    strategy.record_tick(_ctx(after))
    assert strategy.cautious
    assert strategy._grid_trigger_level(_ctx(after), 100.0, 0.002) == NO_BUY_LEVEL
    diagnostics = strategy.diagnostics()
    assert diagnostics["caution_votes"] == 5 and diagnostics["caution_stale"] == ""
    assert diagnostics["caution_raised"] == ", ".join(CORE_SIGNALS)


def test_a_governor_without_its_data_stops_the_strategy_being_built(tmp_path):
    with pytest.raises(ConfigurationError, match="refresh_external"):
        DailyUltimateSizing(**UNIT, caution_min_votes=4, caution_dir=str(tmp_path))


def test_the_run_form_shows_the_switch_and_hides_the_wiring():
    cls = resolve_strategy("daily_ultimate")
    shown = {p["name"] for p in param_schema.describe_params("daily_ultimate", cls)}
    assert {"caution_min_votes", "caution_signals", "caution_stale_days"} <= shown
    assert not {"caution_dir", "caution_by_date"} & shown
