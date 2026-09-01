"""Pull TQQQ extended-hours minute bars from HF Market Data, year by year.

Chunked per calendar year rather than issued as one 10-year request so a
failure at hour four costs one year, not the whole pull. Each year is
written and checksummed on its own; combine_years() then concatenates
into the single CSV the backtest reads.

Run:  python pull_extended_history.py
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

# tools/ scripts import from src/, and Python puts THIS file's directory
# on sys.path[0] -- not the working directory -- so `python
# tools/pull_extended_history.py` would otherwise fail on `from src...` while
# `python -m tools.pull_extended_history` succeeded. Same bootstrap as
# tests/fixtures/regression_baseline.py, so both invocations work.
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

from src.data_validation import validate
from src.hf_market_data import HFMarketData
from src.historical_data import FetchSpec, session_scope_tag, write_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("pull")

SYMBOL = "TQQQ"
START_YEAR = 2016
END = datetime(2026, 8, 21, tzinfo=UTC)
PARTS_DIR = Path("data/parts")


def year_path(year: int) -> Path:
    return PARTS_DIR / f"{SYMBOL}_1Min_hf_splitdiv_ext_{year}.csv"


def pull_year(year: int, client: HFMarketData) -> Path:
    out = year_path(year)
    if out.exists():
        logger.info(f"{year}: already present, skipping")
        return out

    start = datetime(year, 1, 1, tzinfo=UTC)
    end = min(datetime(year + 1, 1, 1, tzinfo=UTC), END)
    spec = FetchSpec(
        symbol=SYMBOL,
        start=start,
        end=end,
        timeframe="1Min",
        feed="hf",
        adjustment="splitdiv",
        regular_hours_only=False,
    )
    df, _, dupes = client.fetch_bars(spec)
    sessions = len({t.tz_convert("America/New_York").date() for t in df.index})
    logger.info(
        f"{year}: {len(df):,} bars / {sessions} sessions "
        f"= {len(df) / max(sessions, 1):.1f} per session (dupes dropped: {dupes})"
    )
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(df, out, force=True)
    return out


def combine_years(years: list[int]) -> Path:
    frames = [
        pd.read_csv(year_path(y), parse_dates=["timestamp"], index_col="timestamp")
        for y in years
        if year_path(y).exists()
    ]
    combined = pd.concat(frames).sort_index()
    before = len(combined)
    combined = combined[~combined.index.duplicated(keep="last")]
    if before != len(combined):
        logger.warning(f"dropped {before - len(combined)} duplicate timestamps at year seams")

    # The same contract gate every other dataset passes.
    validate(combined)

    tag = session_scope_tag(False)
    out = Path("data") / (
        f"{SYMBOL}_1Min_hf_splitdiv_{tag}_"
        f"{combined.index[0].date().isoformat()}_{combined.index[-1].date().isoformat()}.csv"
    )
    write_csv(combined, out, force=True)

    sessions = len({t.tz_convert("America/New_York").date() for t in combined.index})
    logger.info(f"COMBINED -> {out}")
    logger.info(
        f"  {len(combined):,} bars / {sessions} sessions = "
        f"{len(combined) / sessions:.2f} bars per session"
    )
    logger.info(f"  {combined.index[0]} -> {combined.index[-1]}")
    return out


if __name__ == "__main__":
    years = list(range(START_YEAR, END.year + 1))
    client = HFMarketData()
    for y in years:
        try:
            pull_year(y, client)
        except Exception as e:
            logger.error(f"{y}: FAILED {type(e).__name__}: {e}")
            sys.exit(1)
    combine_years(years)
