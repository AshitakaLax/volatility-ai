"""
The risk governor: outside warnings that pause NEW buying
(docs/research/risk-governor.md).

The Ultimate family decides calm or turbulent from the fund's own range
(natr_regime.py). This reads what the fund's bars cannot show -- implied
volatility, credit, the leading sector, the index trend, the Office of
Financial Research's stress index -- as a handful of yes/no warnings, one
vote each. When at least `min_votes` of them are raised for a session, the
calm grid buys nothing that session. It sells as usual, nothing is
liquidated, and the regime is untouched.

--------------------------------------------------------------------
WHY A PAUSE AND NOT A REGIME

Measured on the reserve configuration through the minute-bar engine
(tools/probe_risk_governor.py; the write-up has the tables):

  as a veto on calm     every warning ANDed into the NATR flag costs
                        return and leaves the drawdown where it was. A
                        flip sells the calm book below cost, and the
                        drawdown it was meant to avoid happens inside
                        calm spells.
  as an override        staying in the market when NATR says turbulent
                        but the outside reads benign is far worse: the
                        grid's small steps are sized for narrow ranges.
  as a pause            the one form that helps, and only as a consensus.
                        One warning alone pauses too often and costs
                        return.

--------------------------------------------------------------------
POINT IN TIME

Every series is `timestamp,close` as research/ml/sources.py writes it: the
stamp is the moment the value could first be read, its publication lag
already in it. A session reads the latest value stamped before
SESSION_CUTOFF_UTC of its own date -- 04:00 UTC, midnight in New York in
summer and an hour before it in winter -- so nothing a session sees was
published during it. Rolling windows count sessions (the NYSE calendar),
and each includes the reading itself.

--------------------------------------------------------------------
STALE DATA ABSTAINS

The files are kept current by tools/refresh_external.py, a service that
can stop. A warning whose newest input reading is more than its
`max_age_days` old at a session casts no vote and is listed as stale. With
too few fresh warnings the pause cannot be reached, so a dead feed returns
the strategy to what it does without a governor, the configuration that
was measured on its own. It is never frozen in whatever state the last
download left. An input file that is missing altogether is a
configuration error, raised when the governor is built.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from engine.core.trading_calendar import sessions_between

SESSION_CUTOFF_UTC = 4  # hour of the session's own date; see POINT IN TIME
# The exchange calendar is modelled from 2001 (engine/core/trading_calendar).
FIRST_SESSION = date(2005, 1, 3)
EXTERNAL_DIR_ENV = "VAI_EXTERNAL_DIR"

DAILY_MAX_AGE = 7  # days: a long weekend and a missed refresh
WEEKLY_MAX_AGE = 14


def _above_median(x: pd.Series, n: int) -> pd.Series:
    reference = x.rolling(n, min_periods=n).median()
    return (x > reference).where(reference.notna())


def _below_mean(x: pd.Series, n: int) -> pd.Series:
    reference = x.rolling(n, min_periods=n).mean()
    return (x < reference).where(reference.notna())


def _vxn_hi(vxn: pd.Series) -> pd.Series:
    return _above_median(vxn, 100)


def _sox_weak(sox: pd.Series, ndx: pd.Series) -> pd.Series:
    return _below_mean(sox / ndx, 100)


def _credit(hyg: pd.Series, ief: pd.Series) -> pd.Series:
    return _below_mean(hyg / ief, 100)


def _trend100(qqq: pd.Series) -> pd.Series:
    return _below_mean(qqq, 100)


def _fsi_rising(fsi: pd.Series) -> pd.Series:
    reference = fsi.rolling(20, min_periods=20).mean()
    return (fsi > reference + 0.3).where(reference.notna())


def _dxy_up(dxy: pd.Series) -> pd.Series:
    reference = dxy.rolling(100, min_periods=100).mean()
    return (dxy >= reference).where(reference.notna())


def _move_hi(move: pd.Series) -> pd.Series:
    return _above_median(move, 100)


def _nfci_tight(nfci: pd.Series) -> pd.Series:
    reference = nfci.rolling(260, min_periods=200).median()
    return (nfci > reference).where(reference.notna())


def _term_flat(vix: pd.Series, vix3m: pd.Series) -> pd.Series:
    ratio = vix / vix3m
    return (ratio > 0.95).where(ratio.notna())


def _cor1m_hi(cor: pd.Series) -> pd.Series:
    return _above_median(cor, 100)


def _gex_low(gex: pd.Series) -> pd.Series:
    reference = gex.rolling(250, min_periods=250).quantile(0.2)
    return (gex < reference).where(reference.notna())


@dataclass(frozen=True)
class Signal:
    """One warning: its input series (research/ml/sources.py file keys), the
    rule that raises it, and how old its newest reading may be."""

    name: str
    inputs: tuple[str, ...]
    description: str
    rule: Callable[..., pd.Series]
    max_age_days: int = DAILY_MAX_AGE


SIGNALS: dict[str, Signal] = {
    s.name: s
    for s in (
        Signal(
            "vxn_hi",
            ("cboe_VXN",),
            "Nasdaq-100 implied volatility above its 100-session median",
            _vxn_hi,
        ),
        Signal(
            "sox_weak",
            ("yahoo_SOX", "yahoo_NDX"),
            "semiconductors lagging the Nasdaq-100: SOX/NDX below its 100-session mean",
            _sox_weak,
        ),
        Signal(
            "credit",
            ("yahoo_HYG", "yahoo_IEF"),
            "high yield lagging Treasuries: HYG/IEF below its 100-session mean",
            _credit,
        ),
        Signal(
            "trend100",
            ("yahoo_QQQ",),
            "QQQ below its 100-session mean",
            _trend100,
        ),
        Signal(
            "fsi_rising",
            ("ofr_FSI",),
            "OFR financial stress index 0.3 above its 20-session mean",
            _fsi_rising,
        ),
        Signal(
            "dxy_up",
            ("yahoo_DXY",),
            "US dollar index at or above its 100-session mean",
            _dxy_up,
        ),
        Signal(
            "move_hi",
            ("yahoo_MOVE",),
            "Treasury implied volatility (MOVE) above its 100-session median",
            _move_hi,
        ),
        Signal(
            "nfci_tight",
            ("fred_NFCI",),
            "Chicago Fed financial conditions tighter than their one-year median",
            _nfci_tight,
            WEEKLY_MAX_AGE,
        ),
        Signal(
            "term_flat",
            ("cboe_VIX", "cboe_VIX3M"),
            "VIX above 0.95 of three-month VIX: the term structure flat or inverted",
            _term_flat,
        ),
        Signal(
            "cor1m_hi",
            ("cboe_COR1M",),
            "S&P 500 implied correlation above its 100-session median",
            _cor1m_hi,
        ),
        Signal(
            "gex_low",
            ("squeeze_GEX",),
            "dealer gamma in the lowest fifth of its last 250 sessions",
            _gex_low,
        ),
    )
}

# The measured choice (docs/research/risk-governor.md): five warnings from
# five different corners of the market, paused when four agree.
CORE_SIGNALS: tuple[str, ...] = ("vxn_hi", "sox_weak", "credit", "trend100", "fsi_rising")
CORE_MIN_VOTES = 4


@dataclass(frozen=True)
class Reading:
    """What the governor says of one session."""

    session: date
    votes: int  # warnings raised
    known: int  # warnings with a fresh reading
    raised: tuple[str, ...]
    stale: tuple[str, ...]
    paused: bool


def parse_signals(signals: str | Iterable[str]) -> tuple[str, ...]:
    """Signal names from a comma-separated string or a sequence, checked."""
    if isinstance(signals, str):
        names = tuple(part.strip() for part in signals.split(",") if part.strip())
    else:
        names = tuple(str(part) for part in signals)
    unknown = sorted(set(names) - set(SIGNALS))
    if unknown:
        raise ConfigurationError(
            f"unknown governor signal(s) {unknown}; known: {', '.join(SIGNALS)}"
        )
    if not names or len(set(names)) != len(names):
        raise ConfigurationError(f"governor signals must be distinct and not empty, got {names}")
    return names


def external_directory(directory: str | Path | None = None) -> Path:
    """Where the outside series live: `directory`, else VAI_EXTERNAL_DIR,
    else research/ml/sources.py's data/external/."""
    if directory:
        return Path(directory)
    named = os.environ.get(EXTERNAL_DIR_ENV)
    if named:
        return Path(named)
    from research.ml.sources import default_directory

    return default_directory()


def read_series(path: Path) -> pd.Series:
    """One `timestamp,close` file as a Series on its UTC stamps."""
    frame = pd.read_csv(path, usecols=["timestamp", "close"])
    stamps = pd.to_datetime(frame["timestamp"], utc=True)
    values = pd.to_numeric(frame["close"], errors="coerce")
    series = pd.Series(values.to_numpy(float), index=pd.DatetimeIndex(stamps)).dropna()
    return series[~series.index.duplicated(keep="last")].sort_index()


class RiskGovernor:
    """`min_votes` of `signals` raised for a session pause its new buying.

    `series` maps each input key to its stamped Series. `reading(day)` and
    `paused(day)` answer for any session from FIRST_SESSION on; a session
    past the data reads the latest values, each subject to its age limit.
    """

    def __init__(
        self,
        series: Mapping[str, pd.Series],
        *,
        signals: str | Iterable[str] = CORE_SIGNALS,
        min_votes: int = CORE_MIN_VOTES,
        stale_days: int | None = None,
    ) -> None:
        self.signals = parse_signals(signals)
        if isinstance(min_votes, bool) or int(min_votes) != min_votes:
            raise ConfigurationError(f"min_votes must be a whole number, got {min_votes!r}")
        self.min_votes = int(min_votes)
        if not 1 <= self.min_votes <= len(self.signals):
            raise ConfigurationError(
                f"min_votes must be between 1 and the {len(self.signals)} signals, "
                f"got {self.min_votes}"
            )
        if stale_days is not None and (isinstance(stale_days, bool) or stale_days < 1):
            raise ConfigurationError(f"stale_days must be at least 1, got {stale_days!r}")
        self.stale_days = stale_days
        needed = sorted({key for name in self.signals for key in SIGNALS[name].inputs})
        missing = [key for key in needed if key not in series or len(series[key]) == 0]
        if missing:
            raise ConfigurationError(
                f"the risk governor has no data for {missing}: run tools/refresh_external.py"
            )
        self._series: dict[str, pd.Series] = {}
        for key in needed:
            s = series[key]
            if not isinstance(s.index, pd.DatetimeIndex) or s.index.tz is None:
                raise ConfigurationError(f"governor series {key} needs tz-aware UTC stamps")
            self._series[key] = s.sort_index()
        self._table: pd.DataFrame | None = None
        self._through: date | None = None

    @classmethod
    def from_directory(cls, directory: str | Path | None = None, **options) -> RiskGovernor:
        """Built from `<key>.csv` files in `directory` (external_directory())."""
        names = parse_signals(options.get("signals", CORE_SIGNALS))
        root = external_directory(directory)
        series: dict[str, pd.Series] = {}
        for key in sorted({key for name in names for key in SIGNALS[name].inputs}):
            path = root / f"{key}.csv"
            if path.exists():
                series[key] = read_series(path)
        try:
            return cls(series, **options)
        except ConfigurationError as exc:
            raise ConfigurationError(f"{exc} (looked in {root})") from exc

    # ------------------------------------------------------------ the table

    def _aligned(self, key: str, cutoffs: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
        """For each session cutoff: the latest value stamped at or before
        it, and that value's age in days. NaN where there is none yet."""
        s = self._series[key]
        pos = s.index.searchsorted(cutoffs, side="right") - 1
        have = pos >= 0
        at = np.clip(pos, 0, None)
        values = np.where(have, s.to_numpy(float)[at], np.nan)
        age = (cutoffs - s.index[at]) / pd.Timedelta(days=1)
        return values, np.where(have, np.asarray(age, dtype=float), np.nan)

    def _build(self, through: date) -> pd.DataFrame:
        days = sessions_between(FIRST_SESSION - timedelta(days=1), through)
        index = pd.DatetimeIndex(pd.to_datetime(days))
        cutoffs = index.tz_localize("UTC") + pd.Timedelta(hours=SESSION_CUTOFF_UTC)
        aligned = {key: self._aligned(key, cutoffs) for key in self._series}
        columns: dict[str, pd.Series] = {}
        for name in self.signals:
            signal = SIGNALS[name]
            limit = self.stale_days if self.stale_days is not None else signal.max_age_days
            inputs = [pd.Series(aligned[key][0], index=index) for key in signal.inputs]
            raised = signal.rule(*inputs).astype(float)
            age = np.maximum.reduce([aligned[key][1] for key in signal.inputs])
            fresh = pd.Series(age <= limit, index=index)  # NaN age compares False
            # 1.0 raised, 0.0 clear, NaN no vote (warming up, or stale)
            columns[name] = raised.where(fresh)
        table = pd.DataFrame(columns, index=index)
        table["votes"] = table[list(self.signals)].sum(axis=1).astype(int)
        table["known"] = table[list(self.signals)].notna().sum(axis=1).astype(int)
        table["paused"] = table["votes"] >= self.min_votes
        return table

    def table(self, through: date | None = None) -> pd.DataFrame:
        """One row a session through `through` (default: the newest stamp's
        date): each signal as 1.0 raised / 0.0 clear / NaN no vote, then
        votes, known and paused."""
        if through is None:
            through = max(s.index[-1] for s in self._series.values()).date()
        if self._table is None or self._through is None or through > self._through:
            self._table, self._through = self._build(through), through
        return self._table

    def reading(self, day: date) -> Reading:
        """The governor's word on session `day`."""
        if day < FIRST_SESSION:
            return Reading(day, 0, 0, (), tuple(self.signals), False)
        table = self.table(max(day, self._through or day))
        stamp = pd.Timestamp(day)
        if stamp not in table.index:  # not a session: answer as the next one would
            row = self._build(day + timedelta(days=7)).loc[stamp:].iloc[0]
        else:
            row = table.loc[stamp]
        raised = tuple(n for n in self.signals if row[n] == 1.0)
        stale = tuple(n for n in self.signals if pd.isna(row[n]))
        return Reading(
            day, int(row["votes"]), int(row["known"]), raised, stale, bool(row["paused"])
        )

    def paused(self, day: date) -> bool:
        return self.reading(day).paused

    def paused_by_date(self, first: date | None = None, through: date | None = None) -> dict:
        """{session: True} for every paused session in the window."""
        table = self.table(through)
        paused = table.index[table["paused"].to_numpy()]
        return {
            ts.date(): True
            for ts in paused
            if (first is None or ts.date() >= first) and (through is None or ts.date() <= through)
        }


__all__ = [
    "CORE_MIN_VOTES",
    "CORE_SIGNALS",
    "EXTERNAL_DIR_ENV",
    "FIRST_SESSION",
    "SESSION_CUTOFF_UTC",
    "SIGNALS",
    "Reading",
    "RiskGovernor",
    "Signal",
    "external_directory",
    "parse_signals",
    "read_series",
]
