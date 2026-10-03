"""tools/leverage_stepdown.py: the stitch, the metrics, the plumbing."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from research.tests.test_gated_local_reference_sizing import HF_PARAMS, _minute_sessions
from tools.leverage_stepdown import SleeveFactory, run_book, stitch, summarize

INITIAL = 100_000.0


def _curve(values, start="2024-01-02 14:30", freq="1min"):
    index = pd.date_range(start, periods=len(values), freq=freq, tz="UTC")
    return pd.Series(values, index=index, dtype=float)


class TestStitch:
    def test_adds_pnl_not_equity(self):
        a = _curve([INITIAL, INITIAL + 10, INITIAL + 30])
        b = _curve([INITIAL, INITIAL - 5, INITIAL + 1])
        assert stitch(INITIAL, [a, b]).tolist() == [INITIAL, INITIAL + 5, INITIAL + 31]

    def test_misaligned_bars_hold_their_last_value(self):
        a = _curve([INITIAL, INITIAL + 10, INITIAL + 20])
        b = _curve([INITIAL + 7], start="2024-01-02 14:31")  # one bar, mid-run
        assert stitch(INITIAL, [a, b]).tolist() == [INITIAL, INITIAL + 17, INITIAL + 27]


class TestSummarize:
    def test_known_answers(self):
        # Doubles over exactly two years with a 50% dip on the way.
        index = pd.to_datetime(["2020-01-01", "2020-06-01", "2021-01-01", "2022-01-01"], utc=True)
        curve = pd.Series([100.0, 50.0, 100.0, 200.0], index=index)
        st = summarize(curve, index[0])
        assert st["total_return_pct"] == pytest.approx(100.0)
        assert st["max_dd_pct"] == pytest.approx(50.0)
        assert st["cagr_pct"] == pytest.approx((2 ** (365.25 / 731) - 1) * 100)
        # Year-end 2020 is the dip (50), so 2020 is -50% and 2021 +100%.
        assert st["annual"].to_dict() == {2020: -50.0, 2021: 100.0, 2022: 100.0}

    def test_rebases_at_the_window_start(self):
        curve = _curve([50.0, 100.0, 110.0], freq="D")
        st = summarize(curve, curve.index[1])
        assert st["total_return_pct"] == pytest.approx(10.0)


def test_two_sleeves_on_two_instruments_stitch_into_one_account():
    """The real engine, one sleeve per synthetic instrument, a regime
    that hands the middle sessions to the second sleeve."""
    cfg = BacktestConfig.from_yaml("config/best_known_2026-08-24.yaml")
    dates = [date(2024, 1, d) for d in (2, 3, 4, 5, 8, 9)]
    regime = dict(zip(dates, [True, True, False, False, True, True], strict=True))
    lev = _minute_sessions()
    unlev = lev.copy()
    unlev[["open", "high", "low", "close"]] = (
        100 + (lev[["open", "high", "low", "close"]] - 100) / 3
    )

    calm_curve, calm_row = run_book(
        lev, cfg, SleeveFactory("calm", regime), "LEV", 0.002, 0.004, dict(HF_PARAMS), 0.0
    )
    turb_curve, turb_row = run_book(
        unlev,
        cfg,
        SleeveFactory("turbulent", regime),
        "UNLEV",
        0.002 / 3,
        0.004 / 3,
        dict(HF_PARAMS),
        0.0,
    )
    assert calm_row["Strategy"] == "RegimeSleeve[calm]"
    assert calm_row["Trade Count"] > 0 and turb_row["Trade Count"] > 0

    account = stitch(INITIAL, [calm_curve, turb_curve])
    calm_pnl = calm_curve.iloc[-1] - INITIAL
    turb_pnl = turb_curve.iloc[-1] - INITIAL
    assert account.iloc[-1] == pytest.approx(INITIAL + calm_pnl + turb_pnl)

    # Each sleeve is flat while the other trades: the calm sleeve's
    # equity cannot move during the turbulent sessions after its flip bar.
    mid = calm_curve[(calm_curve.index.date > dates[2]) & (calm_curve.index.date <= dates[3])]
    assert np.ptp(mid.to_numpy()) == pytest.approx(0.0, abs=1e-6)
