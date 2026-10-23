#!/usr/bin/env python
"""Keep every tracked fund's bars in the warehouse current.

    python tools/refresh_warehouse.py                     # every fund, once
    python tools/refresh_warehouse.py --fund RSP XBI      # some of them
    python tools/refresh_warehouse.py --redownload SQQQ   # a fund's whole history again
    python tools/refresh_warehouse.py --dry-run           # fetch and compare; write nothing
    python tools/refresh_warehouse.py --daily 20:30       # now, then daily at 20:30 Eastern
    python tools/refresh_warehouse.py --list              # the funds, and how each is kept

docker-compose.yml's `market-data` service runs the --daily form. It needs
Alpaca keys (APCA_API_KEY_ID / APCA_API_SECRET_KEY: market data only, so the
paper keys) and requirements-warehouse.txt. It writes the bar lake directly
and never opens the warehouse catalogs (engine/warehouse/lake.py), so a sweep
recording its results is never in its way.

--------------------------------------------------------------------
WHAT A RUN DOES FOR EACH FUND

The bars are Alpaca's SIP minute bars, adjusted for splits and dividends
("all"): what every fund here was first downloaded as. A free account reads
SIP bars once they are 15 minutes old, so a session is complete 16 minutes
after its last bar: 16:16 Eastern, or 20:16 for SQQQ, which is kept with
extended hours.

1. THE OLDEST STORED SESSION IS ASKED FOR AGAIN. Adjustment rescales every
   bar before a dividend or split, so that session moves whenever one has
   happened since the bars were stored. Then the whole history is downloaded
   again and replaces the old in one exchange: appending would leave a step
   where the old bars meet the new. (In October 2026 six funds had one: bars
   downloaded in August, an increment after September's dividends, a 0.07% to
   1.4% fake drop at the seam.) It refuses if the download lacks a session the
   warehouse holds. The report gives the factor each stretch moved by.
2. OTHERWISE, THE NEW SESSIONS: from the last three stored (or an earlier
   recent session the fund is missing) through the last complete one. The
   three are compared as well, a second check on the adjustment, and
   rewritten where they differ: the tape's late corrections reach a session's
   volume after it closes.
3. A FUND THE WAREHOUSE LACKS is downloaded from its start.

RSP is kept with every regular-hours minute. A minute without a print is a
flat zero-volume bar at the last price (resample_to_uniform_minutes); the
first minutes of a session that opens late carry the previous close.

URSP_SIM is derived, not downloaded (tools/simulate_ursp.py). Its sessions
since the real fund's launch are URSP's daily bars (Yahoo) drawn on that
day's RSP minutes, so it runs after RSP and adds only sessions RSP holds. If
the real fund's adjusted prices moved (a dividend), the whole series is
rebuilt as simulate_ursp.py builds it.

--------------------------------------------------------------------
GENTLE ON A SHARED KEY

The keys are the paper loops', and the Fidelity loop's price feed. Alpaca
allows a free account 200 requests a minute. Every request here asks for at
most a month of one fund, with --pause seconds (1) before the next: a
re-download of ten years is about 130 requests over three minutes.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.trading_calendar import (
    EASTERN,
    is_session,
    previous_session,
    sessions_between,
)

# A session's bars are complete once its last one is past SIP's 15-minute
# delay for a free account.
REGULAR_CLOSE = clock_time(16, 0)
EXTENDED_CLOSE = clock_time(20, 0)
SIP_DELAY = timedelta(minutes=16)

# Stored sessions fetched again with each run's new ones.
OVERLAP_SESSIONS = 3
# How far back a missing session is looked for and fetched again.
LOOKBACK_SESSIONS = 30
# One request covers at most this many calendar days of one fund: ~21
# regular sessions, under Alpaca's 10,000-bar page (SQQQ's extended hours
# take two pages).
CHUNK_DAYS = 31
PAUSE_SECONDS = 1.0

# Alpaca serves the same adjusted price exactly each time it is asked; a
# dividend moves one by 1e-4 or more. A session's few corrected prints are
# not a re-adjustment, but more than this share of them differing is.
TOLERANCE = 1e-6
CORRECTED_SHARE = 0.05
# A re-download must hold at least this share of the bars it replaces.
KEEP_BARS = 0.99

# A failed daily run is tried again this soon rather than tomorrow.
RETRY_SECONDS = 3600


@dataclass(frozen=True)
class Fund:
    """One fund downloaded from Alpaca, and how it is kept."""

    ticker: str
    start: date  # where a fund the warehouse lacks is first downloaded from
    extended_hours: bool = False
    uniform: bool = False  # every regular-hours minute, a flat bar where none printed


FUNDS: dict[str, Fund] = {
    fund.ticker: fund
    for fund in (
        Fund("TQQQ", date(2016, 1, 1)),
        Fund("QQQ", date(2016, 1, 1)),
        Fund("RSP", date(2016, 1, 1), uniform=True),
        Fund("SOXL", date(2016, 1, 1)),
        Fund("SQQQ", date(2016, 1, 1), extended_hours=True),
        Fund("COWZ", date(2016, 12, 19)),  # launched 2016-12-19
        Fund("SPYD", date(2016, 1, 1)),
        Fund("XBI", date(2016, 1, 1)),
        Fund("URSP", date(2025, 8, 27)),  # launched 2025-08-27
        # Broad index funds added 2026-10-22, kept with pre- and after-market
        # bars. Each has traded for decades; Alpaca's minutes begin in 2016.
        Fund("SPY", date(2016, 1, 1), extended_hours=True),  # S&P 500, since 1993
        Fund("IWM", date(2016, 1, 1), extended_hours=True),  # Russell 2000, since 2000
        Fund("EEM", date(2016, 1, 1), extended_hours=True),  # MSCI Emerging Markets, since 2003
    )
}

# Built from other data rather than downloaded; refreshed after FUNDS.
DERIVED = ("URSP_SIM",)


class RefreshError(RuntimeError):
    """A fund could not be refreshed; its stored bars are untouched."""


@dataclass(frozen=True)
class Outcome:
    """What a run did for one fund."""

    ticker: str
    status: str  # current | updated | redownloaded | new | failed
    detail: str = ""
    added: tuple[date, ...] = ()  # sessions the warehouse did not hold before

    def line(self, dry_run: bool = False) -> str:
        status = self.status
        if dry_run and status in ("updated", "redownloaded", "new"):
            status = f"would be {status}"
        return f"{self.ticker:<9}{status:<23}{self.detail}"


# --------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------


def complete_through(now: datetime, extended_hours: bool) -> date:
    """The last session a free account can read whole at `now` (tz-aware)."""
    local = now.astimezone(EASTERN)
    today = local.date()
    close = EXTENDED_CLOSE if extended_hours else REGULAR_CLOSE
    ready = datetime.combine(today, close, tzinfo=EASTERN) + SIP_DELAY
    if is_session(today) and local >= ready:
        return today
    return previous_session(today)


def _sessions_before(day: date, n: int) -> date:
    """The session `n` sessions before `day`."""
    for _ in range(n):
        day = previous_session(day)
    return day


def _as_sessions(days):
    """Session dates as the naive midnights lake.sessions_of gives."""
    import pandas as pd

    return pd.DatetimeIndex([pd.Timestamp(day) for day in days])


def _at(day: date, at: clock_time) -> datetime:
    return datetime.combine(day, at, tzinfo=EASTERN).astimezone(UTC)


def _span(days) -> str:
    days = list(days)
    if not days:
        return "none"
    return f"{days[0]}" if len(days) == 1 else f"{days[0]}..{days[-1]}"


def _sessions(frame) -> list[date]:
    """The sessions (Eastern dates) a frame of bars holds, in order."""
    from engine.warehouse import lake

    return [stamp.date() for stamp in lake.sessions_of(frame.index).unique()]


# --------------------------------------------------------------------
# Alpaca
# --------------------------------------------------------------------


class AlpacaBars:
    """A fund's SIP minute bars from one session through another, asked for a
    month at a time with `pause` seconds before each request after the first.

    `fetcher` is an engine.data.historical_data.AlpacaHistoricalData (any
    object with its fetch_bars(spec) -> (frame, ...) contract).
    """

    def __init__(
        self,
        fetcher: Any,
        *,
        pause: float = PAUSE_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        chunk_days: int = CHUNK_DAYS,
    ) -> None:
        self.fetcher = fetcher
        self.pause = pause
        self.sleep = sleep
        self.chunk_days = chunk_days
        self.requests = 0
        # Stretches Alpaca had no bars for, and what it said.
        self.empty: list[str] = []

    def __call__(self, fund: Fund, first: date, last: date):
        import pandas as pd

        from engine.core.exceptions import DataValidationError
        from engine.data.historical_data import FetchSpec
        from engine.warehouse import lake

        frames = []
        day = first
        while day <= last:
            stop = min(day + timedelta(days=self.chunk_days - 1), last)
            if self.requests:
                self.sleep(self.pause)
            self.requests += 1
            spec = FetchSpec(
                symbol=fund.ticker,
                start=_at(day, clock_time(0, 0)),
                end=_at(stop, EXTENDED_CLOSE if fund.extended_hours else REGULAR_CLOSE),
                timeframe="1Min",
                feed="sip",
                adjustment="all",
                regular_hours_only=not fund.extended_hours,
            )
            try:
                frame, _, _ = self.fetcher.fetch_bars(spec)
            except DataValidationError as e:  # no bars there: before the fund began
                self.empty.append(f"{day}..{stop}: {e}")
            else:
                frames.append(frame)
            day = stop + timedelta(days=1)
        frames = [frame for frame in frames if len(frame)]
        if not frames:
            return lake.empty_bars()
        bars = pd.concat(frames).sort_index()
        bars = bars[~bars.index.duplicated(keep="last")][list(lake.COLUMNS)].copy()
        bars.index = bars.index.tz_convert("UTC").rename("timestamp")
        bars["volume"] = bars["volume"].round().astype("int64")
        return bars


def uniform(bars, before=None):
    """Every regular-hours minute of each session `bars` holds, as RSP is
    kept: a minute with no print is a flat zero-volume bar at the last price.
    `before`, the stored bars ahead of these, gives a session that opens late
    the previous close to carry."""
    import pandas as pd

    from engine.data.historical_data import resample_to_uniform_minutes
    from engine.warehouse import lake

    if bars.empty:
        return bars
    seeded = before is not None and len(before) > 0
    data = pd.concat([before.iloc[-1:], bars]) if seeded else bars
    out, _ = resample_to_uniform_minutes(data, session_start="09:30", session_end="16:00")
    out.index = out.index.tz_convert("UTC").rename("timestamp")
    if seeded:
        out = out[lake.sessions_of(out.index) > lake.sessions_of(before.index[-1:])[0]]
    out = out[list(lake.COLUMNS)].copy()
    out["volume"] = out["volume"].round().astype("int64")
    return out


# --------------------------------------------------------------------
# Comparing stored bars with fresh ones
# --------------------------------------------------------------------


@dataclass(frozen=True)
class Drift:
    """Fresh prices against stored ones, over the bars both hold that
    traded (a uniform fund's flat bars are derived from those)."""

    bars: int
    ratio: float  # median of fresh close / stored close
    differing: float  # share of those bars whose close differs at all

    @property
    def moved(self) -> bool:
        """The adjustment changed -- or nothing could be compared, which is
        no reason to trust the stored bars either."""
        return (
            self.bars == 0 or abs(self.ratio - 1.0) > TOLERANCE or self.differing > CORRECTED_SHARE
        )


def drift(stored, fresh) -> Drift:
    import numpy as np

    common = stored.index.intersection(fresh.index)
    if len(common):
        traded = (stored.loc[common, "volume"].to_numpy() > 0) & (
            fresh.loc[common, "volume"].to_numpy() > 0
        )
        common = common[traded]
    if not len(common):
        return Drift(0, float("nan"), 1.0)
    ratio = fresh.loc[common, "close"].to_numpy(float) / stored.loc[common, "close"].to_numpy(float)
    return Drift(
        len(common), float(np.median(ratio)), float((np.abs(ratio - 1.0) > TOLERANCE).mean())
    )


def changed_bars(stored, fresh) -> int:
    """Bars that differ between two fetches of the same sessions: in one and
    not the other, or with any value changed."""
    import numpy as np

    from engine.warehouse import lake

    a = stored.set_axis(stored.index.as_unit("ns"))
    b = fresh.set_axis(fresh.index.as_unit("ns"))
    common = a.index.intersection(b.index)
    columns = list(lake.COLUMNS)
    same = (a.loc[common, columns].to_numpy(float) == b.loc[common, columns].to_numpy(float)).all(
        axis=1
    )
    return int(len(a) + len(b) - 2 * len(common) + np.count_nonzero(~same))


def adjustment_steps(old, new, limit: int = 4) -> str:
    """How a re-download moved the stored prices: each stretch of sessions
    and the factor it moved by, oldest first. A session or two off on their
    own (a corrected print) are counted, not listed."""
    import numpy as np
    import pandas as pd

    from engine.warehouse import lake

    common = old.index.intersection(new.index)
    if not len(common):
        return "no bars in common"
    ratio = pd.Series(
        new.loc[common, "close"].to_numpy(float) / old.loc[common, "close"].to_numpy(float),
        index=common,
    )
    by_session = ratio.groupby(lake.sessions_of(common)).median()

    def stretches(factors):
        runs: list[list[Any]] = []  # [first, last, factors]
        for session, factor in factors.items():
            # Adjusted prices are rounded, so a factor wobbles in its fourth
            # decimal on a $2 price; a new stretch starts at a real step.
            if runs and abs(factor / np.median(runs[-1][2]) - 1.0) <= 5e-4:
                runs[-1][1] = session
                runs[-1][2].append(factor)
            else:
                runs.append([session, session, [factor]])
        return runs

    runs = stretches(by_session)
    odd = [run for run in runs if len(run[2]) < 3]
    if odd and len(odd) < len(runs):
        runs = stretches(
            by_session.drop([s for run in odd for s in by_session.loc[run[0] : run[1]].index])
        )
    parts = [
        f"{_span([first.date(), last.date()])} x{float(np.median(factors)):.4f}"
        for first, last, factors in runs
    ]
    if len(parts) > limit:
        parts = [*parts[: limit - 1], f"{len(parts) - limit} more", parts[-1]]
    if odd and len(odd) < len(runs) + len(odd):
        days = sum(len(run[2]) for run in odd)
        parts.append(
            f"{days} session{'s' if days > 1 else ''} off on {'their' if days > 1 else 'its'} own"
        )
    return ", ".join(parts)


# --------------------------------------------------------------------
# A fund from Alpaca
# --------------------------------------------------------------------


def _stored_sessions(root: Path, ticker: str, days: list[date]):
    """The fund's stored bars on these sessions."""

    from engine.warehouse import lake

    if not days:
        return lake.empty_bars()
    # An extended session's evening can lie in the next UTC year.
    years = {day.year + offset for day in days for offset in (0, 1)}
    stored = lake.read_bars(root, ticker, years=years)
    return stored[lake.sessions_of(stored.index).isin(_as_sessions(days))]


def _download(fund: Fund, first: date, through: date, fetch: AlpacaBars):
    bars = fetch(fund, first, through)
    return uniform(bars) if fund.uniform else bars


def redownload(
    fund: Fund,
    *,
    root: Path,
    fetch: AlpacaBars,
    through: date,
    counts,
    reason: str,
    dry_run: bool,
) -> Outcome:
    """The fund's whole history again, replacing the stored one -- unless
    the download lacks a session or a bar share the warehouse holds."""
    from engine.warehouse import lake

    first = counts.index[0]
    bars = _download(fund, first, through, fetch)
    held = _sessions(bars)
    have = set(held)
    missing = [day for day in counts.index if day not in have]
    if missing:
        raise RefreshError(
            f"{reason}, but the download lacks {len(missing)} of the {len(counts)} stored "
            f"sessions (the first {missing[0]}); the stored bars are kept"
        )
    on_stored = int(lake.sessions_of(bars.index).isin(_as_sessions(counts.index)).sum())
    if on_stored < KEEP_BARS * int(counts.sum()):
        raise RefreshError(
            f"{reason}, but the download holds {on_stored:,} bars on the stored sessions where "
            f"the warehouse holds {int(counts.sum()):,}; the stored bars are kept"
        )
    steps = adjustment_steps(lake.read_bars(root, fund.ticker), bars)
    if not dry_run:
        lake.replace_fund(root, fund.ticker, bars)
    added = tuple(day for day in held if day > counts.index[-1])
    detail = f"{reason}; {len(held):,} sessions {_span([held[0], held[-1]])}; moved: {steps}"
    if added:
        detail += f"; +{len(added)} new ({_span(added)})"
    return Outcome(fund.ticker, "redownloaded", detail, added)


def refresh_fund(
    fund: Fund,
    *,
    root: Path,
    fetch: AlpacaBars,
    now: datetime,
    dry_run: bool = False,
    force_redownload: bool = False,
) -> Outcome:
    """Bring one fund's bars up to the last complete session."""
    from engine.warehouse import lake

    through = complete_through(now, fund.extended_hours)
    counts = lake.session_counts(root, fund.ticker)

    if counts.empty:
        bars = _download(fund, fund.start, through, fetch)
        if bars.empty:
            raise RefreshError(f"Alpaca has no bars for it from {fund.start} through {through}")
        if not dry_run:
            lake.replace_fund(root, fund.ticker, bars)
        held = _sessions(bars)
        return Outcome(
            fund.ticker, "new", f"{len(held):,} sessions {_span([held[0], held[-1]])}", tuple(held)
        )

    def again(reason: str) -> Outcome:
        return redownload(
            fund,
            root=root,
            fetch=fetch,
            through=through,
            counts=counts,
            reason=reason,
            dry_run=dry_run,
        )

    if force_redownload:
        return again("asked to")

    first, last = counts.index[0], counts.index[-1]
    anchor = drift(_stored_sessions(root, fund.ticker, [first]), fetch(fund, first, first))
    if anchor.moved:
        if anchor.bars:
            return again(f"{first} moved x{anchor.ratio:.6f} (a dividend or split since stored)")
        return again(f"Alpaca's {first} shares no traded bar with the stored one")

    # The last few stored sessions, and any recent session the fund lacks.
    held = set(counts.index)
    recent = sessions_between(_sessions_before(last, LOOKBACK_SESSIONS), last)
    holes = [day for day in recent if day >= first and day not in held]
    overlap = list(counts.index[-OVERLAP_SESSIONS:])
    start = min([overlap[0], *holes])
    if through < start:
        return Outcome(fund.ticker, "current", f"through {last}")

    fresh = fetch(fund, start, through)
    if fund.uniform:
        earlier = [day for day in counts.index if day < start]
        before = _stored_sessions(root, fund.ticker, earlier[-1:])
        fresh = uniform(fresh, before)
    stored = _stored_sessions(root, fund.ticker, [day for day in counts.index if day >= start])
    check = drift(stored, fresh)
    if check.moved:
        return again(
            f"the last sessions moved x{check.ratio:.6f}"
            if check.bars
            else "Alpaca's last sessions share no traded bar with the stored ones"
        )

    fetched = _sessions(fresh)
    added = tuple(day for day in fetched if day not in held)
    absent = [
        day for day in sessions_between(previous_session(start), through) if day not in set(fetched)
    ]
    # Compared where both hold the session: one Alpaca lacks keeps its stored bars.
    both = _as_sessions(day for day in fetched if day in held)
    corrected = changed_bars(
        stored[lake.sessions_of(stored.index).isin(both)],
        fresh[lake.sessions_of(fresh.index).isin(both)],
    )
    notes = []
    if absent:
        notes.append(f"Alpaca has no bars for {_span(absent)}")
    if not added and not corrected:
        return Outcome(fund.ticker, "current", "; ".join([f"through {last}", *notes]))
    if not dry_run:
        lake.update_sessions(root, fund.ticker, fresh)
    detail = [f"+{len(added)} sessions ({_span(added)})" if added else "no new sessions"]
    if corrected:
        detail.append(f"{corrected} stored bars corrected")
    return Outcome(fund.ticker, "updated", "; ".join(detail + notes), added)


# --------------------------------------------------------------------
# URSP_SIM
# --------------------------------------------------------------------


def _ursp_daily(yahoo, through: date):
    from tools import simulate_ursp as S

    real = S.adjusted(yahoo("URSP"), clean=False)
    return real[real.index.date <= through]


def rebuild_ursp_sim(
    *, root: Path, through: date, counts, yahoo, rates, reason: str, dry_run: bool
) -> Outcome:
    """URSP_SIM as tools/simulate_ursp.py --minutes builds it, through
    `through`, replacing the stored series."""
    from engine.warehouse import lake
    from tools import simulate_ursp as S

    rsp_raw, ursp_raw, rate = yahoo("RSP"), yahoo("URSP"), rates()
    rsp_daily = S.adjusted(rsp_raw)
    spread = S.calibrate_spread(rsp_daily, ursp_raw, rate)
    series = S.splice(S.simulate(rsp_daily, rate, spread), rsp_raw, ursp_raw)
    series = series[series.index.date <= through]
    bars = S.minute_bars(series, S.rsp_minute_library(lake.read_bars(root, "RSP")))
    held = _sessions(bars)
    have = set(held)
    missing = [day for day in counts.index if day not in have]
    if missing:
        raise RefreshError(
            f"{reason}, but the rebuild lacks {len(missing)} stored sessions (the first "
            f"{missing[0]}); the stored series is kept"
        )
    if not dry_run:
        lake.replace_fund(root, "URSP_SIM", bars)
    added = tuple(day for day in held if len(counts) == 0 or day > counts.index[-1])
    return Outcome(
        "URSP_SIM",
        "redownloaded" if len(counts) else "new",
        f"{reason}; rebuilt {len(held):,} sessions {_span([held[0], held[-1]])}, spread over "
        f"DFF {spread * 100:.2f}%/yr",
        added,
    )


def refresh_ursp_sim(
    *,
    root: Path,
    now: datetime,
    yahoo,
    rates,
    dry_run: bool = False,
    force_rebuild: bool = False,
) -> Outcome:
    """Append URSP's new sessions to URSP_SIM, drawn on the same day's RSP
    minutes; rebuild it if URSP's adjusted prices moved."""
    import numpy as np

    from engine.warehouse import lake
    from tools import simulate_ursp as S

    rsp = lake.session_counts(root, "RSP")
    if rsp.empty:
        raise RefreshError("it is drawn on RSP's minutes, and the warehouse holds none")
    through = min(complete_through(now, extended_hours=False), rsp.index[-1])
    counts = lake.session_counts(root, "URSP_SIM")

    def rebuild(reason: str) -> Outcome:
        return rebuild_ursp_sim(
            root=root,
            through=through,
            counts=counts,
            yahoo=yahoo,
            rates=rates,
            reason=reason,
            dry_run=dry_run,
        )

    if counts.empty:
        return rebuild("not in the warehouse")
    if force_rebuild:
        return rebuild("asked to")

    real = _ursp_daily(yahoo, through)
    last = counts.index[-1]
    stored = _stored_sessions(root, "URSP_SIM", list(counts.index[-OVERLAP_SESSIONS:]))
    daily = stored.groupby(lake.sessions_of(stored.index)).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    expected = real.reindex(daily.index)[["open", "high", "low", "close"]]
    if expected.isna().to_numpy().any() or not np.allclose(
        daily.to_numpy(float), expected.to_numpy(float), rtol=TOLERANCE, atol=1e-5
    ):
        return rebuild("URSP's adjusted daily bars moved (a dividend?)")

    new = real[real.index.date > last]
    if new.empty:
        return Outcome("URSP_SIM", "current", f"through {last}")
    bars = S.minute_bars(new, S.rsp_minute_library(lake.read_bars(root, "RSP")))
    if not dry_run:
        lake.update_sessions(root, "URSP_SIM", bars)
    added = tuple(_sessions(bars))
    return Outcome("URSP_SIM", "updated", f"+{len(added)} sessions ({_span(added)})", added)


# --------------------------------------------------------------------
# A run
# --------------------------------------------------------------------


def refresh_all(
    tickers: list[str],
    *,
    root: Path,
    fetch: AlpacaBars,
    now: datetime,
    yahoo=None,
    rates=None,
    dry_run: bool = False,
    redownload_tickers: tuple[str, ...] = (),
    report: Callable[[str], None] = print,
) -> list[Outcome]:
    """Refresh `tickers` (Alpaca funds first, then the derived ones), one
    outcome each; a fund that fails leaves its bars as they were and the run
    goes on."""
    from engine.warehouse import lake

    if yahoo is None or rates is None:
        from tools import simulate_ursp as S

        yahoo = yahoo or S.fetch_yahoo_daily
        rates = rates or S.fetch_dff

    outcomes = []
    with lake.refresh_lock(root):
        lake.clean_staging(root)
        for ticker in sorted(tickers, key=_order):
            try:
                if ticker in FUNDS:
                    outcome = refresh_fund(
                        FUNDS[ticker],
                        root=root,
                        fetch=fetch,
                        now=now,
                        dry_run=dry_run,
                        force_redownload=ticker in redownload_tickers,
                    )
                else:
                    outcome = refresh_ursp_sim(
                        root=root,
                        now=now,
                        yahoo=yahoo,
                        rates=rates,
                        dry_run=dry_run,
                        force_rebuild=ticker in redownload_tickers,
                    )
            except Exception as e:  # one fund's failure must not stop the rest
                outcome = Outcome(ticker, "failed", f"{type(e).__name__}: {e}")
            report(outcome.line(dry_run))
            outcomes.append(outcome)
        if not dry_run and any(o.status in ("new", "redownloaded", "updated") for o in outcomes):
            problem = ensure_views(root)
            if problem:
                report(f"[refresh] {problem}")
    return outcomes


def ensure_views(root: Path) -> str | None:
    """A warehouse whose bar lake was empty has no `ohlcv` view
    (schema.refresh_views skips an empty lake), and nothing reads the bars
    until it has one. Creates it; None, or why it could not."""
    import duckdb

    from engine.warehouse.connection import MARKET_DATA_DB, open_warehouse
    from engine.warehouse.schema import initialize, refresh_views

    path = Path(root) / MARKET_DATA_DB
    if path.exists():
        try:
            con = duckdb.connect(str(path), read_only=True)
            try:
                found = con.execute(
                    "SELECT count(*) FROM duckdb_views() WHERE view_name = 'ohlcv'"
                ).fetchone()[0]
            finally:
                con.close()
        except Exception as e:  # held by a writer: a warehouse in use has its views
            return None if "lock" in str(e).lower() else f"could not check the views: {e}"
        if found:
            return None
    try:
        con = open_warehouse(root)
        try:
            initialize(con, root)
            refresh_views(con, root)
        finally:
            con.close()
    except Exception as e:
        return f"the ohlcv view could not be created ({e}); run tools/build_warehouse.py --init"
    return None


def _order(ticker: str) -> int:
    order = [*FUNDS, *DERIVED]
    return order.index(ticker)


def next_run(now: datetime, at: clock_time) -> datetime:
    """The next `at` (Eastern wall clock) after `now`."""
    local = now.astimezone(EASTERN)
    candidate = datetime.combine(local.date(), at, tzinfo=EASTERN)
    if candidate <= local:
        candidate = datetime.combine(local.date() + timedelta(days=1), at, tzinfo=EASTERN)
    return candidate


def run_daily(
    at: clock_time,
    once: Callable[[], bool],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
    report: Callable[[str], None] = print,
) -> None:
    """Run now, then every day at `at`. A run that failed is tried again
    within the hour, never later than the next daily one."""
    while True:
        ok = once()
        wake = next_run(now(), at)
        if not ok:
            wake = min(wake, now() + timedelta(seconds=RETRY_SECONDS))
        report(f"[refresh] next run {wake.astimezone(EASTERN):%Y-%m-%d %H:%M %Z}")
        sleep(max(0.0, (wake - now()).total_seconds()))


# --------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="warehouse directory (default: VAI_WAREHOUSE_DIR, else warehouse/)",
    )
    parser.add_argument(
        "--fund", nargs="+", metavar="TICKER", help="only these funds (default: every one)"
    )
    parser.add_argument(
        "--redownload",
        nargs="+",
        metavar="TICKER",
        default=[],
        help="download these funds' whole history again (URSP_SIM: rebuild it)",
    )
    parser.add_argument("--dry-run", action="store_true", help="fetch and compare, write nothing")
    parser.add_argument(
        "--pause",
        type=float,
        default=PAUSE_SECONDS,
        help=f"seconds between Alpaca requests (default: {PAUSE_SECONDS:g})",
    )
    parser.add_argument(
        "--daily",
        metavar="HH:MM",
        help="run now, then every day at HH:MM Eastern; a failed run is tried again hourly",
    )
    parser.add_argument("--list", action="store_true", help="the funds, and how each is kept")
    return parser


def _describe(ticker: str) -> str:
    if ticker in DERIVED:
        return "derived: URSP's daily bars (Yahoo) drawn on RSP's minutes, after RSP"
    fund = FUNDS[ticker]
    hours = "extended hours" if fund.extended_hours else "regular hours"
    shape = ", every minute" if fund.uniform else ""
    return f"Alpaca SIP, adjusted, {hours}{shape}; from {fund.start} if absent"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    known = [*FUNDS, *DERIVED]
    if args.list:
        for ticker in known:
            print(f"{ticker:<9}{_describe(ticker)}")
        return 0
    unknown = sorted({t.upper() for t in [*(args.fund or []), *args.redownload]} - set(known))
    if unknown:
        parser.error(f"not a tracked fund: {', '.join(unknown)} (tracked: {', '.join(known)})")
    tickers = [t.upper() for t in args.fund] if args.fund else known
    tickers = list(dict.fromkeys([*tickers, *(t.upper() for t in args.redownload)]))
    at = None
    if args.daily:
        try:
            at = datetime.strptime(args.daily, "%H:%M").time()
        except ValueError:
            parser.error(f"--daily wants HH:MM, got {args.daily!r}")

    try:
        import duckdb  # noqa: F401
    except ImportError as e:
        print(
            f"The warehouse needs its optional dependencies: {e}\n"
            "  pip install -r requirements-warehouse.txt",
            file=sys.stderr,
        )
        return 2

    from engine.core.exceptions import ConfigurationError
    from engine.core.secrets import load_live_credentials
    from engine.data.historical_data import AlpacaHistoricalData
    from engine.warehouse import lake
    from engine.warehouse.bars import warehouse_root

    root = args.root or warehouse_root()

    def once() -> bool:
        started = datetime.now(UTC)
        print(
            f"[refresh] {started.astimezone(EASTERN):%Y-%m-%d %H:%M %Z} -- {len(tickers)} funds"
            f" into {root}{' (dry run: nothing is written)' if args.dry_run else ''}"
        )
        try:
            fetch = AlpacaBars(
                AlpacaHistoricalData(credentials=load_live_credentials()), pause=args.pause
            )
        except ConfigurationError as e:
            print(f"[refresh] {e}")
            return False
        try:
            outcomes = refresh_all(
                tickers,
                root=root,
                fetch=fetch,
                now=started,
                dry_run=args.dry_run,
                redownload_tickers=tuple(t.upper() for t in args.redownload),
            )
        except lake.RefreshBusy as e:
            print(f"[refresh] skipped: {e}")
            return True
        failed = [o.ticker for o in outcomes if o.status == "failed"]
        minutes = (datetime.now(UTC) - started).total_seconds() / 60
        print(
            f"[refresh] done in {minutes:.1f} min, {fetch.requests} Alpaca requests"
            + (f"; FAILED: {', '.join(failed)}" if failed else "")
        )
        return not failed

    if at is None:
        return 0 if once() else 1

    def stop(signum, frame):  # PID 1 in a container: SIGTERM has no default action
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    run_daily(at, once)
    return 0


if __name__ == "__main__":
    sys.exit(main())
