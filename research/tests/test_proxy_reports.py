"""The proxy report (research/risk_overlay/proxy.py): causal -- changing any
input after a session's cutoff leaves that session's report unchanged -- and
every proxy report passes the same audit an LLM report does."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.risk_report import parse_report
from engine.core.trading_calendar import sessions_between
from research.risk_overlay.proxy import (
    as_of,
    build_archive,
    cutoff,
    read_at,
    regime,
    volatility_state,
)

SESSIONS = sessions_between(date(2024, 1, 1), date(2025, 6, 30))


def _series(
    rng: np.random.Generator, level: float, spread: float, start_hour: int = 21
) -> pd.Series:
    """One reading per session, stamped the session's evening (UTC)."""
    stamps = pd.DatetimeIndex(
        [pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=start_hour) for d in SESSIONS]
    )
    values = level * np.exp(np.cumsum(rng.normal(0, spread, len(SESSIONS))))
    return pd.Series(values, index=stamps)


@pytest.fixture
def inputs():
    rng = np.random.default_rng(7)
    closes = pd.Series(
        50 * np.exp(np.cumsum(rng.normal(0, 0.03, len(SESSIONS)))),
        index=pd.DatetimeIndex(SESSIONS),
    )
    series = {
        "cboe_VXN": _series(rng, 22, 0.04),
        "cboe_VIX": _series(rng, 17, 0.04),
        "cboe_VIX9D": _series(rng, 16, 0.05),
        "cboe_VIX3M": _series(rng, 19, 0.03),
        "cboe_VIX6M": _series(rng, 21, 0.02),
        "cboe_SKEW": _series(rng, 135, 0.01),
        "yahoo_QQQ": _series(rng, 400, 0.012),
    }
    return closes, series


def test_every_proxy_report_passes_the_audit(inputs):
    closes, series = inputs
    entries = build_archive("TQQQ", closes, series, SESSIONS[300:340])
    assert len(entries) == 40
    for entry in entries:
        audit = parse_report(entry["report"])
        assert audit.ok, (entry["session"], [f"{f.where}: {f.message}" for f in audit.errors])
        report = audit.require()
        assert report.session.isoformat() == entry["session"]
        assert min(h.bin_coverage for h in report.horizons.values()) > 0.9, (
            "bins scaled to the fund"
        )
        assert entry["inputs"]["implied_move_pct"] > 0


def test_it_reads_nothing_after_the_cutoff(inputs):
    closes, series = inputs
    session = SESSIONS[320]
    before = build_archive("TQQQ", closes, series, [session])[0]["report"]
    later = pd.Timestamp(cutoff(session))
    poisoned_closes = closes.copy()
    poisoned_closes[poisoned_closes.index >= pd.Timestamp(session)] *= 3.0
    poisoned = {k: s.where(s.index < later, s * 5.0) for k, s in series.items()}
    after = build_archive("TQQQ", poisoned_closes, poisoned, [session])[0]["report"]
    assert after == before


def test_a_stale_reading_is_missing():
    stamps = pd.DatetimeIndex([pd.Timestamp("2025-01-02 21:00", tz="UTC")])
    series = pd.Series([20.0], index=stamps)
    assert read_at(series, date(2025, 1, 3)) == 20.0
    assert read_at(series, date(2025, 1, 3) + timedelta(days=10)) is None


def test_its_stamp_is_an_end_of_day_report_for_the_session():
    from engine.core.risk_report import target_session

    for session in SESSIONS[:30]:
        assert target_session(as_of(session)) == session


def test_the_categorical_rules():
    assert volatility_state(0.1) == "compressed" and volatility_state(0.97) == "extreme"
    rising = list(np.linspace(100, 120, 60))
    falling = list(np.linspace(120, 100, 60))
    assert regime(rising, "normal", fomc=False) == "low_vol_uptrend"
    assert regime(falling, "extreme", fomc=False) == "high_vol_downtrend"
    assert regime(falling, "extreme", fomc=True) == "high_vol_downtrend"
    assert regime(rising, "normal", fomc=True) == "event_driven"
