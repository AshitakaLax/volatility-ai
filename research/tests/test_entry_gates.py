"""Unit tests for research/strategies/entry_gates.py.

Every sequence here is built by hand so each expected level can be
checked by arithmetic, not by re-running the code under test. Bars are
regular-session minutes in January (EST), so 14:30 UTC is minute 0.

The causality tests are the ones that matter most: a gate deciding bar
t from bar t's own close would be lookahead under fill_model="intrabar",
and nothing else in the suite would notice.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.entry_gates import (
    BreakdownGate,
    Candle,
    ShootingStarGate,
    as_count,
    is_shooting_star,
)

DAY0 = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def ctx(day: int, minute: int, o: float, h: float, lo: float, c: float, flag=None):
    """One bar. `flag` overrides time_of_day_flag (-1 = out of session)."""
    return MarketContext(
        timestamp=DAY0 + timedelta(days=day, minutes=minute),
        open=o,
        high=h,
        low=lo,
        close=c,
        cash=100_000.0,
        equity=100_000.0,
        peak_equity=100_000.0,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
        time_of_day_flag=minute if flag is None else flag,
    )


def flat(day: int, minute: int, price: float, spread: float = 0.1):
    return ctx(day, minute, price, price + spread, price - spread, price)


def feed(gate, bars) -> list[bool]:
    """Observe each bar; return the suppression state after each."""
    states = []
    for bar in bars:
        gate.observe(bar)
        states.append(gate.suppressed)
    return states


# --------------------------------------------------------------------
# as_count


class TestAsCount:
    def test_an_integral_float_is_accepted(self):
        """analyze_annual hands back 5.0 for an int column with blanks."""
        assert as_count("n", 5.0) == 5
        assert isinstance(as_count("n", 5.0), int)

    @pytest.mark.parametrize("bad", [5.5, True, "5", None])
    def test_anything_else_fails_loudly(self, bad):
        with pytest.raises(ConfigurationError):
            as_count("n", bad)

    def test_the_minimum_is_enforced(self):
        with pytest.raises(ConfigurationError):
            as_count("n", 0)


# --------------------------------------------------------------------
# BreakdownGate


class TestBreakdownValidation:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {"mode": "dual-thrust"},
            {"mode": "dual_thrust", "release": "never"},
            {"mode": "dual_thrust", "dt_k": 0.0},
            {"mode": "dual_thrust", "dt_lookback_days": 0},
            {"mode": "opening_range", "orb_minutes": 390},
            {"mode": "opening_range", "orb_minutes": 15.5},
        ],
    )
    def test_bad_configuration_fails_at_construction(self, kwargs):
        mode = kwargs.pop("mode")
        with pytest.raises(ConfigurationError):
            BreakdownGate(mode, **kwargs)


class TestBreakdownOff:
    def test_off_never_suppresses_and_counts_nothing(self):
        gate = BreakdownGate("off")
        crash = [flat(d, m, 100.0 - 5 * d - m) for d in range(4) for m in range(5)]
        assert not any(feed(gate, crash))
        assert gate.level is None
        assert (gate.suppressed_bars, gate.episodes) == (0, 0)


class TestPriorLow:
    def _yesterday(self):
        # Session low 99.0 on its LAST bar -- also pins fold-before-roll:
        # a gate that rolled the session before folding the final bar
        # would remember 99.5 instead.
        return [
            ctx(0, 0, 100.0, 100.5, 99.6, 100.0),
            ctx(0, 1, 100.0, 100.4, 99.5, 99.8),
            ctx(0, 2, 99.8, 99.9, 99.0, 99.2),
        ]

    def test_level_is_yesterdays_low_including_its_last_bar(self):
        gate = BreakdownGate("prior_low")
        feed(gate, [*self._yesterday(), flat(1, 0, 100.0)])
        assert gate.level == pytest.approx(99.0)

    def test_a_gap_below_yesterdays_low_blocks_from_the_first_bar(self):
        gate = BreakdownGate("prior_low")
        states = feed(gate, [*self._yesterday(), flat(1, 0, 98.0)])
        assert states[-1] is True
        assert gate.episodes == 1

    def test_reclaim_releases_on_an_open_above_the_level(self):
        gate = BreakdownGate("prior_low", release="reclaim")
        today = [flat(1, 0, 98.0), flat(1, 1, 98.5), flat(1, 2, 99.5), flat(1, 3, 98.0)]
        states = feed(gate, self._yesterday() + today)
        assert states[-4:] == [True, True, False, True]
        assert gate.episodes == 2

    def test_session_release_holds_until_the_session_ends(self):
        gate = BreakdownGate("prior_low", release="session")
        today = [flat(1, 0, 98.0), flat(1, 1, 99.5), flat(1, 2, 101.0)]
        tomorrow = [flat(2, 0, 101.0)]
        states = feed(gate, self._yesterday() + today + tomorrow)
        assert states[-4:] == [True, True, True, False]

    def test_no_history_means_no_level(self):
        gate = BreakdownGate("prior_low")
        assert not any(feed(gate, [flat(0, 0, 100.0), flat(0, 1, 50.0)]))
        assert gate.level is None


class TestDualThrust:
    def _history(self):
        """Three one-bar sessions with hand-picked H/L/C:

        highs 102, 103, 101   -> HH 103
        lows   98,  99,  97   -> LL 97
        closes 100, 101, 99   -> HC 101, LC 99
        range = max(HH - LC, HC - LL) = max(4, 4) = 4
        """
        return [
            ctx(0, 0, 100.0, 102.0, 98.0, 100.0),
            ctx(1, 0, 100.0, 103.0, 99.0, 101.0),
            ctx(2, 0, 100.0, 101.0, 97.0, 99.0),
        ]

    def test_no_level_until_lookback_sessions_have_completed(self):
        gate = BreakdownGate("dual_thrust", dt_lookback_days=3, dt_k=0.5)
        feed(gate, self._history())  # the third session is still open
        assert gate.level is None

    def test_level_is_open_minus_k_times_the_range(self):
        gate = BreakdownGate("dual_thrust", dt_lookback_days=3, dt_k=0.5)
        feed(gate, [*self._history(), flat(3, 0, 100.0)])
        assert gate.level == pytest.approx(100.0 - 0.5 * 4.0)

    def test_the_range_takes_the_larger_of_its_two_spans(self):
        # HH 110, LC 99 -> 11; HC 101, LL 97 -> 4. Must pick 11.
        history = self._history()
        history[1] = ctx(1, 0, 100.0, 110.0, 99.0, 101.0)
        gate = BreakdownGate("dual_thrust", dt_lookback_days=3, dt_k=0.5)
        feed(gate, [*history, flat(3, 0, 100.0)])
        assert gate.level == pytest.approx(100.0 - 0.5 * 11.0)

    def test_an_intraday_break_blocks_and_a_reclaim_releases(self):
        gate = BreakdownGate("dual_thrust", dt_lookback_days=3, dt_k=0.5)
        today = [flat(3, 0, 100.0), flat(3, 1, 97.9), flat(3, 2, 98.5)]  # level 98.0
        states = feed(gate, self._history() + today)
        assert states[-3:] == [False, True, False]

    def test_every_session_starts_unblocked(self):
        gate = BreakdownGate("dual_thrust", dt_lookback_days=3, dt_k=0.5, release="session")
        bars = [*self._history(), flat(3, 0, 100.0), flat(3, 1, 90.0), flat(4, 0, 90.0)]
        states = feed(gate, bars)
        assert states[-2:] == [True, False]


class TestOpeningRange:
    def test_no_level_while_the_range_is_forming_then_its_low(self):
        gate = BreakdownGate("opening_range", orb_minutes=3)
        window = [
            ctx(0, 0, 100.0, 100.6, 99.7, 100.2),
            ctx(0, 1, 100.2, 100.8, 99.4, 100.0),  # range low 99.4
            ctx(0, 2, 100.0, 100.3, 99.8, 100.1),
        ]
        states = feed(gate, window)
        assert gate.level is None and not any(states)
        gate.observe(flat(0, 3, 100.0))
        assert gate.level == pytest.approx(99.4)
        assert gate.suppressed is False
        gate.observe(flat(0, 4, 99.3))
        assert gate.suppressed is True

    def test_the_range_resets_each_session(self):
        gate = BreakdownGate("opening_range", orb_minutes=1)
        feed(gate, [flat(0, 0, 100.0), flat(0, 1, 100.0), flat(1, 0, 50.0)])
        assert gate.level is None  # today's range has not formed yet


class TestBreakdownCausality:
    def test_a_bar_cannot_gate_itself_with_its_own_close(self):
        """Two runs identical except bar t's low/close, which crash
        below the level. The decision AT bar t must be identical --
        only bar t+1 may differ. Under fill_model="intrabar" anything
        else is lookahead."""
        history = TestDualThrust()._history()
        calm = [*history, flat(3, 0, 100.0), ctx(3, 1, 99.0, 99.2, 98.8, 99.0)]
        crash = [*history, flat(3, 0, 100.0), ctx(3, 1, 99.0, 99.2, 90.0, 90.0)]
        nxt_calm, nxt_crash = flat(3, 2, 99.0), flat(3, 2, 90.0)
        a, b = (
            BreakdownGate("dual_thrust", dt_lookback_days=3),
            BreakdownGate("dual_thrust", dt_lookback_days=3),
        )
        assert feed(a, calm) == feed(b, crash)
        a.observe(nxt_calm)
        b.observe(nxt_crash)
        assert (a.suppressed, b.suppressed) == (False, True)

    def test_out_of_session_bars_change_nothing(self):
        bars = [*TestPriorLow()._yesterday(), flat(1, 0, 100.0)]
        noisy = list(bars)
        noisy.insert(3, ctx(0, 400, 50.0, 200.0, 1.0, 50.0, flag=-1))  # after the close
        a, b = BreakdownGate("prior_low"), BreakdownGate("prior_low")
        feed(a, bars)
        feed(b, noisy)
        assert a.level == b.level == pytest.approx(99.0)
        assert a.suppressed == b.suppressed


# --------------------------------------------------------------------
# ShootingStarGate


# A canonical sequence, oldest first, every condition satisfied:
#   prior2 / prior1 rise into the star (closes 100.2 -> 100.5 -> 100.8)
#   star: open 101.0 close 100.8 (body 0.2), low 100.78 (lower shadow
#         0.02 < 0.2 * 0.2), high 101.6 (upper shadow 0.6 >= 2 * 0.2)
#   confirm: high 101.0 <= 101.6, close 100.4 <= 100.8
P2 = Candle(99.2, 100.3, 99.1, 100.2)
P1 = Candle(99.5, 100.6, 99.4, 100.5)
STAR = Candle(101.0, 101.6, 100.78, 100.8)
CONFIRM = Candle(100.8, 101.0, 100.3, 100.4)
TYPICAL = 0.01  # 1% bodies, so the 0.5x threshold is 0.5%; the star's is ~0.2%


class TestIsShootingStar:
    def test_the_canonical_star_passes(self):
        assert is_shooting_star(STAR, P1, P2, CONFIRM, TYPICAL, 0.2, 0.5)

    def test_an_unwarmed_typical_body_never_signals(self):
        assert not is_shooting_star(STAR, P1, P2, CONFIRM, None, 0.2, 0.5)

    @pytest.mark.parametrize(
        "star, p1, p2, confirm, why",
        [
            (Candle(100.8, 101.6, 100.78, 101.0), P1, P2, CONFIRM, "1: bullish body"),
            (Candle(101.0, 101.6, 100.5, 100.8), P1, P2, CONFIRM, "2: lower shadow"),
            (Candle(101.0, 103.0, 99.99, 100.0), P1, P2, CONFIRM, "3: body too big"),
            (Candle(101.0, 101.3, 100.78, 100.8), P1, P2, CONFIRM, "4: short upper shadow"),
            (STAR, Candle(99.5, 101.0, 99.4, 100.9), P2, CONFIRM, "5: no rise into star"),
            (STAR, P1, Candle(99.2, 100.7, 99.1, 100.6), CONFIRM, "6: no prior rise"),
            (STAR, P1, P2, Candle(100.8, 101.7, 100.3, 100.4), "7: confirm made a new high"),
            (STAR, P1, P2, Candle(100.8, 101.0, 100.3, 100.9), "8: confirm closed higher"),
        ],
    )
    def test_each_condition_is_necessary(self, star, p1, p2, confirm, why):
        assert not is_shooting_star(star, p1, p2, confirm, TYPICAL, 0.2, 0.5), why

    def test_a_flat_body_cannot_have_a_lower_shadow_below_zero(self):
        doji = Candle(101.0, 101.6, 100.9, 101.0)
        assert not is_shooting_star(doji, P1, P2, CONFIRM, TYPICAL, 0.2, 0.5)


def _star_session(day: int = 0) -> list:
    """One-minute candles: three warm-up candles with ~1% bodies, then
    P2, P1, STAR, CONFIRM, then bars that only exist to complete the
    candles before them. Index 7 is the first bar that may be gated."""
    warm = [
        Candle(98.0, 99.1, 97.9, 99.0),
        Candle(98.5, 99.6, 98.4, 99.5),
        Candle(98.8, 99.9, 98.7, 99.8),
    ]
    candles = [*warm, P2, P1, STAR, CONFIRM]
    bars = [ctx(day, m, c.open, c.high, c.low, c.close) for m, c in enumerate(candles)]
    return bars


def _gate(**kw):
    defaults = dict(candle_minutes=1, hold_candles=2, body_lookback=3)
    defaults.update(kw)
    return ShootingStarGate("shooting_star", **defaults)


class TestShootingStarGate:
    def test_validation(self):
        with pytest.raises(ConfigurationError):
            ShootingStarGate("hammer")
        with pytest.raises(ConfigurationError):
            ShootingStarGate("shooting_star", candle_minutes=196)
        with pytest.raises(ConfigurationError):
            ShootingStarGate("shooting_star", body_size=0.0)

    def test_off_is_inert(self):
        gate = ShootingStarGate("off", candle_minutes=1, body_lookback=3)
        assert not any(feed(gate, [*_star_session(), flat(0, 7, 100.4)]))
        assert gate.episodes == 0

    def test_blocks_only_once_the_confirming_candle_is_complete(self):
        """The confirm candle is bar 6; it is complete only when bar 7
        starts. Gating bar 6 itself would be the original's shift(-1)
        lookahead in a new place."""
        gate = _gate()
        states = feed(gate, [*_star_session(), flat(0, 7, 100.4)])
        assert states[6] is False
        assert states[7] is True
        assert gate.episodes == 1

    def test_releases_after_hold_candles_complete(self):
        gate = _gate(hold_candles=2)
        tail = [flat(0, 7, 100.4), flat(0, 8, 100.3), flat(0, 9, 100.2)]
        states = feed(gate, _star_session() + tail)
        assert states[7:] == [True, True, False]

    def test_an_open_above_the_star_high_undoes_it(self):
        gate = _gate(hold_candles=10)
        tail = [flat(0, 7, 100.4), flat(0, 8, 101.7)]
        states = feed(gate, _star_session() + tail)
        assert states[7:] == [True, False]

    def test_a_block_expires_at_the_session_end(self):
        gate = _gate(hold_candles=10)
        states = feed(gate, [*_star_session(), flat(0, 7, 100.4), flat(1, 0, 100.4)])
        assert states[-2:] == [True, False]

    def test_candles_never_span_sessions(self):
        """The same seven candles split 3 / 4 across two sessions: the
        four-candle window is cleared at the roll, so no star."""
        bars = _star_session()
        split = bars[:5] + [
            ctx(1, m, b.open, b.high, b.low, b.close) for m, b in enumerate(bars[5:])
        ]
        gate = _gate()
        assert not any(feed(gate, [*split, flat(1, 2, 100.4)]))

    def test_a_cold_body_average_never_signals(self):
        gate = _gate(body_lookback=50)
        assert not any(feed(gate, [*_star_session(), flat(0, 7, 100.4)]))

    def test_multi_minute_candles_aggregate_open_high_low_close(self):
        """Two one-minute bars per candle reproduce the same star."""
        bars = []
        for m, bar in enumerate(_star_session()):
            mid = (bar.open + bar.close) / 2
            bars.append(ctx(0, 2 * m, bar.open, bar.high, min(bar.low, mid), mid))
            bars.append(ctx(0, 2 * m + 1, mid, max(mid, bar.close), bar.low, bar.close))
        gate = _gate(candle_minutes=2)
        states = feed(gate, [*bars, flat(0, 14, 100.4)])
        assert states[13] is False and states[14] is True
