"""The TFT's three outside series, built from free data the warehouse holds.

research/ml/tft_features.py reads s_macro, s_earnings and s_news from CSVs
(`timestamp`, `value`), point-in-time. None of the three has a free source
in the shape the TFT asks for -- a macro-surprise index and earnings-call
sentiment need consensus forecasts and transcripts, which are sold -- so
each is the closest free stand-in, named for what it is:

    s_news      the San Francisco Fed's daily news sentiment index
                (frbsf_NEWS_SENTIMENT): the tone of economics articles in
                24 US newspapers, already in about [-0.6, 0.4].
    s_macro     a policy-uncertainty shock: the z-score of the daily
                Economic Policy Uncertainty index (fred_USEPUINDXD; Baker,
                Bloom & Davis), its log smoothed over SMOOTH_DAYS and set
                against the trailing UNCERTAINTY_WINDOW readings. Positive
                is MORE uncertainty than usual -- news, not a forecast miss.
    s_earnings  the earnings announcement return (Brandt, Kishore,
                Santa-Clara & Venkatachalam 2008): for each release on the
                warehouse's earnings calendar (16 Nasdaq-100 reporters),
                the reporter's log return over its reaction session less
                QQQ's, scored tanh(EAR / EAR_SCALE) -- a 5% beat of the
                index is +0.76. The decayed sum of the scores (half-life
                HALFLIFE_SESSIONS) over the decayed count, held to at least
                one: a mean through a reporting season, fading toward 0
                between seasons. How the market graded the reports, which is
                what a sentiment score tries to measure.

POINT IN TIME. Every input row in the warehouse is already stamped at the
moment it could first be read (research/ml/sources.py: the series' lag is
in the stamp). Each output row keeps its input's stamp, so a value is read
only on bars after it. An earnings reaction is stamped at its reaction
session's close (21:00 UTC), when both closes it compares are known:

    released after the close (16:00 NY or later)   reaction = the next session
    released before the open, or during it         reaction = the release day,
                                                   against the session before

The earnings calendar is tools/build_earnings_calendar.py's, ingested as
market_events; s_earnings fades toward 0 after its last release.
"""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

NEW_YORK = ZoneInfo("America/New_York")
CLOSE_HOUR_UTC = 21  # research/ml/sources.py stamps a daily close here

NEWS_SERIES = "frbsf_NEWS_SENTIMENT"
UNCERTAINTY_SERIES = "fred_USEPUINDXD"
BENCHMARK_SERIES = "yahoo_QQQ"

SMOOTH_DAYS = 5
UNCERTAINTY_WINDOW = 250
UNCERTAINTY_CLIP = 4.0
EAR_SCALE = 0.05
HALFLIFE_SESSIONS = 10.0
# GOOG and GOOGL report together: one company, scored once.
DUPLICATE_REPORTERS = {"GOOG": "GOOGL"}


def news_sentiment(series: pd.Series) -> pd.Series:
    """s_news: the sentiment index, as stamped."""
    return series.astype(float).sort_index()


def uncertainty_shock(
    epu: pd.Series,
    smooth: int = SMOOTH_DAYS,
    window: int = UNCERTAINTY_WINDOW,
    clip: float = UNCERTAINTY_CLIP,
) -> pd.Series:
    """s_macro: the z-score of smoothed log EPU against its own trailing
    `window` readings, each from readings at or before it."""
    values = epu.astype(float).sort_index()
    level = np.log(values.where(values > 0)).rolling(smooth, min_periods=smooth).mean()
    mean = level.rolling(window, min_periods=window).mean()
    sd = level.rolling(window, min_periods=window).std()
    return ((level - mean) / sd.where(sd > 0)).clip(-clip, clip).dropna()


def _session_closes(series: pd.Series) -> pd.Series:
    """A daily close series stamped at 21:00 UTC, indexed by session date."""
    stamps = pd.DatetimeIndex(series.index)
    days = (stamps - pd.Timedelta(hours=CLOSE_HOUR_UTC)).tz_convert("UTC").normalize()
    out = pd.Series(series.to_numpy(float), index=days.tz_localize(None))
    return out[~out.index.duplicated(keep="last")].sort_index()


def reaction_sessions(release: pd.Timestamp, sessions: pd.DatetimeIndex) -> tuple | None:
    """(session before, reaction session) for a release at `release`, from
    the sorted session dates; None when the history does not reach both."""
    local = release.tz_convert(NEW_YORK)
    day = pd.Timestamp(local.date())
    after_close = local.hour >= 16
    i = int(sessions.searchsorted(day, side="right" if after_close else "left"))
    if i <= 0 or i >= len(sessions):
        return None
    return sessions[i - 1], sessions[i]


def earnings_reaction(
    events: pd.DataFrame,
    closes: dict[str, pd.Series],
    benchmark: pd.Series,
    scale: float = EAR_SCALE,
    halflife: float = HALFLIFE_SESSIONS,
) -> pd.Series:
    """s_earnings: the decayed mean of the releases' scored announcement
    returns, one value per benchmark session, stamped at its close."""
    bench = _session_closes(benchmark)
    sessions = pd.DatetimeIndex(bench.index)
    stock = {t: _session_closes(s) for t, s in closes.items()}
    scores: dict[pd.Timestamp, list[float]] = {}
    seen: set[tuple[str, pd.Timestamp]] = set()
    for row in events.itertuples(index=False):
        ticker = DUPLICATE_REPORTERS.get(str(row.ticker), str(row.ticker))
        if ticker not in stock:
            continue
        pair = reaction_sessions(pd.Timestamp(row.release).tz_convert("UTC"), sessions)
        if pair is None or (ticker, pair[1]) in seen:
            continue
        before, react = pair
        series = stock[ticker]
        if before not in series.index or react not in series.index:
            continue
        ear = math.log(series[react] / series[before]) - math.log(bench[react] / bench[before])
        if math.isfinite(ear):
            seen.add((ticker, react))
            scores.setdefault(react, []).append(math.tanh(ear / scale))
    if not scores:
        raise ConfigurationError("no earnings release could be scored against the closes given")
    keep = 0.5 ** (1.0 / halflife)
    total = count = 0.0
    values = []
    start = sessions.searchsorted(min(scores))
    for day in sessions[start:]:
        day_scores = scores.get(day, ())
        total = keep * total + sum(day_scores)
        count = keep * count + len(day_scores)
        values.append(total / max(count, 1.0))
    index = sessions[start:].tz_localize("UTC") + pd.Timedelta(hours=CLOSE_HOUR_UTC)
    return pd.Series(values, index=index)


def as_csv_frame(series: pd.Series) -> pd.DataFrame:
    """The `timestamp`, `value` shape tft_features.PointInTimeSeries reads."""
    stamps = pd.DatetimeIndex(series.index)
    if stamps.tz is None:
        raise ConfigurationError("a TFT input series needs tz-aware stamps")
    return pd.DataFrame(
        {"timestamp": stamps.tz_convert("UTC").map(pd.Timestamp.isoformat), "value": series.values}
    )


__all__ = [
    "BENCHMARK_SERIES",
    "EAR_SCALE",
    "HALFLIFE_SESSIONS",
    "NEWS_SERIES",
    "UNCERTAINTY_SERIES",
    "as_csv_frame",
    "earnings_reaction",
    "news_sentiment",
    "reaction_sessions",
    "uncertainty_shock",
]
