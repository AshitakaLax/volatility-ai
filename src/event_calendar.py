"""
Minute-precision, index-weighted earnings event windows.

--------------------------------------------------------------------
WHAT THIS REPLACES

src/earnings_calendar.py stores a frozenset[date] -- 296 dates, day
granularity, no company attribution, no weight. Every join truncates
through .date() before comparison, so a bar at 09:31 and a bar at
15:59 are identical to it. This module is the minute-precision
replacement: an interval per event, carrying which company, how much
of the index it represents, and a configurable lead time.

src/earnings_calendar.py is left importable and unchanged -- it is
still what every existing recorded sweep result was produced against,
and this module is additive, not a migration.

--------------------------------------------------------------------
THE DATA

data/earnings_releases_derived.csv, from tools/build_earnings_calendar.py:
676 release timestamps across 16 tickers, RECOVERED FROM THE TAPE
rather than transcribed -- found the day from the next session's
opening gap (release timing is a scheduled, publicly announced fact;
recovering the schedule offline and showing the strategy only "an
event is scheduled at 16:06" is not lookahead -- see that module's
docstring for the full argument), then the minute from that day's peak
post-close volume. Cross-checked against a hand-supplied reference
table: 2 tickers exact, 6 more within 2 minutes, worst case 5.

Weights are src/index_weights.py's single 2026-08-13 snapshot, and
that module documents why applying it to all history is lookahead bias
that quarterly snapshots are meant to fix later. Nothing here corrects
that; it is inherited, not introduced.

--------------------------------------------------------------------
LEAD AND REACTION WINDOWS

Each event becomes one interval: [release - lead_minutes, release +
reaction_minutes). default lead_minutes=15.0 matches the motivating
example directly -- "aware 15 minutes before a 5:30pm release."
reaction_minutes=30.0 is a design default, not a measured constant;
src/high_frequency_sizing.py's own event-day boosts operate at whole-
session granularity, so there is no existing minute-scale reaction
measurement to inherit here.

event_intensity is a SUM over every event whose window currently
contains the bar, not a max. Two constituents reporting within the
same 45-minute window is rare but real (14 of this project's 74 FOMC
days also carried a mega-cap earnings reaction, at day granularity --
see src/high_frequency_sizing.py's docstring on why THOSE combine with
max instead: they are alternative labels for the SAME claim, "the
index is scheduled to move today." Two different companies reporting
in the same window are not the same claim -- they are two independent
sources of exposure, and summing their weights is what actual index
risk would do.

minutes_to_event counts down only through the LEAD portion, and is the
sentinel -1.0 once the release has happened -- including through the
reaction window, where event_intensity is still nonzero. "Aware 15
minutes before" is a countdown to something that hasn't happened yet;
once it has, intensity is what says the window is still active, not
a countdown that would otherwise have to go negative or freeze at
zero, both worse than a lookahead-safe fact ("already occurred") the
strategy can check independently.

--------------------------------------------------------------------
STATE OWNERSHIP AND COST

EarningsEventTable holds only the sorted interval table -- read-only
after construction, no per-lot or per-strategy state. vectorized()
does one O(bars log events) pass using np.searchsorted per event
rather than a per-bar Python loop, matching this project's existing
convention (optimization_controller's _fomc_flags/_earnings_flags) of
computing derived per-bar arrays once and indexing them, not
recomputing per bar in the hot loop.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.exceptions import ConfigurationError, DataValidationError
from src.index_weights import weight_pct

DEFAULT_EARNINGS_CSV = Path("data/earnings_releases_derived.csv")
DEFAULT_LEAD_MINUTES = 15.0
DEFAULT_REACTION_MINUTES = 30.0

NO_EVENT_MINUTES = -1.0


class EarningsEventTable:
    """A sorted table of weighted event windows, with vectorized and
    scalar lookups sharing one definition of the window."""

    def __init__(
        self,
        events: pd.DataFrame,
        *,
        lead_minutes: float = DEFAULT_LEAD_MINUTES,
        reaction_minutes: float = DEFAULT_REACTION_MINUTES,
    ) -> None:
        """events must have columns 'release_utc' (tz-aware) and
        'symbol'. Weight is looked up per symbol at construction, not
        per lookup, since src/index_weights.weight_pct is currently a
        constant table -- this is the seam that changes when
        quarterly snapshots land (see that module)."""
        if lead_minutes <= 0:
            raise ConfigurationError(f"lead_minutes must be positive, got {lead_minutes}")
        if reaction_minutes <= 0:
            raise ConfigurationError(f"reaction_minutes must be positive, got {reaction_minutes}")
        if events.empty:
            raise DataValidationError("EarningsEventTable given an empty event set.")

        self.lead_minutes = lead_minutes
        self.reaction_minutes = reaction_minutes

        release = pd.DatetimeIndex(events["release_utc"])
        if release.tz is None:
            raise DataValidationError(
                "EarningsEventTable requires tz-aware release_utc timestamps."
            )
        release = release.tz_convert("UTC")

        weights = events["symbol"].map(weight_pct).to_numpy(dtype=float)
        order = np.argsort(release.values)
        self._release = release[order]
        self._weight = weights[order]
        self._window_start = self._release - pd.Timedelta(minutes=lead_minutes)
        self._window_end = self._release + pd.Timedelta(minutes=reaction_minutes)

    @classmethod
    def from_csv(cls, path: Path | str = DEFAULT_EARNINGS_CSV, **kw) -> EarningsEventTable:
        events = pd.read_csv(path)
        events["release_utc"] = pd.to_datetime(events["release_utc"], utc=True)
        return cls(events, **kw)

    @property
    def event_count(self) -> int:
        return len(self._release)

    def scalar(self, timestamp: pd.Timestamp) -> tuple[float, float]:
        """(event_intensity, minutes_to_event) for one timestamp.

        For the live path: one lookup per tick, O(log events). Not
        vectorized -- there is exactly one timestamp per call, and
        building the machinery to batch calls that never arrive
        batched would add complexity for the case that does not occur.

        Uses np.searchsorted with side="right" for the countdown, the
        SAME boundary vectorized() uses via its lead_hi cut -- both
        exclude the release instant itself from the countdown (a bar
        AT the release is already in the reaction window, not counting
        down to it). Getting this boundary to disagree between the two
        paths is exactly the class of bug this module's docstring
        warns decision_cycle.py exists to prevent elsewhere; it is
        pinned directly by test_scalar_and_vectorized_agree_on_every_bar.
        """
        # Accept a plain datetime.datetime too, not only pd.Timestamp --
        # live_trading_loop.py's bar.timestamp is the former, and
        # pd.Timestamp is a strict subclass so this is a no-op there.
        timestamp = pd.Timestamp(timestamp)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        ts64 = timestamp.to_datetime64()

        active = (self._window_start.values <= ts64) & (ts64 < self._window_end.values)
        intensity = float(self._weight[active].sum())

        i = np.searchsorted(self._release.values, ts64, side="right")
        if i < len(self._release):
            minutes = (self._release.values[i] - ts64) / np.timedelta64(1, "m")
            if minutes <= self.lead_minutes:
                return intensity, float(minutes)
        return intensity, NO_EVENT_MINUTES

    def vectorized(self, index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
        """(event_intensity, minutes_to_event) arrays, one entry per bar.

        index must be sorted ascending and tz-aware (this project's
        DataFrames always are by the time they reach here -- see
        historical_data.to_backtest_frame). Bars are assumed sorted,
        which is what makes the searchsorted approach below O(log n)
        per event rather than O(n).
        """
        if index.tz is None:
            raise DataValidationError("EarningsEventTable.vectorized requires a tz-aware index.")
        idx_utc = index.tz_convert("UTC")

        intensity = np.zeros(len(idx_utc), dtype=float)
        minutes_to_event = np.full(len(idx_utc), NO_EVENT_MINUTES, dtype=float)

        idx_values = idx_utc.values
        for start, end, release, weight in zip(
            self._window_start, self._window_end, self._release, self._weight, strict=False
        ):
            # .to_datetime64() rather than np.datetime64(ts): the latter
            # on a tz-aware Timestamp warns and silently drops the tz --
            # harmless here since idx_values is already UTC-normalized,
            # but the explicit conversion says so instead of relying on
            # a warning nobody reads in a hot loop.
            start64, end64, release64 = (
                start.to_datetime64(),
                end.to_datetime64(),
                release.to_datetime64(),
            )
            lo = np.searchsorted(idx_values, start64, side="left")
            hi = np.searchsorted(idx_values, end64, side="left")
            if lo < hi:
                intensity[lo:hi] += weight

            # Countdown covers only the LEAD portion, [start, release).
            # side="left" for release excludes the release instant
            # itself, matching scalar()'s side="right" boundary exactly
            # -- see that method's docstring.
            lead_hi = np.searchsorted(idx_values, release64, side="left")
            lead_lo = lo
            if lead_lo < lead_hi:
                span = idx_values[lead_lo:lead_hi]
                mins = (release64 - span) / np.timedelta64(1, "m")
                # A later, closer event must not be overwritten by an
                # earlier iteration's farther one -- keep the minimum
                # countdown seen so far, not the last one written.
                current = minutes_to_event[lead_lo:lead_hi]
                still_default = current == NO_EVENT_MINUTES
                minutes_to_event[lead_lo:lead_hi] = np.where(
                    still_default, mins, np.minimum(current, mins)
                )
        return intensity, minutes_to_event
