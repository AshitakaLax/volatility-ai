"""
Bear markets deeper than 2022's, built from a fund's own minute bars, for
asking what a book does when the next bear is worse than the worst one in the
warehouse.

TQQQ's 2022 bear -- the close of 2021-11-19 to the close of 2022-12-28,
-81.7% -- is the deepest it has had since 2016. Each scenario rebuilds the
bars around it. Everything up to the peak is untouched, and after the bear
the real bars continue from wherever the scenario left the price:

  deeper   every bar's log move inside the bear x1.5: the same path, half
           again as violent, bottoming at -92%. A 3x fund in a 2008 or
           2000-02 bear falls about that far.
  grind    the same bars with a steady extra fall, bottoming at -95%. Each
           bar's own range is 2022's, so a volatility regime reads the slide
           as no worse than 2022 while it goes further.
  twice    the bear, then the bear again from its trough (-96.5% in all),
           then the real 2023 on: two years of 2022 back to back. The copy
           and everything after it move whole weeks, so weekdays and session
           minutes line up.
  fast     not 2022 but the 2020 crash (2020-02-19 to 2020-03-20, -69.9%)
           made `deeper` the same way: -83.5% in a month, past 2022's fall
           in a twelfth of the time. A regime read from daily volatility
           is slowest to turn on a crash like this one.

Not a price change, but the same question (`top_start`): an account that
opens at the 2021 peak, its bars starting WARMUP_SESSIONS before so the
regime is warm when the bear begins, has no profit cushion when it does.

Calendar-keyed inputs (event and earnings days) do not move with the `twice`
copy: those days are mislabelled for its length, which shifts a few lots'
size and nothing else.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

TZ = "America/New_York"
PRICE_COLUMNS = ("open", "high", "low", "close")

# TQQQ's deepest bear in the warehouse (regular-session closes).
BEAR_PEAK = "2021-11-19"
BEAR_TROUGH = "2022-12-28"
# TQQQ's fastest crash.
CRASH_PEAK = "2020-02-19"
CRASH_TROUGH = "2020-03-20"
DEEPER_FACTOR = 1.5
GRIND_FALL = 0.95
# The Ultimate family buys nothing until its 250-session bear window fills.
WARMUP_SESSIONS = 252

SCENARIOS = ("deeper", "grind", "twice", "fast")


def _day(bars: pd.DataFrame) -> pd.DatetimeIndex:
    return bars.index.tz_convert(TZ).tz_localize(None).normalize()


def _bear_bounds(bars: pd.DataFrame, peak: str, trough: str) -> tuple[int, int]:
    """Positions of the last bar of the peak session and of the trough
    session."""
    day = _day(bars)
    a = int(np.searchsorted(day, pd.Timestamp(peak), side="right")) - 1
    b = int(np.searchsorted(day, pd.Timestamp(trough), side="right")) - 1
    if a < 0 or b <= a:
        raise ValueError(f"bars do not cover the bear {peak}..{trough}")
    return a, b


def _scaled(bars: pd.DataFrame, factor: np.ndarray) -> pd.DataFrame:
    out = bars.copy()
    for col in PRICE_COLUMNS:
        out[col] = bars[col].to_numpy(float) * factor
    return out


def deeper(
    bars: pd.DataFrame,
    factor: float = DEEPER_FACTOR,
    peak: str = BEAR_PEAK,
    trough: str = BEAR_TROUGH,
) -> pd.DataFrame:
    """Every price inside the bear moved to peak x (price / peak) ** factor,
    and every later price scaled to continue from where that leaves it."""
    a, b = _bear_bounds(bars, peak, trough)
    p_peak, p_trough = float(bars["close"].iloc[a]), float(bars["close"].iloc[b])
    out = bars.copy()
    for col in PRICE_COLUMNS:
        x = bars[col].to_numpy(float).copy()
        x[a + 1 : b + 1] = p_peak * (x[a + 1 : b + 1] / p_peak) ** factor
        x[b + 1 :] *= p_peak * (p_trough / p_peak) ** factor / p_trough
        out[col] = x
    return out


def grind(
    bars: pd.DataFrame,
    fall: float = GRIND_FALL,
    peak: str = BEAR_PEAK,
    trough: str = BEAR_TROUGH,
) -> pd.DataFrame:
    """The bear's bars with an extra fall spread evenly over them, so it
    bottoms `fall` below the peak; every later price scaled to continue."""
    a, b = _bear_bounds(bars, peak, trough)
    p_peak, p_trough = float(bars["close"].iloc[a]), float(bars["close"].iloc[b])
    extra = math.log((p_trough / p_peak) / (1.0 - fall))
    if extra <= 0:
        raise ValueError(f"the bear already falls {1 - p_trough / p_peak:.1%}, past {fall:.1%}")
    factor = np.ones(len(bars))
    n = b - a
    factor[a + 1 : b + 1] = np.exp(-extra * np.arange(1, n + 1) / n)
    factor[b + 1 :] = math.exp(-extra)
    return _scaled(bars, factor)


def _shift_days(index: pd.DatetimeIndex, days: int) -> pd.DatetimeIndex:
    """Move timestamps `days` calendar days in New York time, so a bar keeps
    its session minute across a daylight-saving change."""
    local = index.tz_convert(TZ).tz_localize(None) + pd.Timedelta(days=days)
    return local.tz_localize(TZ).tz_convert(index.tz)


def twice_shift_days(bars: pd.DataFrame, peak: str = BEAR_PEAK, trough: str = BEAR_TROUGH) -> int:
    """How far `twice` moves its copy and everything after: the bear's
    length rounded up to whole weeks."""
    a, b = _bear_bounds(bars, peak, trough)
    day = _day(bars)
    first, last = day[a + 1], day[b]
    return 7 * math.ceil(((last - first).days + 1) / 7)


def twice(bars: pd.DataFrame, peak: str = BEAR_PEAK, trough: str = BEAR_TROUGH) -> pd.DataFrame:
    """The bear, then a copy of it starting where it ended, then the real
    bars after it, moved and scaled to continue from the copy."""
    a, _ = _bear_bounds(bars, peak, trough)
    shift = twice_shift_days(bars, peak, trough)
    day = _day(bars)
    seg_end = int(np.searchsorted(day, day[a + 1] + pd.Timedelta(days=shift), side="left"))
    p_peak = float(bars["close"].iloc[a])
    factor = float(bars["close"].iloc[seg_end - 1]) / p_peak
    copy = _scaled(bars.iloc[a + 1 : seg_end], np.full(seg_end - a - 1, factor))
    copy.index = _shift_days(copy.index, shift)
    later = _scaled(bars.iloc[seg_end:], np.full(len(bars) - seg_end, factor))
    later.index = _shift_days(later.index, shift)
    return pd.concat([bars.iloc[:seg_end], copy, later])


def stressed(bars: pd.DataFrame, scenario: str | None) -> pd.DataFrame:
    """`bars` under `scenario` (module docstring); None is history."""
    if scenario is None:
        return bars
    if scenario == "deeper":
        return deeper(bars)
    if scenario == "grind":
        return grind(bars)
    if scenario == "twice":
        return twice(bars)
    if scenario == "fast":
        return deeper(bars, DEEPER_FACTOR, CRASH_PEAK, CRASH_TROUGH)
    raise ValueError(f"unknown stress scenario {scenario!r}: {', '.join(SCENARIOS)}")


def crash_window(
    bars: pd.DataFrame, scenario: str | None, peak: str = BEAR_PEAK, trough: str = BEAR_TROUGH
) -> tuple[str, str]:
    """(peak session, last session of the bear) in the scenario's calendar,
    from the history `bars`."""
    if scenario == "fast":
        return CRASH_PEAK, CRASH_TROUGH
    if scenario != "twice":
        return peak, trough
    end = pd.Timestamp(trough) + pd.Timedelta(days=twice_shift_days(bars, peak, trough))
    return peak, str(end.date())


def top_start(bars: pd.DataFrame, peak: str = BEAR_PEAK) -> str:
    """The session WARMUP_SESSIONS before the peak: where an account's bars
    start for it to begin trading at the peak."""
    sessions = _day(bars).unique()
    at = int(np.searchsorted(sessions, pd.Timestamp(peak), side="right")) - 1
    return str(sessions[max(0, at - WARMUP_SESSIONS)].date())
