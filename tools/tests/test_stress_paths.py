"""tools/stress_paths.py: each bear deeper than 2022's leaves the bars before
the peak alone, falls as far as it says, and hands the real bars after it
on at the price it left -- with the `twice` copy on the right weekdays and
session minutes."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools import stress_paths as sp

# The copy of this bear, and everything after it, crosses the end of
# daylight saving (2021-11-07).
PEAK, TROUGH = "2021-09-01", "2021-10-15"


def _ts(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz=sp.TZ).tz_convert("UTC")


def _bars() -> pd.DataFrame:
    """Two bars a session (09:30 and 15:59 New York): up to PEAK, down 60%
    to TROUGH, then up again."""
    days = pd.bdate_range("2020-01-02", "2022-03-31")
    peak, trough = pd.Timestamp(PEAK), pd.Timestamp(TROUGH)

    def level(d):
        top = 100.0 * (1 + 0.001 * (min(d, peak) - days[0]).days)
        if d <= peak:
            return top
        if d <= trough:
            return top * 0.4 ** ((d - peak).days / (trough - peak).days)
        return top * 0.4 * (1 + 0.002 * (d - trough).days)

    stamps, close = [], []
    for d in days:
        for hm, wiggle in (("09:30", 1.001), ("15:59", 1.0)):
            stamps.append(_ts(f"{d.date()} {hm}"))
            close.append(level(d) * wiggle)
    close = np.array(close)
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.997,
            "close": close,
            "volume": 1000,
        },
        index=pd.DatetimeIndex(stamps),
    )


def _closes(bars):
    day = bars.index.tz_convert(sp.TZ).tz_localize(None).normalize()
    return pd.Series(bars["close"].to_numpy(), index=day).groupby(level=0).last()


def _left(bars) -> float:
    """The deepest close as a share of the peak before it."""
    c = _closes(bars)
    return float((c / c.cummax()).min())


def test_history_is_untouched_and_an_unknown_scenario_is_refused():
    bars = _bars()
    assert sp.stressed(bars, None) is bars
    with pytest.raises(ValueError, match="unknown stress"):
        sp.stressed(bars, "worse")


def test_deeper_raises_the_bears_fall_to_its_power_and_keeps_what_follows():
    bars = _bars()
    out = sp.deeper(bars, 1.5, PEAK, TROUGH)
    before = out.index <= _ts(f"{PEAK} 16:00")
    pd.testing.assert_frame_equal(out[before], bars[before])
    assert _left(bars) == pytest.approx(0.4)
    assert _left(out) == pytest.approx(0.4**1.5)
    after = out.index > _ts(f"{TROUGH} 16:00")
    ratio = out["close"][after] / bars["close"][after]
    assert np.allclose(ratio, 0.4**1.5 / 0.4)  # the recovery's moves, from a lower base
    assert (out["high"] >= out["low"]).all()


def test_grind_falls_as_far_as_asked_with_each_bars_own_range_unchanged():
    bars = _bars()
    out = sp.grind(bars, 0.8, PEAK, TROUGH)
    assert _left(out) == pytest.approx(0.2)
    assert np.allclose(out["high"] / out["low"], bars["high"] / bars["low"])
    after = out.index > _ts(f"{TROUGH} 16:00")
    assert np.allclose(out["close"][after] / bars["close"][after], 0.2 / 0.4)
    with pytest.raises(ValueError, match="already falls"):
        sp.grind(bars, 0.5, PEAK, TROUGH)


def test_twice_repeats_the_bear_from_where_it_ended_on_the_same_weekdays_and_minutes():
    bars = _bars()
    shift = sp.twice_shift_days(bars, PEAK, TROUGH)
    assert shift == 49  # 2021-09-02..2021-10-15 rounded up to whole weeks
    out = sp.twice(bars, PEAK, TROUGH)
    assert out.index.is_monotonic_increasing and out.index.is_unique

    first = _ts("2021-09-02 09:30")
    copy_first = _ts(f"{(pd.Timestamp('2021-09-02') + pd.Timedelta(days=shift)).date()} 09:30")
    seg_close = bars.loc[_ts("2021-10-20 15:59"), "close"]  # the last bar before the copy
    peak_close = bars.loc[_ts(f"{PEAK} 15:59"), "close"]
    factor = seg_close / peak_close
    assert out.loc[copy_first, "close"] == pytest.approx(bars.loc[first, "close"] * factor)
    assert _left(out) == pytest.approx(0.4 * factor)
    copied = (bars.index > _ts(f"{PEAK} 16:00")) & (bars.index < copy_first)
    assert len(out) == len(bars) + int(copied.sum())

    ny = out.index.tz_convert(sp.TZ)
    assert set(zip(ny.hour, ny.minute, strict=True)) == {(9, 30), (15, 59)}  # across the DST end
    assert set(ny.dayofweek) <= {0, 1, 2, 3, 4}
    later = out.loc[_ts("2022-01-03 09:30") :]
    assert later["close"].iloc[0] == pytest.approx(
        bars.loc[_ts("2021-11-15 09:30"), "close"] * factor
    )  # the real 2021-11-15, seven weeks on
    assert sp.crash_window(bars, "twice", PEAK, TROUGH) == (PEAK, "2021-12-03")
    assert sp.crash_window(bars, "deeper", PEAK, TROUGH) == (PEAK, TROUGH)


def test_top_start_is_the_warmup_before_the_peak():
    bars = _bars()
    sessions = list(_closes(bars).index)
    at = sessions.index(pd.Timestamp(PEAK))
    assert sp.top_start(bars, PEAK) == str(sessions[at - sp.WARMUP_SESSIONS].date())
