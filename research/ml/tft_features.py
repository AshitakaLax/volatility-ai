"""The Temporal Fusion Transformer's covariates, one definition for training
and trading (research/ml/tft_training.py builds them for a whole history;
research/ml/tft_sizing.py keeps them bar by bar).

--------------------------------------------------------------------
THE COVARIATE GROUPS, AS THE TFT SEES THEM

    target              log_close              log of the bar's close; the model
                                               forecasts its quantiles H bars ahead
    observed (unknown)  ret_1   R_{t-1}        log(close_s / close_{s-1})
    time-varying        ret_2   R_{t-2}        the same, one bar earlier
                        s_macro                macroeconomic surprise
                        s_earnings             earnings-call / filing sentiment
                        s_news                 news sentiment
    known future        e_event E_event        1 on a scheduled FOMC decision day
                        t_open  T_open         minutes since 09:30 New York / 390
                        t_close T_close        minutes until 16:00 New York / 390

"Observed" inputs exist only up to the forecast origin, so the TFT reads them
in its encoder alone. "Known" inputs are scheduled -- the calendar and the
clock say what they will be -- so the decoder reads their future values too;
that is the TFT's ability to condition a forecast on an economic calendar
(Lim et al. 2021, sec. 3).

At row s, ret_1 is the return INTO bar s and ret_2 the return into s-1. At
a forecast origin t (the bar being traded), the encoder ends at t-1, so
its last row carries exactly R_{t-1} and R_{t-2}.

--------------------------------------------------------------------
OUTSIDE SERIES ARE READ POINT-IN-TIME

The three sentiment / surprise series come from CSV files (a `timestamp`
or `date` column and a `value` column). A row stamped with a time is usable
on bars STRICTLY after that time; a row stamped with a date only is usable
from the next calendar day (it describes a day still in progress). Before
its first row, or with no file at all, a series is 0.0 -- neutral -- and
the model is trained on the same zeros, so a missing file cannot become a
silent difference between training and trading. The trainer records which
files it used and the sizer refuses to run without them.

--------------------------------------------------------------------
THE BUFFER

CovariateRing keeps the last `capacity` rows in a pre-allocated float64
array: a push is one row write and an index increment, O(1) and
allocation-free, which is what the live dispatcher's per-bar budget allows.
Only a forecast -- once per trigger at most -- copies the window out in
chronological order, O(capacity).
"""

from __future__ import annotations

import bisect
import csv
import math
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from engine.core import trading_calendar
from engine.core.exceptions import ConfigurationError
from engine.data.fomc_calendar import FOMC_DECISION_DATES

NEW_YORK = ZoneInfo("America/New_York")
SESSION_MINUTES = 390
_OPEN_MINUTE = 9 * 60 + 30

TARGET = "log_close"
OBSERVED = ("ret_1", "ret_2", "s_macro", "s_earnings", "s_news")
KNOWN = ("e_event", "t_open", "t_close")
SOURCES = ("s_macro", "s_earnings", "s_news")
# One row of the ring: the target, then the observed inputs, then the known.
ROW = (TARGET, *OBSERVED, *KNOWN)


def _utc(ts) -> datetime:
    if isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    return ts.replace(tzinfo=UTC) if ts.tzinfo is None else ts


def known_at(ts) -> tuple[float, float, float]:
    """(e_event, t_open, t_close) for a bar opening at `ts`."""
    local = _utc(ts).astimezone(NEW_YORK)
    minute = local.hour * 60 + local.minute + local.second / 60.0 - _OPEN_MINUTE
    event = 1.0 if local.date() in FOMC_DECISION_DATES else 0.0
    return event, minute / SESSION_MINUTES, (SESSION_MINUTES - minute) / SESSION_MINUTES


def known_frame(index: pd.DatetimeIndex) -> pd.DataFrame:
    """`known_at` over a whole index (the training path)."""
    if index.tz is None:
        index = index.tz_localize("UTC")
    local = index.tz_convert(NEW_YORK)
    naive = local.tz_localize(None)
    minute = (naive - naive.normalize()).total_seconds().to_numpy() / 60.0 - _OPEN_MINUTE
    dates = naive.date
    event = np.fromiter((d in FOMC_DECISION_DATES for d in dates), dtype=float, count=len(dates))
    return pd.DataFrame(
        {
            "e_event": event,
            "t_open": minute / SESSION_MINUTES,
            "t_close": (SESSION_MINUTES - minute) / SESSION_MINUTES,
        },
        index=index,
    )


def future_bar_times(ts, steps: int, bars_per_day: int) -> list[datetime]:
    """Opening times of the next `steps` bars after the one opening at
    `ts`, on the NYSE calendar: a bar past the close continues at the next
    session's open. Regular-session bars only; the decoder's known inputs
    are read from these."""
    bar = timedelta(minutes=SESSION_MINUTES / bars_per_day)
    local = _utc(ts).astimezone(NEW_YORK)
    day = local.date()
    open_at = datetime.combine(day, datetime.min.time(), NEW_YORK) + timedelta(minutes=_OPEN_MINUTE)
    offset = local - open_at
    if offset < timedelta(0):  # before the open: the next bar is the open itself
        offset = -bar
        if not trading_calendar.is_session(day):
            day = trading_calendar.next_session(day)
            open_at = datetime.combine(day, datetime.min.time(), NEW_YORK) + timedelta(
                minutes=_OPEN_MINUTE
            )
    out = []
    for _ in range(steps):
        offset += bar
        if offset >= timedelta(minutes=SESSION_MINUTES):
            day = trading_calendar.next_session(day)
            open_at = datetime.combine(day, datetime.min.time(), NEW_YORK) + timedelta(
                minutes=_OPEN_MINUTE
            )
            offset = timedelta(0)
        out.append((open_at + offset).astimezone(UTC))
    return out


class PointInTimeSeries:
    """One outside series, read as of each bar. `path` empty: always 0.0."""

    def __init__(self, path: str | None, column: str = "value") -> None:
        self.path = path or ""
        self._times: list[datetime] = []
        self._values: list[float] = []
        self._cursor = 0
        if self.path:
            self._load(Path(self.path), column)

    def _load(self, path: Path, column: str) -> None:
        if not path.exists():
            raise ConfigurationError(f"series file not found: {path}")
        rows = []
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    if row.get("timestamp"):
                        stamp = pd.Timestamp(row["timestamp"])
                        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp
                        usable = stamp.to_pydatetime().astimezone(UTC) + timedelta(microseconds=1)
                    else:
                        day = date.fromisoformat(row["date"].strip()[:10])
                        usable = datetime.combine(day + timedelta(days=1), datetime.min.time(), UTC)
                    value = float(row[column])
                except (KeyError, ValueError, TypeError) as exc:
                    raise ConfigurationError(
                        f"bad row in {path} (need `timestamp` or `date`, and `{column}`): {row}"
                    ) from exc
                if math.isfinite(value):
                    rows.append((usable, value))
        if not rows:
            raise ConfigurationError(f"no rows in {path}")
        rows.sort()
        self._times = [r[0] for r in rows]
        self._values = [r[1] for r in rows]

    def at(self, ts) -> float:
        """The latest value usable at bar time `ts`. Amortised O(1) when the
        bars come in time order (the strategy's case); a bisection otherwise."""
        if not self._times:
            return 0.0
        when = _utc(ts)
        k = self._cursor
        if k > 0 and self._times[k - 1] > when:
            k = bisect.bisect_right(self._times, when)
        while k < len(self._times) and self._times[k] <= when:
            k += 1
        self._cursor = k
        return self._values[k - 1] if k > 0 else 0.0

    def over(self, index: pd.DatetimeIndex) -> np.ndarray:
        """`at` for every bar of an index at once (the training path)."""
        if not self._times:
            return np.zeros(len(index))
        times = np.array([t.timestamp() for t in self._times])
        if index.tz is None:
            index = index.tz_localize("UTC")
        # as_unit: pandas 3 may hold microseconds, and asi8 counts in the unit held.
        bars = index.tz_convert("UTC").as_unit("ns").asi8 / 1e9
        k = np.searchsorted(times, bars, side="right")
        values = np.asarray(self._values)
        return np.where(k > 0, values[np.maximum(k - 1, 0)], 0.0)


def load_sources(paths: dict[str, str | None]) -> dict[str, PointInTimeSeries]:
    unknown = set(paths) - set(SOURCES)
    if unknown:
        raise ConfigurationError(f"unknown series {sorted(unknown)}; expected {SOURCES}")
    return {name: PointInTimeSeries(paths.get(name)) for name in SOURCES}


def build_frame(
    bars: pd.DataFrame, sources: dict[str, PointInTimeSeries], group: str
) -> pd.DataFrame:
    """Every bar's row, for TimeSeriesDataSet: time_idx (consecutive bar
    number), group, the target and both covariate groups. The same
    definitions CovariateRing rows are built from."""
    close = bars["close"].astype(float)
    if (close <= 0).any():
        raise ConfigurationError("bars contain a non-positive close")
    index = pd.DatetimeIndex(bars.index)
    log_close = np.log(close.to_numpy())
    ret_1 = np.zeros_like(log_close)
    ret_1[1:] = np.diff(log_close)
    ret_2 = np.zeros_like(log_close)
    ret_2[1:] = ret_1[:-1]
    frame = pd.DataFrame(
        {
            "time_idx": np.arange(len(bars), dtype=np.int64),
            "group": group,
            TARGET: log_close,
            "ret_1": ret_1,
            "ret_2": ret_2,
        },
        index=index,
    )
    for name in SOURCES:
        frame[name] = sources[name].over(index)
    frame = frame.join(known_frame(index))
    frame["timestamp"] = index
    return frame.reset_index(drop=True)


class CovariateRing:
    """The last `capacity` rows of ROW, pre-allocated; O(1) per push."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ConfigurationError(f"capacity must be >= 1, got {capacity}")
        self.capacity = capacity
        self._buf = np.zeros((capacity, len(ROW)), dtype=np.float64)
        self._next = 0
        self.count = 0
        self._prev_log: float | None = None
        self._prev_ret = 0.0

    @property
    def full(self) -> bool:
        return self.count >= self.capacity

    def push_bar(self, ts, close: float, sources: dict[str, PointInTimeSeries]) -> None:
        """Append the completed bar opening at `ts` with this close."""
        if close <= 0:
            return
        log_close = math.log(close)
        ret_1 = 0.0 if self._prev_log is None else log_close - self._prev_log
        ret_2 = self._prev_ret if self._prev_log is not None else 0.0
        row = self._buf[self._next]
        row[0] = log_close
        row[1] = ret_1
        row[2] = ret_2
        row[3] = sources["s_macro"].at(ts)
        row[4] = sources["s_earnings"].at(ts)
        row[5] = sources["s_news"].at(ts)
        row[6], row[7], row[8] = known_at(ts)
        self._next = (self._next + 1) % self.capacity
        self.count += 1
        self._prev_log = log_close
        self._prev_ret = ret_1

    def window(self) -> np.ndarray:
        """The rows in chronological order (a copy; oldest first)."""
        if not self.full:
            return self._buf[: self.count].copy()
        return np.concatenate([self._buf[self._next :], self._buf[: self._next]])

    @property
    def last_log_close(self) -> float | None:
        return self._prev_log


__all__ = [
    "KNOWN",
    "OBSERVED",
    "ROW",
    "SOURCES",
    "TARGET",
    "CovariateRing",
    "PointInTimeSeries",
    "build_frame",
    "future_bar_times",
    "known_at",
    "known_frame",
    "load_sources",
]
