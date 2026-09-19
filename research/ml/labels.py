"""What a lot opened at bar i actually went on to do.

--------------------------------------------------------------------
WHY THE LABEL IS MFE, AND NOT FORWARD RETURN

The engine places a limit sell at buy_price * (1 + profit_target) and
fills on TOUCH. So a lot is harvested if the price ever reaches the
target inside the horizon -- whether it closes there is irrelevant. A
bar that spikes through the target and closes back at the entry is a
completed, profitable cycle, and forward return would score it zero.

The quantity that decides the outcome is therefore maximum favourable
excursion: the highest high between the entry and the horizon.

    reached      MFE >= target      -> the cycle completes
    time_to_hit  bars until it does -> how long capital was committed
    mfe          how far it got     -> the regression target
    mae          worst excursion    -> how deep it sat underwater

--------------------------------------------------------------------
WHY ALL FOUR, GIVEN THE OBJECTIVE IS RISK REDUCTION

`reached` alone would rank a lot that hits its target in three bars
equally with one that takes four months. Those are not equally good:
enforce_no_loss means an unreached lot is never sold at a loss, it is
simply HELD -- so the real cost of a bad entry is not a realised loss,
it is capital stranded in a lot that is not working. That is why this
project already measures Stuck Capital Value and Harvest to Stuck
Ratio, and it is why time_to_hit and mae are labels here rather than
diagnostics.

A model trained on `reached` alone optimises for hit rate and will
happily accept four months of dead capital to get it.

--------------------------------------------------------------------
STRICTLY FORWARD-LOOKING, AND THE WINDOW EXCLUDES THE ENTRY BAR

Every window is [i+1, i+horizon]. Including bar i would let a lot be
filled by the same bar that created it, at a high the entry price was
drawn from -- which reads as a free profit and is not one.

The last `horizon` rows of any file have an incomplete window and are
returned as NaN rather than as a short window. A truncated window
biases `reached` downward, and silently: the model would learn that
late-sample entries fail.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LabelSet:
    """Labels for one (profit_target, horizon) pair."""

    profit_target: float
    horizon: int
    reached: np.ndarray
    time_to_hit: np.ndarray
    mfe: np.ndarray
    mae: np.ndarray

    def to_frame(self, index: pd.Index) -> pd.DataFrame:
        suffix = f"t{self.profit_target * 100:g}_h{self.horizon}"
        return pd.DataFrame(
            {
                f"reached_{suffix}": self.reached,
                f"time_to_hit_{suffix}": self.time_to_hit,
                f"mfe_{suffix}": self.mfe,
                f"mae_{suffix}": self.mae,
            },
            index=index,
        )


def _forward_max_levels(values: np.ndarray, horizon: int) -> list[np.ndarray]:
    """Sparse table of forward maxima over windows of 1, 2, 4, ... bars.

    level[k][i] = max(values[i+1 : i+1+2**k])

    Built so time_to_hit can be found by binary lifting instead of by
    scanning. A naive per-bar scan is O(n * horizon), which on a
    1M-bar file with a one-day horizon is 400M comparisons per label
    set; this is O(n log horizon) and fully vectorised.

    float64, deliberately. float32 halves the ~90MB of scratch this
    needs on a 1M-bar file, and was measured against a brute-force
    reference to shift MFE by ~1e-8 -- harmless on its own. But
    `reached` compares these maxima against a float64 target, and a
    limit order resting exactly ON its target is the ordinary case in
    real data rather than a rare one. A rounding error there does not
    perturb a label, it flips it.
    """
    n = values.size
    shifted = np.full(n, -np.inf, dtype=np.float64)
    shifted[:-1] = values[1:]  # window starts at i+1

    levels = [shifted]
    span = 1
    while span < horizon:
        previous = levels[-1]
        combined = previous.copy()
        # max(window at i, window starting span later)
        combined[: n - span] = np.maximum(previous[: n - span], previous[span:])
        levels.append(combined)
        span *= 2
    return levels


def _forward_min(values: np.ndarray, horizon: int) -> np.ndarray:
    """min(values[i+1 : i+1+horizon]), by the same reversal trick."""
    reversed_series = pd.Series(values[::-1])
    rolled = reversed_series.rolling(horizon, min_periods=1).min().to_numpy()[::-1]
    out = np.full(values.size, np.nan, dtype=np.float64)
    out[:-1] = rolled[1:]
    return out


def compute(
    high: np.ndarray,
    low: np.ndarray,
    entry: np.ndarray,
    *,
    profit_target: float,
    horizon: int,
) -> LabelSet:
    """Label every bar as though a lot were opened at `entry`.

    entry is passed separately rather than assumed to be the close: the
    engine buys at a grid level, and labelling against the close would
    describe a trade it does not place.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least one bar")
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    entry = np.asarray(entry, dtype=np.float64)
    n = high.size
    if not (low.size == entry.size == n):
        raise ValueError("high, low and entry must be the same length")

    target = entry * (1.0 + profit_target)
    levels = _forward_max_levels(high, horizon)

    # Binary lifting. `position` walks forward while the running max
    # stays BELOW target; where it stops is the first bar that touches.
    position = np.zeros(n, dtype=np.int64)
    running = np.full(n, -np.inf, dtype=np.float64)
    index = np.arange(n)

    for k in range(len(levels) - 1, -1, -1):
        span = 1 << k
        candidate = np.minimum(index + position, n - 1)
        block = levels[k][candidate]
        combined = np.maximum(running, block)
        # Step only where the target is still not reached AND the step
        # stays inside the horizon.
        step = (combined < target) & (position + span <= horizon)
        running = np.where(step, combined, running)
        position = position + np.where(step, span, 0)

    time_to_hit = (position + 1).astype(np.float64)
    reached = time_to_hit <= horizon

    # MFE over exactly [i+1, i+horizon], as two overlapping blocks.
    #
    # The top level spans 2**ceil(log2(horizon)), which OVERSHOOTS the
    # window whenever horizon is not a power of two -- a horizon of 17
    # would be measured over 32 bars. So the level used is the largest
    # one that FITS, and the window is covered by two blocks of that
    # size: one anchored at the start, one at the end. They overlap,
    # which is harmless for a maximum.
    fitting = max(0, min(len(levels) - 1, int(horizon).bit_length() - 1))
    span = 1 << fitting
    head = levels[fitting]
    tail = levels[fitting][np.minimum(index + (horizon - span), n - 1)]
    mfe = np.maximum(head, tail) / entry - 1.0

    # MAE over the SAME fixed horizon, not "before the target was hit".
    # The fixed-horizon version is cheap and is the honest description
    # of what it measures: how far underwater the position went inside
    # the window, whether or not it had already been harvested.
    mae = _forward_min(low, horizon) / entry - 1.0

    # An incomplete window is not a short window.
    incomplete = np.arange(n) >= n - horizon
    time_to_hit = np.where(reached, time_to_hit, np.nan)
    for array in (mfe, mae, time_to_hit):
        array[incomplete] = np.nan
    reached_float = reached.astype(np.float64)
    reached_float[incomplete] = np.nan

    return LabelSet(
        profit_target=profit_target,
        horizon=horizon,
        reached=reached_float,
        time_to_hit=time_to_hit,
        mfe=mfe,
        mae=mae,
    )


def compute_grid(
    bars: pd.DataFrame,
    *,
    profit_targets: tuple[float, ...],
    horizons: tuple[int, ...],
    entry_column: str = "close",
) -> pd.DataFrame:
    """Label sets for every (target, horizon) pair, in one frame.

    Several targets are labelled at once because the model must be able
    to answer "is THIS target reachable now", and a model trained on a
    single target cannot be asked about another one.
    """
    for column in ("high", "low", entry_column):
        if column not in bars.columns:
            raise ValueError(f"bars is missing {column!r}; have {list(bars.columns)}")

    frames = [
        compute(
            bars["high"].to_numpy(),
            bars["low"].to_numpy(),
            bars[entry_column].to_numpy(),
            profit_target=target,
            horizon=horizon,
        ).to_frame(bars.index)
        for target in profit_targets
        for horizon in horizons
    ]
    return pd.concat(frames, axis=1)
