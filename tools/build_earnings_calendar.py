"""Derive minute-precise earnings release timestamps from the tape.

--------------------------------------------------------------------
WHY DERIVE RATHER THAN TRANSCRIBE

A hand-kept table of "MSFT releases at 4:05 PM ET" has two problems that
only show up once you check it against the market:

  1. It is a single time applied to a decade. Release schedules drift;
     a company that released at 16:05 in 2024 may have released at 16:30
     in 2017, and one static number is silently wrong for whole years.
  2. It cannot be verified. Spot-checking the supplied table against
     post-close volume matched NVDA (16:20) and META (16:05) exactly and
     AAPL/AMZN/GOOGL/NFLX closely, but put MSFT's and TSLA's measured
     peaks 3-6 minutes EARLIER than claimed -- on one quarter each,
     which is not enough to correct a table, but is enough to say the
     table should not be trusted unchecked.

Both are solved by measuring each event separately.

--------------------------------------------------------------------
IS THIS LOOKAHEAD? No, and the distinction matters.

Earnings dates and times are announced weeks in advance -- they are
scheduled, publicly known facts, not information revealed by the
reaction. Recovering the schedule from historical data offline, then
letting the strategy see only "an event is scheduled at 16:06", gives
the strategy exactly what a real trader had in advance. What would be
lookahead is letting it see the REACTION (the +5.5% move) before that
move happened; nothing here does that, and the calendar this emits
carries no outcome, only a timestamp.

--------------------------------------------------------------------
METHOD

Two stages, cheap then precise:

  1. FIND THE DAY, from daily bars. 381 of 385 mega-cap announcements in
     this window landed after the close, so the reaction is the NEXT
     session's opening gap. A day whose open gaps hard from the prior
     close on elevated volume means the prior session carried the
     release. Daily bars cost ~3 requests per ticker for a decade.
  2. FIND THE MINUTE, from that day's post-close minute bars. The
     release minute is the peak of post-close volume -- verified
     against the supplied table on NVDA (16:20) and META (16:05),
     both exact.

Candidates are then filtered to at most four per calendar year with a
minimum spacing, because a quarterly reporter has four events and the
largest remaining gaps are macro moves, not earnings.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import timedelta

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("earnings")

BASE = "https://www.hfmarketdata.io"
SOURCE_TZ = "America/New_York"

# The actual top QQQ holdings by weight (stockanalysis.com, 2026-08-13),
# not the conventional "mega-cap" list. Those differ in a way that
# matters: MU is the 4th largest holding at 4.61% and AMD the 6th at
# 3.39%, and neither appears on the usual FAANG-shaped roster, while
# NFLX -- which does -- is outside the top 15 entirely.
#
# GOOG is included alongside GOOGL deliberately. They are one company
# reporting once, so the derivation finds the same timestamp twice; that
# is correct here, because they are two separate holdings (3.14% +
# 2.92%) and an event table that sums concurrent weights should see
# 6.06%, not 3.14%.
TICKERS = (
    "NVDA", "AAPL", "MSFT", "MU", "AMZN", "AMD", "GOOGL", "AVGO", "GOOG",
    "META", "TSLA", "WMT", "INTC", "CSCO", "COST", "NFLX",
)

START = "2016-01-01"
END = "2026-08-21"

# The gap threshold is measured in units of each ticker's OWN gap
# volatility, not as an absolute percentage. A fixed 2% cut-off silently
# selects on beta: it caught 43/43 of TSLA's and NFLX's releases but only
# 24 of COST's, because Costco simply does not gap 2% on an ordinary
# earnings beat. That is a detector that finds volatile names and calls
# the quiet ones absent.
MIN_GAP_SIGMA = 1.5
MIN_GAP_FLOOR_PCT = 0.8
MIN_VOLUME_RATIO = 1.15
EVENTS_PER_YEAR = 4
MIN_SPACING_DAYS = 45


def get(path: str, **params) -> list[dict]:
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r).get("data") or []
        except Exception as e:
            if attempt == 2:
                logger.warning(f"give up on {path}: {e}")
                return []
            time.sleep(1.5 * (attempt + 1))
    return []


def daily_bars(ticker: str) -> pd.DataFrame:
    rows, cursor = [], START
    while True:
        page = get(
            f"/v1/bars/stock/{ticker}",
            timeframe="1day", start=cursor, end=END,
            order="asc", limit=1000, format="json",
        )
        if not page:
            break
        rows.extend(page)
        last = pd.Timestamp(page[-1]["datetime"])
        if len(page) < 1000:
            break
        cursor = (last + timedelta(days=1)).date().isoformat()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime").sort_index()


def candidate_release_days(df: pd.DataFrame) -> list[pd.Timestamp]:
    """Sessions that carried an after-close release.

    The gap is measured on the FOLLOWING session, so the announcement is
    that row's predecessor.
    """
    if df.empty or len(df) < 30:
        return []
    gap = (df["open"] / df["close"].shift(1) - 1.0).abs() * 100.0
    vol_ratio = df["volume"] / df["volume"].rolling(20, min_periods=5).median()
    # Normalize the gap by the ticker's own recent gap volatility, so the
    # bar for "unusually large" is set per name rather than globally.
    gap_sigma = gap.rolling(120, min_periods=30).std()
    gap_z = gap / gap_sigma.replace(0, pd.NA)

    hits = df.index[
        (gap_z >= MIN_GAP_SIGMA)
        & (gap >= MIN_GAP_FLOOR_PCT)
        & (vol_ratio >= MIN_VOLUME_RATIO)
    ]
    scored = sorted(
        ((gap_z.loc[d] * vol_ratio.loc[d], d) for d in hits), reverse=True
    )
    by_year: dict[int, list[pd.Timestamp]] = defaultdict(list)
    positions = {d: i for i, d in enumerate(df.index)}
    for _, reaction_day in scored:
        i = positions[reaction_day]
        if i == 0:
            continue
        announce = df.index[i - 1]  # the session that held the release
        year = announce.year
        if len(by_year[year]) >= EVENTS_PER_YEAR:
            continue
        if any(abs((announce - k).days) < MIN_SPACING_DAYS for k in by_year[year]):
            continue
        by_year[year].append(announce)
    return sorted(d for days in by_year.values() for d in days)


def release_minute(ticker: str, day: pd.Timestamp) -> tuple[pd.Timestamp, float] | None:
    """Peak post-close volume minute -- the release."""
    d = day.date().isoformat()
    rows = get(
        f"/v1/bars/stock/{ticker}",
        timeframe="1min", start=f"{d}T16:01:00", end=f"{d}T20:00:00",
        order="asc", limit=300, format="json",
    )
    if not rows:
        return None
    peak = max(rows, key=lambda b: b["volume"])
    return pd.Timestamp(peak["datetime"]), float(peak["volume"])


def main() -> None:
    records = []
    for ticker in TICKERS:
        df = daily_bars(ticker)
        if df.empty:
            logger.warning(f"{ticker}: no daily bars")
            continue
        days = candidate_release_days(df)
        logger.info(f"{ticker}: {len(df):,} sessions -> {len(days)} candidate releases")
        for day in days:
            found = release_minute(ticker, day)
            if found is None:
                continue
            ts_et, vol = found
            records.append(
                {
                    "symbol": ticker,
                    "release_et": ts_et.isoformat(),
                    "release_utc": ts_et.tz_localize(SOURCE_TZ, ambiguous="raise",
                                                     nonexistent="raise")
                    .tz_convert("UTC").isoformat(),
                    "postclose_peak_volume": int(vol),
                }
            )
    out = pd.DataFrame(records).sort_values(["release_utc", "symbol"])
    out.to_csv("data/earnings_releases_derived.csv", index=False)
    logger.info(f"wrote {len(out)} events -> data/earnings_releases_derived.csv")

    if not out.empty:
        et = pd.to_datetime(out["release_et"])
        # Minutes-since-midnight, so the median is arithmetic rather than
        # a string sort -- "16:30" and "09:05" do not order numerically.
        summary = out.assign(
            hm=et.dt.strftime("%H:%M"), mins=et.dt.hour * 60 + et.dt.minute
        )
        logger.info("release minute per symbol (ET):")
        for sym, grp in summary.groupby("symbol"):
            mode = grp["hm"].mode()
            med = int(grp["mins"].median())
            post = grp[grp["mins"] >= 16 * 60]
            logger.info(
                f"  {sym:6} n={len(grp):3}  modal={mode.iloc[0] if len(mode) else '--':>5}  "
                f"median={med // 60:02d}:{med % 60:02d}  after-close={len(post)}/{len(grp)}"
            )


if __name__ == "__main__":
    main()
