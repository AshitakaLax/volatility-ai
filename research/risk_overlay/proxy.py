"""
The proxy report: the nightly risk report's schema, built causally from data
we already hold -- a quant twin of the LLM (docs/daily_risk_report_plan.md,
"The proxy report").

It exists for three things: to design and stress-test the mappings on
fifteen years of sessions, where no LLM report exists or can honestly be
made; to set the funds' frozen baselines (baselines.py); and to be the
baseline the LLM's reports must beat.

--------------------------------------------------------------------
THE RULES (proxy v1, frozen with mapping v1)

  expected_1d_move_pct   the implied move (leverage x the options index /
                         sqrt(252): 3 x VXN for TQQQ) blended equally with the
                         fund's realised volatility over its last 10 sessions
                         (inputs.proxy_move -- the same function the trader's
                         cross-check uses)
  1-day quantiles, ES5   a Student-t with unit variance scaled to that move,
                         on log returns: nu from the fund's trailing 252-session
                         excess kurtosis (nu = 4 + 6 / k, clipped to [3, 30]);
                         the lower tail widened and the upper narrowed by up
                         to 20% as CBOE SKEW's 252-session percentile rises
  21- and 63-session     the options index's 30-day implied volatility scaled
                         to the horizon, x leverage, with the same tails; for
                         63 sessions scaled again by the VIX term structure's
                         slope (VIX6M / VIX). 5 and 252 sessions likewise
  volatility_state       the move's percentile over 252 sessions: below 20
                         compressed, below 70 normal, below 95 elevated, else
                         extreme
  regime                 QQQ against its 50-session mean and the sign of its
                         20-session return, crossed with the volatility state;
                         event_driven on an FOMC day (unless high_vol_downtrend)
  overnight_gap_risk     high when VIX9D / VIX is above 1 or a megacap
                         earnings reaction session opens; moderate when VIX /
                         VIX3M is above 0.95; else low
  skew_bias              SKEW's 252-session percentile: above 80 bearish_tail,
                         below 20 bullish_tail, else neutral
  next_day_catalysts     FOMC decisions and megacap earnings reaction sessions
                         from the engine's calendars (a CPI, payrolls or UMich
                         calendar does not exist yet -- a known gap)
  data_quality           the share of its inputs fresh at the cutoff

POINT IN TIME: a session reads every outside series as the risk governor
does -- the newest value stamped before 04:00 UTC of its own date, a reading
older than seven days counting as missing -- and the fund's closes before
the session. Changing anything after a session's cutoff leaves its report
unchanged (research/tests/test_proxy_reports.py).

The bins are the plan's prompt change 1: scaled to the fund, so they hold
the distribution (ten bins of 0.6 sigma either side of zero) and the audit
can check them.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from typing import Any

import numpy as np
import pandas as pd

from engine.core.trading_calendar import EASTERN, previous_session
from research.risk_overlay.inputs import (
    IMPLIED_INDEX,
    MAX_AGE_DAYS,
    SESSION_CUTOFF_UTC,
    calendar_catalysts,
    proxy_move,
    realised_sigma_pct,
)

PROXY_VERSION = "proxy-v1"
SERIES = (
    "cboe_VXN",
    "cboe_VIX",
    "cboe_VIX9D",
    "cboe_VIX3M",
    "cboe_VIX6M",
    "cboe_SKEW",
    "yahoo_QQQ",
)
HORIZON_DAYS = {
    "tomorrow": 1,
    "next_week": 5,
    "next_month": 21,
    "next_quarter": 63,
    "next_year": 252,
}
LABELS = {
    "tomorrow": "Tomorrow (1D)",
    "next_week": "Next Week (5D)",
    "next_month": "Next Month (21D)",
    "next_quarter": "Next Quarter (63D)",
    "next_year": "Next Year (252D)",
}
LEVELS = {"p01": 0.01, "p05": 0.05, "p25": 0.25, "p75": 0.75, "p95": 0.95, "p99": 0.99}
BINS_EACH_SIDE = 5
BIN_SIGMAS = 0.6
WINDOW = 252
SKEW_TILT = 0.4  # +-20% at the percentile's extremes


@dataclass(frozen=True)
class Readings:
    """What one session's proxy reads: each series' value at the cutoff
    (None when missing or stale), and the fund's and QQQ's histories before
    the session."""

    session: date
    values: Mapping[str, float | None]
    closes: Sequence[float]  # the fund's daily closes, before the session
    qqq: Sequence[float]  # QQQ's daily closes, readable at the cutoff
    vol_history: Sequence[float] = field(default_factory=tuple)  # past proxy moves
    skew_history: Sequence[float] = field(default_factory=tuple)  # past SKEW readings


def cutoff(session: date) -> datetime:
    return datetime.combine(session, time(SESSION_CUTOFF_UTC), tzinfo=UTC)


def as_of(session: date) -> datetime:
    """The proxy's stamp: 21:00 Eastern the evening before -- an end-of-day
    report for `session`."""
    return datetime.combine(previous_session(session), time(21, 0), tzinfo=EASTERN).astimezone(UTC)


def read_at(series: pd.Series, session: date) -> float | None:
    """The newest value stamped before the session's cutoff, if fresh."""
    end = cutoff(session)
    idx = series.index.searchsorted(pd.Timestamp(end), side="left")
    if idx == 0:
        return None
    stamp = series.index[idx - 1]
    if pd.Timestamp(end) - stamp > pd.Timedelta(days=MAX_AGE_DAYS):
        return None
    value = float(series.iloc[idx - 1])
    return value if math.isfinite(value) else None


def _percentile(history: Sequence[float], value: float) -> float | None:
    window = [v for v in history[-WINDOW:] if v is not None and math.isfinite(v)]
    if len(window) < 60:
        return None
    return sum(1 for v in window if v <= value) / len(window)


def _nu(closes: Sequence[float]) -> float:
    returns = np.diff(np.log(np.asarray(closes[-(WINDOW + 1) :], dtype=float)))
    if len(returns) < 60:
        return 8.0
    centred = returns - returns.mean()
    var = float(np.mean(centred**2))
    if var <= 0:
        return 30.0
    kurtosis = float(np.mean(centred**4)) / var**2 - 3.0
    return float(np.clip(4.0 + 6.0 / kurtosis, 3.0, 30.0)) if kurtosis > 0 else 30.0


class _Tails:
    """A unit-variance Student-t, its lower and upper halves tilted by SKEW.
    Its quantiles do not depend on a horizon's sigma, so the grids the
    moments and the shortfall are taken over are computed once a session."""

    GRID = np.linspace(0.0005, 0.9995, 2000)
    TAIL = np.linspace(0.05 / 400.0, 0.05, 400)

    def __init__(self, nu: float, tilt: float) -> None:
        from scipy import stats

        self.nu = nu
        self.scale = math.sqrt((nu - 2.0) / nu)
        self.dist = stats.t(df=nu)
        self.lower = 1.0 + tilt
        self.upper = 1.0 - tilt
        self.grid_z = self.zs(self.GRID)
        self.tail_z = self.zs(self.TAIL)
        self.level_z = dict(zip(LEVELS, self.zs(np.array(list(LEVELS.values()))), strict=True))
        self.median_z = float(self.zs(np.array([0.5]))[0])

    def zs(self, ps: np.ndarray) -> np.ndarray:
        z = self.dist.ppf(ps) * self.scale
        return np.where(z < 0, z * self.lower, z * self.upper)

    def cdf(self, z: float) -> float:
        stretch = self.lower if z < 0 else self.upper
        return float(self.dist.cdf(z / stretch / self.scale))

    def moments(self, sigma: float) -> tuple[float, float]:
        values = np.expm1(sigma * self.grid_z)
        return float(values.mean()) * 100.0, float(values.std()) * 100.0

    def es(self, sigma: float) -> float:
        """E[exp(sigma z) - 1 | z <= z_0.05], in percent."""
        return float(np.mean(np.expm1(sigma * self.tail_z))) * 100.0


def _horizon(name: str, sigma: float, tails: _Tails) -> dict[str, Any]:
    """One horizon in the schema, from its log-return sigma (a fraction)."""

    def pct(z: float) -> float:
        return round(float(math.expm1(sigma * z)) * 100.0, 4)

    quantiles = {key: pct(z) for key, z in tails.level_z.items()}
    width = BIN_SIGMAS
    edges = [k * width for k in range(-BINS_EACH_SIDE, BINS_EACH_SIDE + 1)]
    cdfs = [tails.cdf(z) for z in edges]
    under = round(cdfs[0], 4)
    bins, running = [], under
    for i in range(len(edges) - 1):
        prob = round(cdfs[i + 1] - cdfs[i], 4)
        running = round(running + prob, 4)
        low, high = pct(edges[i]), pct(edges[i + 1])
        if abs(edges[i + 1]) < 1e-12:
            high = 0.0
        if abs(edges[i]) < 1e-12:
            low = 0.0
        bins.append({"min_pct": low, "max_pct": high, "prob": prob, "cdf": running})
    over = round(1.0 - running, 4)
    zero_cdf = next(b["cdf"] for b in bins if b["max_pct"] == 0.0)
    median = pct(tails.median_z)
    mean, std = (round(x, 4) for x in tails.moments(sigma))
    es5 = round(min(tails.es(sigma), quantiles["p05"]), 4)
    return {
        "label": LABELS[name],
        "trading_days": HORIZON_DAYS[name],
        "bin_width_pct": round(width * sigma * 100, 4),
        "underflow_prob": under,
        "overflow_prob": over,
        "bins": bins,
        "summary": {
            "mean_pct": mean,
            "median_pct": min(max(median, quantiles["p25"]), quantiles["p75"]),
            "std_pct": max(std, 1e-4),
            "prob_positive": round(1.0 - zero_cdf, 4),
            "expected_shortfall_5pct": es5,
            "quantiles_pct": quantiles,
        },
    }


def volatility_state(percentile: float | None) -> str:
    if percentile is None:
        return "normal"
    if percentile < 0.20:
        return "compressed"
    if percentile < 0.70:
        return "normal"
    if percentile < 0.95:
        return "elevated"
    return "extreme"


def regime(qqq: Sequence[float], state: str, fomc: bool) -> str:
    calm = state in ("compressed", "normal")
    if len(qqq) < 51:
        out = "mean_reverting_range"
    else:
        above = qqq[-1] > float(np.mean(qqq[-50:]))
        rising = qqq[-1] > qqq[-21]
        if not above and not rising and not calm:
            out = "high_vol_downtrend"
        elif above and rising and calm:
            out = "low_vol_uptrend"
        elif not calm and (above or rising):
            out = "breakout_expansion"
        else:
            out = "mean_reverting_range"
    if fomc and out != "high_vol_downtrend":
        return "event_driven"
    return out


def build_report(symbol: str, readings: Readings) -> tuple[dict[str, Any], dict[str, Any]]:
    """(the proxy report for `readings.session`, the inputs it was built
    with). The report passes engine/core/risk_report.parse_report."""
    session = readings.session
    v = readings.values
    key, leverage = IMPLIED_INDEX.get(symbol.upper(), ("cboe_VIX", 1.0))
    index = v.get(key)
    implied = leverage * index / math.sqrt(252.0) if index else None
    realised = realised_sigma_pct(readings.closes)
    move = proxy_move(implied, realised) or 1.0
    move_pct_history = [*readings.vol_history, move]
    state = volatility_state(_percentile(move_pct_history[:-1], move))
    catalysts = calendar_catalysts(session, live=False)
    fomc = any("FOMC" in c.event for c in catalysts)
    reaction = any("earnings" in c.event for c in catalysts)
    vix, vix9d, vix3m, vix6m = (
        v.get("cboe_VIX"),
        v.get("cboe_VIX9D"),
        v.get("cboe_VIX3M"),
        v.get("cboe_VIX6M"),
    )
    if (vix and vix9d and vix9d / vix > 1.0) or reaction:
        gap = "high"
    elif vix and vix3m and vix / vix3m > 0.95:
        gap = "moderate"
    else:
        gap = "low"
    skew = v.get("cboe_SKEW")
    skew_pct = _percentile(readings.skew_history, skew) if skew else None
    if skew_pct is None:
        bias, tilt = "neutral", 0.0
    else:
        bias = (
            "bearish_tail" if skew_pct > 0.80 else "bullish_tail" if skew_pct < 0.20 else "neutral"
        )
        tilt = SKEW_TILT * (skew_pct - 0.5)
    tails = _Tails(_nu(readings.closes), tilt)
    term = (vix6m / vix) if vix and vix6m else 1.0
    sigmas = {"tomorrow": move / 100.0}
    longer = (leverage * index / 100.0) if index else move / 100.0 * math.sqrt(252.0)
    for name, days in HORIZON_DAYS.items():
        if name == "tomorrow":
            continue
        scale = term if days >= 63 else 1.0
        sigmas[name] = longer * scale * math.sqrt(days / 252.0)
    fresh = sum(1 for k in SERIES if v.get(k) is not None)
    confidence = round(fresh / len(SERIES), 4)
    missing = [k for k in SERIES if v.get(k) is None]
    coverage = (
        "primary_verified" if not missing else ("degraded" if confidence < 0.6 else "partial")
    )
    report = {
        "schema_version": "1.2.0",
        "symbol": symbol.upper(),
        "as_of": as_of(session).isoformat().replace("+00:00", "Z"),
        "target_session": session.isoformat(),
        "prompt_version": PROXY_VERSION,
        "model": "proxy",
        "base_price": round(float(readings.closes[-1]), 4) if readings.closes else 1.0,
        "return_type": "simple_pct",
        "execution_signals": {
            "data_quality": {
                "confidence_score": confidence,
                "source_coverage": coverage,
                "missing_inputs": missing,
            },
            "regime": regime(readings.qqq, state, fomc),
            "volatility_state": state,
            "implied_vs_realized_vol_spread_pct": (
                round(implied - realised, 4)
                if implied is not None and realised is not None
                else None
            ),
            "expected_1d_move_pct": round(move, 4),
            "skew_bias": bias,
            "overnight_gap_risk": gap,
            "next_day_catalysts": [
                {
                    "time_utc": c.at.isoformat().replace("+00:00", "Z") if c.at else None,
                    "event": c.event,
                    "impact": c.impact,
                }
                for c in catalysts
            ],
        },
        "horizons": {name: _horizon(name, sigmas[name], tails) for name in HORIZON_DAYS},
    }
    if report["execution_signals"]["implied_vs_realized_vol_spread_pct"] is None:
        del report["execution_signals"]["implied_vs_realized_vol_spread_pct"]
    inputs = {
        "implied_move_pct": implied,
        "implied_source": f"{key.split('_', 1)[1]} {index:.2f}" if index else None,
        "proxy_move_pct": move,
        "last_close": float(readings.closes[-1]) if readings.closes else None,
        "calendar": [c.to_dict() for c in catalysts],
    }
    return report, inputs


def daily_closes(bars: pd.DataFrame) -> pd.Series:
    """The fund's regular-session closes by Eastern date."""
    ny = bars.index.tz_convert(EASTERN)
    minutes = ny.hour * 60 + ny.minute
    keep = (minutes >= 570) & (minutes < 960)
    closes = bars["close"][keep]
    days = pd.DatetimeIndex(closes.index.tz_convert(EASTERN).date)
    return pd.Series(closes.to_numpy(float), index=days).groupby(level=0).last()


def build_archive(
    symbol: str,
    closes: pd.Series,
    series: Mapping[str, pd.Series],
    sessions: Sequence[date],
) -> list[dict[str, Any]]:
    """A proxy archive entry for each of `sessions` (archive.py's format)."""
    from engine.core.risk_report import report_sha256

    close_days = np.array(
        [(d.date() if hasattr(d, "date") else d) for d in closes.index], dtype="datetime64[D]"
    )
    close_values = closes.to_numpy(float)
    qqq = series.get("yahoo_QQQ")
    entries, vol_history, skew_history = [], [], []
    for session in sessions:
        n = int(np.searchsorted(close_days, np.datetime64(session), side="left"))
        if n < 12:
            continue
        values = {
            key: (read_at(s, session) if s is not None else None) for key, s in series.items()
        }
        qqq_closes = []
        if qqq is not None:
            end = qqq.index.searchsorted(pd.Timestamp(cutoff(session)), side="left")
            qqq_closes = qqq.iloc[max(0, end - 60) : end].to_numpy(float).tolist()
        readings = Readings(
            session=session,
            values=values,
            closes=close_values[max(0, n - WINDOW - 1) : n].tolist(),
            qqq=qqq_closes,
            vol_history=tuple(vol_history[-WINDOW:]),
            skew_history=tuple(skew_history[-WINDOW:]),
        )
        report, inputs = build_report(symbol, readings)
        vol_history.append(report["execution_signals"]["expected_1d_move_pct"])
        if values.get("cboe_SKEW") is not None:
            skew_history.append(values["cboe_SKEW"])
        received = as_of(session)
        entries.append(
            {
                "session": session.isoformat(),
                "source": "proxy",
                "received_at": received.isoformat(),
                "prompt_version": PROXY_VERSION,
                "model": "proxy",
                "sha256": report_sha256(report),
                "report": report,
                "inputs": inputs,
            }
        )
    return entries


__all__ = [
    "PROXY_VERSION",
    "SERIES",
    "Readings",
    "as_of",
    "build_archive",
    "build_report",
    "cutoff",
    "daily_closes",
    "read_at",
    "regime",
    "volatility_state",
]
