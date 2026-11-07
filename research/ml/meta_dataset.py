"""The meta-label training set: one row per grid buy the primary signal
would have placed, its features, and what the lot then did.

--------------------------------------------------------------------
META-LABELLING, MAPPED ONTO THE GRID (ledger RK317, RK294, C-ML1)

López de Prado's split of side from size. The PRIMARY signal decides when
to trade and which way; here that is hf_local_reference's buy trigger and
the side is always long. A SECONDARY model learns which of those trades
work. Its label comes from the triple-barrier method, with the barriers
taken from the lot itself:

    upper     entry * (1 + profit_target)   the lot's resting sell, filled on touch
    lower     entry * (1 - stop)            optional: "went this far underwater first"
    vertical  max_hold bars                 capital that is not back by then is stuck

    label = 1 when the upper barrier is touched first, inside max_hold
            0 otherwise (the lower barrier first, or neither in time)

The upper barrier is tested against bar HIGHS and the lower one against
LOWS (research/ml/labels.py's maximum-excursion rule: the sell is a
resting limit and fills on touch, so the close would ask a different
question). A bar that touches both is scored 0: OHLC cannot say which came
first, and the conservative reading costs a label, never a fiction.

--------------------------------------------------------------------
THE EVENTS ARE THE TRIGGER, FROM PRICE ALONE

hf_local_reference buys when the price falls `step` below the higher of
its last fill and a rolling high of closes over `lookback_days`. The last
fill is book state, which depends on how earlier buys were sized and what
cash allowed; the builder cannot reproduce it without running a book. So
the event is the price-only half: a fall of `step` below the rolling high,
which is the strategy's trigger whenever the rolling high is the higher
reference (nearly always: a fill is at or below the high it was measured
from). Each fill model is mirrored exactly:

    close                 close <= high_t * (1 - step), entry at the close
    intrabar, level       low <= high_t * (1 - step),   entry at the level
    intrabar, open_or_level   the same touch,           entry at min(level, open)
    intrabar, causal      the same with high_{t-1},     entry at min(level, open)

(high_t includes bar t's close, as the engine's rolling high does unless
the fill is "causal".) The strategy is asked about a subset of these bars
at most, so the model is trained on every bar it can be asked about.

--------------------------------------------------------------------
OVERLAP, AND THE WEIGHTS THAT ACCOUNT FOR IT

Consecutive triggers share most of their label window, so they are not
independent observations. Each row carries `weight`, its average
uniqueness (AFML ch. 4; ledger RK271): the mean over the bars of its label
window of 1 / (rows whose window covers that bar). The trainer passes it
to LightGBM as a sample weight and purges on (t0, t1). `min_gap_bars`
thins the triggers further when a run has more than it needs.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine.core.config import INTRABAR_FILL_MODES
from engine.core.exceptions import ConfigurationError
from research.ml import labels
from research.ml.meta_features import FEATURE_NAMES, MetaFeatures, session_clock_arrays
from research.strategies.sizing_indicators import bars_from_days

FILL_MODELS: tuple[str, ...] = ("close", "intrabar")


@dataclass(frozen=True)
class PrimarySignal:
    """hf_local_reference's trigger: a fall of `step` below the rolling
    high of closes over `lookback_days`."""

    step: float
    lookback_days: float
    bars_per_day: int
    fill_model: str = "close"
    intrabar_fill: str = "level"

    def __post_init__(self) -> None:
        if not 0 < self.step < 1:
            raise ConfigurationError(f"step must be in (0, 1), got {self.step}")
        if self.fill_model not in FILL_MODELS:
            raise ConfigurationError(f"fill_model must be one of {FILL_MODELS}")
        if self.intrabar_fill not in INTRABAR_FILL_MODES:
            raise ConfigurationError(f"intrabar_fill must be one of {INTRABAR_FILL_MODES}")
        bars_from_days(self.lookback_days, self.bars_per_day)  # validates both

    @property
    def lookback_bars(self) -> int:
        return bars_from_days(self.lookback_days, self.bars_per_day)

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "lookback_days": self.lookback_days,
            "bars_per_day": self.bars_per_day,
            "fill_model": self.fill_model,
            "intrabar_fill": self.intrabar_fill,
        }


@dataclass(frozen=True)
class BarrierLabel:
    """The triple barrier of one lot: its profit target, an optional stop
    (a training label only -- nothing sells there), and a maximum hold."""

    profit_target: float
    max_hold_bars: int
    stop: float | None = None

    def __post_init__(self) -> None:
        if not self.profit_target > 0:
            raise ConfigurationError(f"profit_target must be > 0, got {self.profit_target}")
        if not (isinstance(self.max_hold_bars, int) and self.max_hold_bars >= 1):
            raise ConfigurationError(
                f"max_hold_bars must be an integer >= 1, got {self.max_hold_bars!r}"
            )
        if self.stop is not None and not 0 < self.stop < 1:
            raise ConfigurationError(f"stop must be in (0, 1) or null, got {self.stop}")

    def to_dict(self) -> dict:
        return {
            "profit_target": self.profit_target,
            "max_hold_bars": self.max_hold_bars,
            "stop": self.stop,
        }


def trigger_events(bars: pd.DataFrame, signal: PrimarySignal) -> tuple[np.ndarray, np.ndarray]:
    """(bar positions, entry prices) of every bar the trigger fires on."""
    close = bars["close"].astype(float)
    high_t = close.where(close > 0).rolling(signal.lookback_bars, min_periods=1).max()
    if signal.fill_model == "close":
        level = high_t * (1.0 - signal.step)
        fired = (close <= level).to_numpy(copy=True)
        entry = close.to_numpy(copy=True)
    else:
        reference = high_t.shift(1) if signal.intrabar_fill == "causal" else high_t
        level = (reference * (1.0 - signal.step)).to_numpy()
        low = bars["low"].to_numpy(dtype=float)
        with np.errstate(invalid="ignore"):
            fired = low <= level
        entry = level.copy()
        if signal.intrabar_fill in ("open_or_level", "causal"):
            entry = np.minimum(level, bars["open"].to_numpy(dtype=float))
    fired &= np.isfinite(entry) & (entry > 0)
    positions = np.flatnonzero(fired)
    return positions, entry[positions]


def thin(positions: np.ndarray, min_gap_bars: int) -> np.ndarray:
    """Indices into `positions` keeping events at least `min_gap_bars` apart."""
    if min_gap_bars <= 1 or positions.size == 0:
        return np.arange(positions.size)
    kept, last = [], -(10**18)
    for i, p in enumerate(positions):
        if p - last >= min_gap_bars:
            kept.append(i)
            last = p
    return np.asarray(kept, dtype=np.int64)


def barrier_outcomes(
    bars: pd.DataFrame, positions: np.ndarray, entries: np.ndarray, label: BarrierLabel
) -> pd.DataFrame:
    """label, t1 (the bar the outcome was decided), time_to_hit, mae per
    event. Rows whose window runs past the data are NaN (dropped later):
    a truncated window would bias the label toward 0, silently."""
    n = len(bars)
    horizon = label.max_hold_bars
    high = bars["high"].to_numpy(dtype=float)
    low = bars["low"].to_numpy(dtype=float)
    entry_full = bars["close"].to_numpy(dtype=float).copy()
    entry_full[positions] = entries
    up = labels.compute(high, low, entry_full, profit_target=label.profit_target, horizon=horizon)
    up_time = up.time_to_hit[positions]  # NaN: not reached in time, or incomplete
    complete = ~np.isnan(up.mfe[positions])
    if label.stop is not None:
        # The same first-touch search on negated lows finds the first bar
        # whose low reaches entry * (1 - stop).
        down = labels.compute(-low, -high, -entry_full, profit_target=-label.stop, horizon=horizon)
        dn_time = down.time_to_hit[positions]
    else:
        dn_time = np.full(positions.size, np.nan)
    hit = ~np.isnan(up_time) & (np.isnan(dn_time) | (up_time < dn_time))
    decided = np.fmin(np.fmin(up_time, dn_time), horizon)
    decided = np.where(np.isnan(decided), horizon, decided)
    t1 = np.minimum(positions + decided.astype(np.int64), n - 1)
    out = pd.DataFrame(
        {
            "t0": positions,
            "t1": t1,
            "label": np.where(complete, hit.astype(float), np.nan),
            "time_to_hit": np.where(complete, up_time, np.nan),
            "mae": up.mae[positions],
        }
    )
    return out


def average_uniqueness(t0: np.ndarray, t1: np.ndarray, n_bars: int) -> np.ndarray:
    """AFML's average uniqueness of each label over its window (t0, t1],
    in O(bars + events)."""
    start = np.asarray(t0, dtype=np.int64) + 1
    end = np.maximum(np.asarray(t1, dtype=np.int64), start)  # window [start, end]
    diff = np.zeros(n_bars + 2, dtype=np.int64)
    np.add.at(diff, np.minimum(start, n_bars), 1)
    np.add.at(diff, np.minimum(end + 1, n_bars + 1), -1)
    concurrency = np.cumsum(diff)[: n_bars + 1]
    inverse = np.where(concurrency > 0, 1.0 / np.maximum(concurrency, 1), 0.0)
    prefix = np.concatenate([[0.0], np.cumsum(inverse)])
    start_c = np.minimum(start, n_bars)
    end_c = np.minimum(end, n_bars)
    span = np.maximum(end_c - start_c + 1, 1)
    # A prefix-sum difference can overshoot 1 by a rounding error.
    return np.clip((prefix[end_c + 1] - prefix[start_c]) / span, 0.0, 1.0)


def feature_rows(
    bars: pd.DataFrame, positions: np.ndarray, entries: np.ndarray, signal: PrimarySignal
) -> np.ndarray:
    """Feature vectors at `positions`, by walking every bar through
    MetaFeatures in the strategy's order: snapshot(t) then fold(t)."""
    features = MetaFeatures(signal.bars_per_day, signal.lookback_bars)
    day, minute, weekday = session_clock_arrays(pd.DatetimeIndex(bars.index))
    o = bars["open"].to_numpy(dtype=float)
    h = bars["high"].to_numpy(dtype=float)
    lo = bars["low"].to_numpy(dtype=float)
    c = bars["close"].to_numpy(dtype=float)
    rows = np.empty((positions.size, len(FEATURE_NAMES)), dtype=np.float64)
    want = iter(zip(positions.tolist(), entries.tolist(), strict=True))
    nxt = next(want, None)
    k = 0
    for t in range(len(bars)):
        if nxt is not None and nxt[0] == t:
            rows[k] = features.snapshot(
                int(day[t]), float(minute[t]), int(weekday[t]), o[t], nxt[1]
            )
            k += 1
            nxt = next(want, None)
        features.fold(int(day[t]), o[t], h[t], lo[t], c[t])
    return rows


def build_dataset(
    bars: pd.DataFrame,
    signal: PrimarySignal,
    label: BarrierLabel,
    *,
    min_gap_bars: int = 1,
) -> pd.DataFrame:
    """Features, label and bookkeeping for every trigger whose outcome is
    known: FEATURE_NAMES..., t0, t1, ts0, ts1, entry, label, time_to_hit,
    mae, weight. Sorted by t0."""
    missing = {"open", "high", "low", "close"} - set(bars.columns)
    if missing:
        raise ConfigurationError(f"bars are missing {sorted(missing)}")
    if not isinstance(bars.index, pd.DatetimeIndex) or not bars.index.is_monotonic_increasing:
        raise ConfigurationError("bars need a sorted DatetimeIndex")
    positions, entries = trigger_events(bars, signal)
    keep = thin(positions, min_gap_bars)
    positions, entries = positions[keep], entries[keep]
    outcomes = barrier_outcomes(bars, positions, entries, label)
    known = outcomes["label"].notna().to_numpy()
    positions, entries, outcomes = positions[known], entries[known], outcomes[known]
    columns = list(FEATURE_NAMES)
    frame = pd.DataFrame(feature_rows(bars, positions, entries, signal), columns=columns)
    for name in ("t0", "t1", "label", "time_to_hit", "mae"):
        frame[name] = outcomes[name].to_numpy()
    frame["t0"] = frame["t0"].astype(np.int64)
    frame["t1"] = frame["t1"].astype(np.int64)
    frame["label"] = frame["label"].astype(np.int64)
    index = pd.DatetimeIndex(bars.index)
    frame["ts0"] = index[frame["t0"].to_numpy()]
    frame["ts1"] = index[frame["t1"].to_numpy()]
    frame["entry"] = entries
    frame["weight"] = average_uniqueness(frame["t0"].to_numpy(), frame["t1"].to_numpy(), len(bars))
    return frame


__all__ = [
    "FILL_MODELS",
    "BarrierLabel",
    "PrimarySignal",
    "average_uniqueness",
    "barrier_outcomes",
    "build_dataset",
    "feature_rows",
    "thin",
    "trigger_events",
]
