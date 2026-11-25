"""
The pre-market forecast generator, ported: market data in, one risk report
out -- the same report the Live page's RiskReportPanel is pasted, in the
schema engine/core/risk_report.py parses.

This is the pipeline of github.com/AshitakaLax/pre-market-session-forecast-
report-generator (chronos_service/app.py), moved onto this repository's own
pieces: the engine's trading calendar instead of pandas_market_calendars,
research/ml/sources.py's HTTP getter instead of yfinance, and parse_report as
the audit instead of the TypeScript one.

--------------------------------------------------------------------
WHAT ONE RUN DOES

  1. The session the report is for: target_session(now). A run inside
     regular hours is refused -- the parser refuses such a report -- and so
     is one in the quarter hour after the close, while closing prints settle.
  2. Daily bars for the fund and its covariates (underlying, SPY, index
     futures, VIX, VXN, 10-year yield, dollar index, crude), every bar
     strictly BEFORE the target session. The fund's last bar must be the
     session before it, or the run is refused: a forecast anchored to an
     older close would be for the wrong day.
  3. A training frame of daily log returns (%) with covariates known at each
     close (the generator's set, each kept only with 75% coverage).
  4. Daily quantiles from the engine (model.py): Chronos-2 through its
     native horizon, extended to 252 sessions with the historical
     standardised-innovation model; or the historical baseline.
  5. 10,000 correlated paths (scenarios.py, a five-session circular block
     bootstrap), seeded by symbol and session so a rerun reproduces itself.
  6. The snapshot: what was observable at the run -- the pre-market window,
     the overnight futures change, the overnight VIX, Cboe's volatility
     closes, IV rank -- each with where and when it was read
     (input_observations). Display only: none is a model input
     (market_inputs.py's docstring says why).
  7. The report, rounded so the audit's sums hold, then parse_report's audit.

The report is the payload alone; the snapshot, sources and diagnostics travel
beside it, never inside it (MAX_REPORT_BYTES, and a report is hashed whole).

Nothing here writes anything: storing a report is
research/risk_overlay/forecasts.py's, through server/risk_forecasts.py.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from datetime import time as clock_time
from typing import Any

import numpy as np
import pandas as pd

from engine.core.risk_report import parse_report, target_session
from engine.core.trading_calendar import (
    EASTERN,
    SESSION_CLOSE,
    is_session,
    next_session,
    previous_session,
)
from research.forecast_generator import model as engines
from research.forecast_generator.market_data import (
    MarketData,
    MarketSource,
    cboe_csv_url,
    minute_closes,
)
from research.forecast_generator.market_inputs import (
    CBOE_INDEX_SOURCES,
    REGULAR_OPEN,
    choose_daily_series,
    daily_observation,
    intraday_observation,
    iv_rank_pct,
    latest_overnight_vix,
    overnight_futures_change,
    overnight_vix_window_open,
)
from research.forecast_generator.scenarios import (
    build_horizon_distributions,
    extend_daily_quantiles,
    simulate_cumulative_returns,
)

SCHEMA_VERSION = "1.2.0"  # engine/core/risk_report.py's: target_session, model, prompt_version
GENERATOR_VERSION = "forecast-generator-v1"
SIMULATIONS = max(1000, int(os.getenv("VAI_FORECAST_SIMULATIONS", "10000")))
BLOCK_LENGTH = 5
MIN_HISTORY = 300
MAX_HORIZON = 252
CLOSE_SETTLES = clock_time(16, 15)
PREMARKET_WINDOW = (clock_time(4, 0), clock_time(4, 5))  # end exclusive; fully elapsed by 04:05
SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.^=-]{0,11}$")

# Each fund's underlying, leverage, options index and index future -- the
# generator's PROFILE_MAP. An unlisted symbol forecasts as itself at 1x.
PROFILES: dict[str, dict[str, Any]] = {
    "TQQQ": {"underlying": "QQQ", "leverage": 3, "volatility": "^VXN", "futures": "NQ=F"},
    "SQQQ": {"underlying": "QQQ", "leverage": 3, "volatility": "^VXN", "futures": "NQ=F"},
    "QLD": {"underlying": "QQQ", "leverage": 2, "volatility": "^VXN", "futures": "NQ=F"},
    "QID": {"underlying": "QQQ", "leverage": 2, "volatility": "^VXN", "futures": "NQ=F"},
    "QQQ": {"underlying": "QQQ", "leverage": 1, "volatility": "^VXN", "futures": "NQ=F"},
    "UPRO": {"underlying": "SPY", "leverage": 3, "volatility": "^VIX", "futures": "ES=F"},
    "SPXL": {"underlying": "SPY", "leverage": 3, "volatility": "^VIX", "futures": "ES=F"},
    "SPXU": {"underlying": "SPY", "leverage": 3, "volatility": "^VIX", "futures": "ES=F"},
    "SSO": {"underlying": "SPY", "leverage": 2, "volatility": "^VIX", "futures": "ES=F"},
    "SPY": {"underlying": "SPY", "leverage": 1, "volatility": "^VIX", "futures": "ES=F"},
    "SOXL": {"underlying": "SOXX", "leverage": 3, "volatility": "^VXN", "futures": "NQ=F"},
    "SOXS": {"underlying": "SOXX", "leverage": 3, "volatility": "^VXN", "futures": "NQ=F"},
    "TNA": {"underlying": "IWM", "leverage": 3, "volatility": "^RVX", "futures": "RTY=F"},
}

# key, label, sessions, 1x bin width (%). Widths scale with leverage (the
# generator's leveraged_scaled template).
HORIZON_SPECS: tuple[tuple[str, str, int, float], ...] = (
    ("tomorrow", "Tomorrow (1D)", 1, 0.5),
    ("next_week", "Next Week (5D)", 5, 1.0),
    ("next_month", "Next Month (21D)", 21, 2.0),
    ("next_quarter", "Next Quarter (63D)", 63, 3.0),
    ("next_year", "Next Year (252D)", 252, 5.0),
)

Progress = Callable[[str], None]


class ForecastRefused(ValueError):
    """The run cannot make an honest report now; the message says why."""


@dataclass(frozen=True)
class Generated:
    """One run's report and everything shown beside it."""

    report: dict[str, Any]
    audit: dict[str, Any]
    snapshot: dict[str, Any]
    sources: list[dict[str, str]]
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report,
            "audit": self.audit,
            "snapshot": self.snapshot,
            "sources": self.sources,
            "diagnostics": self.diagnostics,
        }


def profile_for(symbol: str) -> dict[str, Any]:
    return PROFILES.get(
        symbol, {"underlying": symbol, "leverage": 1, "volatility": "^VIX", "futures": "ES=F"}
    )


def horizon_specs(leverage: float) -> list[dict[str, Any]]:
    specs = []
    for key, label, days, width in HORIZON_SPECS:
        scaled = round(width * max(1.0, float(leverage)), 2)
        bins = [
            {"min_pct": round(i * scaled, 2), "max_pct": round((i + 1) * scaled, 2)}
            for i in range(-5, 5)
        ]
        specs.append(
            {
                "key": key,
                "label": label,
                "trading_days": days,
                "bin_width_pct": scaled,
                "bins": bins,
            }
        )
    return specs


def window_check(now: datetime) -> tuple[date | None, str | None]:
    """(the session a report made now is for, or why none can be made now)."""
    try:
        session = target_session(now)
    except ValueError:
        return None, (
            "Reports are made outside regular hours: the regular session (09:30-16:00 ET) is "
            "trading, and a report stamped inside it is not for any one session."
        )
    local = now.astimezone(EASTERN)
    if is_session(local.date()) and SESSION_CLOSE <= local.time() < CLOSE_SETTLES:
        return None, "Closing prints settle until 16:15 ET; generate the evening report after that."
    return session, None


# --------------------------------------------------------------------
# Daily history


def _completed(frame: pd.DataFrame, before: date) -> pd.DataFrame:
    """Bars strictly before the target session: nothing from the day the
    report is about."""
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame.loc[frame.index < pd.Timestamp(before)]


def _close(histories: dict[str, pd.DataFrame], ticker: str) -> pd.Series | None:
    frame = histories.get(ticker)
    if frame is None or frame.empty or "Close" not in frame:
        return None
    series = frame["Close"].replace([np.inf, -np.inf], np.nan).dropna()
    return series if not series.empty else None


def _log_returns_pct(series: pd.Series) -> pd.Series:
    return np.log(series / series.shift(1)) * 100.0


def calendar_covariates(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Deterministic covariates known for every future session."""
    dates = pd.DatetimeIndex(index)
    weekday = 2.0 * np.pi * dates.day_of_week.to_numpy(dtype=float) / 5.0
    year = 2.0 * np.pi * dates.day_of_year.to_numpy(dtype=float) / 365.25
    month = 2.0 * np.pi * (dates.month.to_numpy(dtype=float) - 1.0) / 12.0
    day = 2.0 * np.pi * (dates.day.to_numpy(dtype=float) - 1.0) / 31.0
    return pd.DataFrame(
        {
            "calendar_weekday_sin": np.sin(weekday),
            "calendar_weekday_cos": np.cos(weekday),
            "calendar_year_sin": np.sin(year),
            "calendar_year_cos": np.cos(year),
            "calendar_month_sin": np.sin(month),
            "calendar_month_cos": np.cos(month),
            "calendar_day_sin": np.sin(day),
            "calendar_day_cos": np.cos(day),
        },
        index=dates,
    )


def future_sessions(after: date, count: int) -> pd.DatetimeIndex:
    days, day = [], after
    for _ in range(count):
        day = next_session(day)
        days.append(pd.Timestamp(day))
    return pd.DatetimeIndex(days)


def training_frame(
    symbol: str,
    profile: dict[str, Any],
    histories: dict[str, pd.DataFrame],
    target: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    """The generator's frame: the target's daily log return (%) and every
    covariate known at each close, each kept only with 75% coverage."""
    close = target["Close"].astype(float)
    returns = _log_returns_pct(close)
    frame = pd.DataFrame({"target": returns}, index=target.index)
    missing: dict[str, str] = {}
    candidates: dict[str, pd.Series] = {}

    for ticker, name in (
        (str(profile["underlying"]), "underlying_return_pct"),
        ("SPY", "spy_return_pct"),
        (str(profile["futures"]), "index_futures_return_pct"),
    ):
        if ticker == symbol or name in candidates:
            continue
        series = _close(histories, ticker)
        if series is not None:
            candidates[name] = _log_returns_pct(series).reindex(frame.index)
        else:
            missing[name] = f"{ticker} history unavailable"

    seen: set[str] = set()
    for ticker, name in (
        ("^VIX", "vix_level"),
        (str(profile["volatility"]), "primary_volatility_index"),
    ):
        if ticker == symbol or ticker in seen:
            continue
        seen.add(ticker)
        series = _close(histories, ticker)
        if series is not None:
            candidates[name] = series.reindex(frame.index) / 100.0
        else:
            missing[name] = f"{ticker} history unavailable"

    for name, series in calendar_covariates(pd.DatetimeIndex(frame.index)).items():
        candidates[name] = series

    for ticker, name in (
        ("^TNX", "us_10y_yield_level"),
        ("DX-Y.NYB", "dxy_return_pct"),
        ("CL=F", "wti_return_pct"),
    ):
        series = _close(histories, ticker)
        if series is None:
            missing[name] = f"{ticker} history unavailable"
        elif ticker == "^TNX":
            candidates[name] = (series / 10.0).reindex(frame.index)
        else:
            candidates[name] = _log_returns_pct(series).reindex(frame.index)

    candidates["realized_volatility_20d"] = returns.rolling(20).std() * np.sqrt(252)
    candidates["momentum_5d_pct"] = returns.rolling(5).sum()
    candidates["momentum_20d_pct"] = returns.rolling(20).sum()
    previous = close.shift(1)
    if "Open" in target:
        candidates["overnight_gap_pct"] = np.log(target["Open"].astype(float) / previous) * 100.0
    if {"High", "Low"}.issubset(target.columns):
        candidates["intraday_range_pct"] = (
            (target["High"].astype(float) - target["Low"].astype(float)) / previous * 100.0
        )
    if "Volume" in target:
        volume = target["Volume"].astype(float).replace(0, np.nan)
        candidates["volume_surprise_log"] = np.log(volume / volume.rolling(20).mean())

    included: list[str] = []
    for name, series in candidates.items():
        aligned = series.reindex(frame.index).replace([np.inf, -np.inf], np.nan)
        coverage = float(aligned.notna().mean())
        if coverage < 0.75:
            missing[name] = f"only {coverage:.0%} historical coverage"
            continue
        frame[name] = aligned.ffill(limit=5)
        included.append(name)

    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) > engines.CONTEXT_LENGTH:
        frame = frame.tail(engines.CONTEXT_LENGTH)
    return frame, included, missing


# --------------------------------------------------------------------
# The snapshot


def _premarket(
    data: MarketSource, symbol: str, now_et: datetime, session: date, previous_close: float
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]], list[str]]:
    """The fund's own pre-market tape, on a pre-market run of the target
    session. An evening run has none to read, and reports none missing."""
    start, end = PREMARKET_WINDOW
    out: dict[str, Any] = {
        "pre_market_or_latest_price": None,
        "pre_market_change_pct": None,
        "premarket_window_start_et": start.strftime("%H:%M"),
        "premarket_window_end_et": end.strftime("%H:%M"),
        "premarket_open_4am": None,
        "premarket_window_high": None,
        "premarket_window_low": None,
        "premarket_window_change_pct": None,
        "premarket_window_volume": None,
    }
    missing: list[str] = []
    observations: list[dict[str, Any]] = []
    notes: list[str] = []
    pre_market_run = now_et.date() == session and start <= now_et.time() < REGULAR_OPEN
    if not pre_market_run:
        return out, missing, observations, notes
    try:
        frame = data.minutes(symbol)
    except Exception as exc:
        frame = None
        notes.append(f"{symbol} 1-minute bars unavailable: {str(exc)[:160]}.")
    today = (
        frame.loc[frame.index.date == session] if frame is not None and not frame.empty else None
    )
    if today is None or today.empty:
        missing.append("pre_market_or_latest_price")
        return out, missing, observations, notes
    pre = today.between_time("04:00", "09:29")
    if not pre.empty:
        latest = float(pre["Close"].iloc[-1])
        out["pre_market_or_latest_price"] = latest
        if previous_close > 0:
            out["pre_market_change_pct"] = (latest / previous_close - 1.0) * 100.0
        observations.append(
            intraday_observation("pre_market_or_latest_price", symbol, pre.index[-1])
        )
        observations.append(intraday_observation("pre_market_change_pct", symbol, pre.index[-1]))
    if now_et.time() >= end:
        opening = today.between_time(
            start.strftime("%H:%M"), end.strftime("%H:%M"), inclusive="left"
        )
        if not opening.empty:
            first, last = opening.iloc[0], opening.iloc[-1]
            out.update(
                {
                    "premarket_open_4am": float(first["Open"]),
                    "premarket_window_high": float(opening["High"].max()),
                    "premarket_window_low": float(opening["Low"].min()),
                    "premarket_window_change_pct": float((last["Close"] / first["Open"] - 1) * 100),
                    "premarket_window_volume": float(opening["Volume"].fillna(0).sum()),
                }
            )
            observations.append(
                intraday_observation("premarket_open_4am", symbol, opening.index[0])
            )
            observations.append(
                intraday_observation(
                    "premarket_window_change_pct", symbol, opening.index[-1], opening.index[0]
                )
            )
    if out["pre_market_or_latest_price"] is None:
        missing.append("pre_market_or_latest_price")
    return out, missing, observations, notes


def _overnight_inputs(
    data: MarketSource,
    profile: dict[str, Any],
    now_et: datetime,
    base_session: date,
    histories: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Inputs observable at ~4:20am ET that daily bars cannot supply. Every
    fetch is best effort: a failure leaves the field null and names it in
    missing, and never fails the forecast."""
    out: dict[str, Any] = {
        "overnight_futures_change_pct": None,
        "vix_overnight_level": None,
        "vix9d_level": None,
        "vix3m_level": None,
        "rvx_level": None,
        "primary_volatility_level": None,
        "iv_rank_pct": None,
        "observations": [],
        "missing": [],
        "notes": [],
        "cboe_symbols": [],
    }
    futures = str(profile["futures"])
    volatility = str(profile["volatility"])
    keys = [k for k in dict.fromkeys(["^VIX9D", "^VIX3M", volatility]) if k in CBOE_INDEX_SOURCES]
    want_vix = overnight_vix_window_open(now_et)

    with ThreadPoolExecutor(max_workers=2 + len(keys)) as pool:
        futures_job = pool.submit(data.minutes, futures)
        vix_job = pool.submit(data.minutes, "^VIX") if want_vix else None
        cboe_jobs = {k: pool.submit(data.cboe, str(CBOE_INDEX_SOURCES[k]["cboe"])) for k in keys}

    try:
        change = overnight_futures_change(minute_closes(futures_job.result()), base_session, now_et)
        if change["change_pct"] is not None:
            out["overnight_futures_change_pct"] = float(change["change_pct"])
            out["observations"].append(
                intraday_observation(
                    "overnight_futures_change_pct",
                    futures,
                    change["latest"][0],
                    change["reference"][0],
                )
            )
        else:
            out["notes"].append(f"Overnight {futures} change unavailable: {change['reason']}.")
    except Exception as exc:
        out["notes"].append(f"{futures} 1-minute bars unavailable: {str(exc)[:160]}.")
    if out["overnight_futures_change_pct"] is None:
        out["missing"].append("overnight_futures_change_pct")

    if vix_job is not None:
        try:
            bar = latest_overnight_vix(
                minute_closes(vix_job.result()), now_et.date(), base_session, now_et
            )
        except Exception as exc:
            bar = None
            out["notes"].append(f"^VIX 1-minute bars unavailable: {str(exc)[:160]}.")
        if bar is not None:
            out["vix_overnight_level"] = bar[1]
            out["observations"].append(intraday_observation("vix_overnight_level", "^VIX", bar[0]))
        else:
            out["missing"].append("vix_overnight_level")

    chosen: dict[str, dict[str, Any]] = {}
    for key in keys:
        cboe = str(CBOE_INDEX_SOURCES[key]["cboe"])
        fallback = CBOE_INDEX_SOURCES[key]["yahoo_fallback"]
        try:
            cboe_series = cboe_jobs[key].result()
        except Exception as exc:
            cboe_series = None
            out["notes"].append(f"Cboe {cboe} CSV unavailable: {str(exc)[:160]}.")
        candidates: list[dict[str, Any]] = [
            {"source": "cboe_daily_csv", "ticker": cboe, "series": cboe_series}
        ]
        first = choose_daily_series(candidates, base_session)
        if fallback and (first is None or first["latest_date"] < base_session):
            frame = histories.get(fallback)
            if frame is None:
                try:
                    frame = data.daily(fallback)
                except Exception:
                    frame = None
            if frame is not None and not frame.empty:
                yahoo = frame["Close"].replace([np.inf, -np.inf], np.nan).dropna()
                yahoo.index = [stamp.date() for stamp in yahoo.index]
                candidates.append({"source": "yahoo_chart_1d", "ticker": fallback, "series": yahoo})
        pick = choose_daily_series(candidates, base_session)
        if pick is None:
            continue
        if pick["source"] == "cboe_daily_csv":
            out["cboe_symbols"].append(cboe)
        if pick["latest_date"] < base_session:
            out["notes"].append(
                f"{cboe} close is from {pick['latest_date'].isoformat()}, older than {base_session.isoformat()}."
            )
        chosen[key] = pick

    for key, name in (("^VIX9D", "vix9d_level"), ("^VIX3M", "vix3m_level"), ("^RVX", "rvx_level")):
        if key == "^RVX" and volatility != "^RVX":
            continue
        pick = chosen.get(key)
        if pick is not None:
            out[name] = pick["latest"]
            out["observations"].append(
                daily_observation(name, pick["source"], pick["ticker"], pick["latest_date"])
            )
        else:
            out["missing"].append(name)

    primary = chosen.get(volatility)
    if primary is not None:
        out["primary_volatility_level"] = primary["latest"]
        out["iv_rank_pct"] = iv_rank_pct(primary["series"], base_session)
        if out["iv_rank_pct"] is not None:
            out["observations"].append(
                daily_observation(
                    "iv_rank_pct", primary["source"], primary["ticker"], primary["latest_date"]
                )
            )
    if out["iv_rank_pct"] is None:
        out["missing"].append("iv_rank_pct")
    return out


def _last(series: pd.Series | None) -> float | None:
    if series is None or len(series) == 0:
        return None
    value = float(series.iloc[-1])
    return value if np.isfinite(value) else None


def yield_pct(tnx: float | None) -> float | None:
    """^TNX as a yield in percent. Yahoo once quoted it x10 (42.0 for 4.20%)
    and now quotes the yield itself (4.84); no 10-year yield has been near
    20% since 1981, so anything above that is the old convention."""
    if tnx is None:
        return None
    return tnx / 10.0 if tnx > 20.0 else tnx


def _session_phase(now_et: datetime) -> str:
    if not is_session(now_et.date()) or now_et.time() < clock_time(4, 0):
        return "closed"
    if now_et.time() < REGULAR_OPEN:
        return "pre_market"
    if now_et.time() < SESSION_CLOSE:
        return "regular_open"
    return "after_hours" if now_et.time() < clock_time(20, 0) else "closed"


def build_snapshot(
    data: MarketSource,
    symbol: str,
    profile: dict[str, Any],
    histories: dict[str, pd.DataFrame],
    target: pd.DataFrame,
    covariates: list[str],
    training_rows: int,
    missing: list[str],
    notes: list[str],
    now: datetime,
    session: date,
) -> tuple[dict[str, Any], list[str]]:
    """What was observable at the run, each value with where and when it
    was read. Returns (snapshot, the Cboe symbols read)."""
    now_et = now.astimezone(EASTERN)
    close = target["Close"].astype(float)
    base_price = float(close.iloc[-1])
    base_session = target.index[-1].date()
    premarket, pm_missing, pm_observations, pm_notes = _premarket(
        data, symbol, now_et, session, base_price
    )
    overnight = _overnight_inputs(data, profile, now_et, base_session, histories)
    missing = [*missing, *pm_missing, *overnight["missing"]]
    notes = [*notes, *pm_notes, *overnight["notes"]]

    vix = _close(histories, "^VIX")
    vxn = _close(histories, "^VXN")
    futures = _close(histories, str(profile["futures"]))
    dxy = _close(histories, "DX-Y.NYB")
    crude = _close(histories, "CL=F")
    tnx = _close(histories, "^TNX")

    returns = _log_returns_pct(close).dropna()
    rv20 = float(returns.tail(20).std(ddof=1) * np.sqrt(252)) if len(returns) >= 20 else None
    implied = overnight["primary_volatility_level"]
    if implied is not None:
        # The underlying's index scaled to a daily-reset leveraged fund.
        implied *= float(profile["leverage"])
    futures_daily = (
        (float(futures.iloc[-1]) / float(futures.iloc[-2]) - 1) * 100
        if futures is not None and len(futures) >= 2
        else None
    )
    for name, value in (
        ("vix_level", _last(vix)),
        ("vxn_level", _last(vxn)),
        ("us_10y_yield_pct", _last(tnx)),
    ):
        if value is None:
            missing.append(name)

    observations: list[dict[str, Any]] = [
        daily_observation("prev_close", "yahoo_chart_1d", symbol, base_session),
        *pm_observations,
        *overnight["observations"],
    ]
    for name, ticker, series, value in (
        ("vix_level", "^VIX", vix, _last(vix)),
        ("vxn_level", "^VXN", vxn, _last(vxn)),
        ("futures_daily_change_pct", str(profile["futures"]), futures, futures_daily),
        ("us_10y_yield_pct", "^TNX", tnx, _last(tnx)),
        ("dxy_level", "DX-Y.NYB", dxy, _last(dxy)),
        ("wti_crude_usd", "CL=F", crude, _last(crude)),
    ):
        if value is not None and series is not None:
            observations.append(
                daily_observation(name, "yahoo_chart_1d", ticker, series.index[-1].date())
            )
    iv_source = next((o for o in overnight["observations"] if o["field"] == "iv_rank_pct"), None)
    if implied is not None and iv_source is not None:
        observations.append({**iv_source, "field": "symbol_iv_pct"})

    last_bar = target.iloc[-1]
    snapshot = {
        "symbol": symbol,
        "underlying_symbol": profile["underlying"],
        "leverage_factor": profile["leverage"],
        "base_session_date": base_session.isoformat(),
        "target_session": session.isoformat(),
        "as_of_utc": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "market_session_phase": _session_phase(now_et),
        "prev_close": base_price,
        **premarket,
        "intraday_high": float(last_bar["High"]) if pd.notna(last_bar.get("High")) else None,
        "intraday_low": float(last_bar["Low"]) if pd.notna(last_bar.get("Low")) else None,
        "five_day_return_pct": (float(close.iloc[-1]) / float(close.iloc[-6]) - 1) * 100
        if len(close) >= 6
        else None,
        "twenty_day_return_pct": (float(close.iloc[-1]) / float(close.iloc[-21]) - 1) * 100
        if len(close) >= 21
        else None,
        "overnight_futures_symbol": profile["futures"],
        "overnight_futures_change_pct": overnight["overnight_futures_change_pct"],
        "futures_daily_change_pct": futures_daily,
        "vix_level": _last(vix),
        "vix_overnight_level": overnight["vix_overnight_level"],
        "vxn_level": _last(vxn),
        "rvx_level": overnight["rvx_level"],
        "vix9d_level": overnight["vix9d_level"],
        "vix3m_level": overnight["vix3m_level"],
        "symbol_iv_pct": implied,
        "iv_rank_pct": overnight["iv_rank_pct"],
        "realized_vol_20d_pct": rv20,
        "us_10y_yield_pct": yield_pct(_last(tnx)),
        "dxy_level": _last(dxy),
        "wti_crude_usd": _last(crude),
        "missing_inputs": list(dict.fromkeys(missing)),
        "confidence_score": min(1.0, len(covariates) / 22.0),
        "source_coverage": "mixed" if training_rows >= 500 and len(covariates) >= 3 else "degraded",
        "notes": notes,
        "input_observations": observations,
    }
    return snapshot, overnight["cboe_symbols"]


# --------------------------------------------------------------------
# Signals and the report


def execution_signals(
    training: pd.DataFrame, snapshot: dict[str, Any], distributions: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """The generator's rules: volatility state from 20-session realised vol
    against its last year, regime from 20-session momentum, skew from the
    1-day tails, gap risk from the pre-market move. Position sizing stays
    off (kelly 0, all cash-defensive) until the model is walk-forward
    calibrated."""
    returns = training["target"].to_numpy(dtype=np.float64)
    rv = (training["target"].rolling(20).std() * np.sqrt(252)).dropna().tail(252).to_numpy()
    current = float(rv[-1]) if len(rv) else 0.0
    q50, q85, q97 = (float(np.quantile(rv, q)) if len(rv) else current for q in (0.5, 0.85, 0.97))
    state = (
        "compressed"
        if current < q50
        else "normal"
        if current < q85
        else "elevated"
        if current < q97
        else "extreme"
    )
    momentum = float(np.sum(returns[-20:])) if len(returns) >= 20 else 0.0
    if momentum > 2.0:
        regime = "low_vol_uptrend" if state in ("compressed", "normal") else "breakout_expansion"
    elif momentum < -2.0:
        regime = "high_vol_downtrend"
    else:
        regime = "mean_reverting_range"

    one_day = distributions["tomorrow"]["summary"]
    p05, median, p95 = (
        one_day["quantiles_pct"]["p05"],
        one_day["median_pct"],
        one_day["quantiles_pct"]["p95"],
    )
    left, right = abs(p05 - median), abs(p95 - median)
    skew = (
        "bearish_tail"
        if left > right * 1.2
        else "bullish_tail"
        if right > left * 1.2
        else "neutral"
    )

    gap = snapshot.get("pre_market_change_pct")
    gap_risk = (
        "moderate"
        if gap is None
        else "high"
        if abs(gap) >= 2.0
        else "moderate"
        if abs(gap) >= 0.75
        else "low"
    )
    implied, rv20 = snapshot.get("symbol_iv_pct"), snapshot.get("realized_vol_20d_pct")
    return {
        "data_quality": {
            "confidence_score": round(float(snapshot["confidence_score"]), 2),
            "source_coverage": snapshot["source_coverage"],
            "missing_inputs": snapshot["missing_inputs"],
        },
        "regime": regime,
        "volatility_state": state,
        "implied_vs_realized_vol_spread_pct": round(implied - rv20, 2)
        if implied is not None and rv20 is not None
        else 0.0,
        "expected_1d_move_pct": round(max(0.01, (p95 - p05) / 2.0), 2),
        "skew_bias": skew,
        "overnight_gap_risk": gap_risk,
        "kelly_fraction_cap": 0.0,
        "next_day_catalysts": [],
        "suggested_strategy_weights": {
            "momentum_trend": 0.0,
            "mean_reversion": 0.0,
            "volatility_harvesting": 0.0,
            "cash_defensive": 1.0,
        },
    }


def rounded_horizon(horizon: dict[str, Any]) -> dict[str, Any]:
    """A horizon as the report carries it: probabilities in whole basis
    points that sum to exactly 10,000 (the largest share absorbs the
    rounding), each CDF the running sum of what is shown, percentages to two
    places. Rounding is monotone, so quantile order, ES <= p05 and the
    median inside p25-p75 survive it."""
    raw = [
        horizon["underflow_prob"],
        *(b["prob"] for b in horizon["bins"]),
        horizon["overflow_prob"],
    ]
    total = sum(raw) or 1.0
    bp = [round(p / total * 10_000) for p in raw]
    bp[int(np.argmax(bp))] += 10_000 - sum(bp)
    under, inner, over = bp[0], bp[1:-1], bp[-1]
    running = under
    bins = []
    for spec, prob in zip(horizon["bins"], inner, strict=True):
        running += prob
        bins.append(
            {
                "min_pct": round(spec["min_pct"], 2),
                "max_pct": round(spec["max_pct"], 2),
                "prob": prob / 10_000,
                "cdf": running / 10_000,
            }
        )
    summary = horizon["summary"]
    return {
        "label": horizon["label"],
        "trading_days": horizon["trading_days"],
        "bin_width_pct": horizon["bin_width_pct"],
        "underflow_prob": under / 10_000,
        "overflow_prob": over / 10_000,
        "bins": bins,
        "summary": {
            "mean_pct": round(summary["mean_pct"], 2),
            "median_pct": round(summary["median_pct"], 2),
            "std_pct": max(0.01, round(summary["std_pct"], 2)),
            "prob_positive": round(summary["prob_positive"], 4),
            "expected_shortfall_5pct": round(summary["expected_shortfall_5pct"], 2),
            "quantiles_pct": {k: round(v, 2) for k, v in summary["quantiles_pct"].items()},
        },
    }


def _fetch_histories(
    data: MarketSource, tickers: list[str]
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    histories: dict[str, pd.DataFrame] = {}
    errors: dict[str, str] = {}
    unique = list(dict.fromkeys(tickers))
    with ThreadPoolExecutor(max_workers=min(6, len(unique))) as pool:
        jobs = {ticker: pool.submit(data.daily, ticker) for ticker in unique}
    for ticker, job in jobs.items():
        try:
            histories[ticker] = job.result()
        except Exception as exc:  # an outage is a missing input, not a failed run
            errors[ticker] = str(exc)[:240]
    return histories, errors


def _sources(histories: dict[str, pd.DataFrame], cboe_symbols: list[str]) -> list[dict[str, str]]:
    found = [
        {
            "title": f"Yahoo Finance daily history: {ticker}",
            "uri": f"https://finance.yahoo.com/quote/{ticker.replace('^', '%5E').replace('=', '%3D')}/",
            "domain": "finance.yahoo.com",
        }
        for ticker in sorted(histories)
    ]
    found.extend(
        {
            "title": f"Cboe daily index history: {s}",
            "uri": cboe_csv_url(s),
            "domain": "cdn-api.cboe.com",
        }
        for s in sorted(set(cboe_symbols))
    )
    return found


def generate(
    symbol: str,
    engine: str = "chronos",
    *,
    now: datetime | None = None,
    data: MarketSource | None = None,
    progress: Progress | None = None,
    pipeline: Any | None = None,
    simulations: int | None = None,
) -> Generated:
    """One forecast for `symbol` (module docstring). ForecastRefused when no
    honest report can be made now; the message is meant for the page."""
    say = progress or (lambda _message: None)
    symbol = (symbol or "").strip().upper()
    if not SYMBOL.match(symbol):
        raise ForecastRefused(f"{symbol!r} is not a market symbol.")
    if engine not in engines.ENGINES:
        raise ForecastRefused(f"Unknown engine {engine!r}; one of {', '.join(engines.ENGINES)}.")
    if engine == "chronos" and pipeline is None:
        available, why = engines.chronos_available()
        if not available:
            raise ForecastRefused(f"Chronos-2 is not available on this host: {why}.")
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ForecastRefused("The run's clock has no time zone.")
    session, why_not = window_check(now)
    if session is None:
        raise ForecastRefused(why_not or "No report can be made now.")
    data = data or MarketData()
    profile = profile_for(symbol)

    say(f"Fetching daily history for {symbol} and its covariates")
    tickers = [
        symbol,
        str(profile["underlying"]),
        "SPY",
        "^VIX",
        "^VXN",
        str(profile["futures"]),
        "^TNX",
        "DX-Y.NYB",
        "CL=F",
    ]
    raw, errors = _fetch_histories(data, tickers)
    if symbol not in raw:
        raise ForecastRefused(
            f"No daily history for {symbol}: {errors.get(symbol, 'nothing returned')}."
        )
    histories = {ticker: _completed(frame, session) for ticker, frame in raw.items()}
    target = histories[symbol]
    if len(target) < MIN_HISTORY:
        raise ForecastRefused(
            f"Only {len(target)} completed daily bars for {symbol}; {MIN_HISTORY} are needed."
        )
    base_session = target.index[-1].date()
    expected = previous_session(session)
    if base_session != expected:
        raise ForecastRefused(
            f"The latest {symbol} daily bar is {base_session}, but a report for {session} is anchored "
            f"to the {expected} close: the data source has not posted it yet."
        )

    say("Building the training frame")
    training, covariates, frame_missing = training_frame(symbol, profile, histories, target)
    if len(training) < MIN_HISTORY:
        raise ForecastRefused(
            f"Only {len(training)} aligned observations after joining covariates; {MIN_HISTORY} are needed."
        )
    target_values = training["target"].to_numpy(dtype=np.float64)
    history = target_values[-min(len(target_values), 1260) :]

    if engine == "chronos":
        say(
            f"Running {engines.MODEL_ID}"
            + ("" if pipeline is not None else " (the first run loads the model)")
        )
        future = calendar_covariates(future_sessions(base_session, MAX_HORIZON))
        quantiles = engines.chronos_quantiles(
            target_values,
            {name: training[name].to_numpy() for name in covariates},
            {name: future[name].to_numpy() for name in future.columns if name in covariates},
            MAX_HORIZON,
            pipeline=pipeline,
        )
    else:
        say("Computing the historical baseline")
        quantiles = engines.bootstrap_quantiles(history, MAX_HORIZON)
    daily, extension = extend_daily_quantiles(quantiles.values, history, MAX_HORIZON)

    paths_n = int(simulations or SIMULATIONS)
    say(f"Simulating {paths_n:,} scenarios")
    seed = (sum(ord(c) for c in symbol) + int(session.strftime("%Y%m%d"))) % (2**32 - 1)
    paths = simulate_cumulative_returns(
        daily, history, n_paths=paths_n, block_length=BLOCK_LENGTH, seed=seed
    )
    distributions = build_horizon_distributions(paths, horizon_specs(profile["leverage"]))

    say("Reading the overnight inputs")
    snapshot, cboe_symbols = build_snapshot(
        data,
        symbol,
        profile,
        histories,
        target,
        covariates,
        len(training),
        [*frame_missing, *(f"{t} history" for t in errors if t != symbol)],
        [
            *(f"{name}: {why}." for name, why in frame_missing.items()),
            *(f"{t}: {e}" for t, e in errors.items()),
        ],
        now,
        session,
    )

    say("Assembling and auditing the report")
    if quantiles.engine == "chronos":
        model_text = (
            f"{quantiles.model} zero-shot (direct {quantiles.direct_steps}-session quantiles + "
            f"historical extension to {MAX_HORIZON}; {BLOCK_LENGTH}-session block bootstrap; "
            f"{paths_n:,} scenarios)"
        )
    else:
        model_text = (
            f"historical-bootstrap baseline, no model ({BLOCK_LENGTH}-session block bootstrap; "
            f"{paths_n:,} scenarios)"
        )
    report = {
        "schema_version": SCHEMA_VERSION,
        "symbol": symbol,
        "as_of": now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "target_session": session.isoformat(),
        "base_price": round(float(target["Close"].iloc[-1]), 4),
        "return_type": "simple_pct",
        "model": model_text,
        "prompt_version": GENERATOR_VERSION,
        "execution_signals": execution_signals(training, snapshot, distributions),
        "horizons": {key: rounded_horizon(value) for key, value in distributions.items()},
    }
    audit = parse_report(report)
    return Generated(
        report=report,
        audit={
            **audit.to_dict(),
            "session": session.isoformat(),
            "sha256": audit.report.sha256 if audit.report else None,
        },
        snapshot=snapshot,
        sources=_sources(histories, cboe_symbols),
        diagnostics={
            "engine": quantiles.engine,
            "model_id": quantiles.model,
            "history_observations": len(training),
            "covariates_used": covariates,
            "simulation_paths": paths_n,
            "block_length": BLOCK_LENGTH,
            "direct_steps": quantiles.direct_steps,
            "native_horizon": quantiles.native_horizon,
            "extension_steps": int(extension["extension_steps"]),
            "base_session": base_session.isoformat(),
            "target_session": session.isoformat(),
            "calibration_status": "uncalibrated",
        },
    )


__all__ = [
    "GENERATOR_VERSION",
    "HORIZON_SPECS",
    "PROFILES",
    "SCHEMA_VERSION",
    "ForecastRefused",
    "Generated",
    "calendar_covariates",
    "execution_signals",
    "future_sessions",
    "generate",
    "horizon_specs",
    "profile_for",
    "rounded_horizon",
    "training_frame",
    "window_check",
    "yield_pct",
]
