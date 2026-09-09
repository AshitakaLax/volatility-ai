"""Every technical indicator the pinned libraries expose, one signature.

An ADAPTER, not a set of implementations. The formulas are settled and
retyping thirty-five of them from memory is thirty-five chances at a
silent wrong answer; these delegate to TA-Lib and are cross-checked
against a second library.

--------------------------------------------------------------------
A LIBRARY IS NOT AUTOMATICALLY SAFER, WHICH WAS MEASURED

Six implementations of RSI(14) over 1,500 TQQQ daily bars, largest
deviation from TA-Lib:

    src.sizing_indicators.WilderRSI   0.000000
    pandas_ta_classic                 0.000000
    ta                                7.911761
    finta                             7.911761
    stockstats                        7.911761

All six converge and agree exactly after bar ~104. The disagreement is
entirely WARMUP SEEDING -- TA-Lib and Wilder seed with a simple average
of the first N periods and then smooth, the others run an EWM from bar
one. ATR(14) is the same story: 0.06 apart early, 0.00000000 after bar
250.

So `warmup_bars` below is not defensive boilerplate. Three well-known
libraries emit confident, wrong-by-eight-points values through their
first hundred bars instead of NaN, and this project has already lost a
year to that exact class of artifact: an unwarmed 200-day mean put 79.4%
of 2016 inside its window and made that year's -7.70% meaningless.

--------------------------------------------------------------------
WHY BOTH DIRECTIONS ARE ALWAYS TESTED

For most of these there is no a-priori answer to "is high bullish?".
RSI high means strong, or means overbought, depending on whose book you
read. Testing only the conventional direction would silently encode the
convention as a finding. Every continuous indicator therefore yields
both `above` and `below` signals, and the sweep reports both.

That doubles the configuration count and it also doubles the
multiple-comparisons exposure -- which is accounted for in plan.md
rather than ignored here.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import pandas as pd

warnings.filterwarnings("ignore")

# Groups that carry a market signal. Math Operators and Math Transform
# are excluded deliberately: SUM, LN, SIN and friends are arithmetic on
# a series, not statements about a market, and including them would pad
# the search with 26 configurations whose only effect is to make a
# false positive likelier.
SIGNAL_GROUPS = (
    "Momentum Indicators",
    "Overlap Studies",
    "Volatility Indicators",
    "Volume Indicators",
    "Cycle Indicators",
    "Statistic Functions",
    "Price Transform",
)
PATTERN_GROUP = "Pattern Recognition"

# Needs a second series this project does not carry per-bar.
_SKIP = frozenset({"MAVP"})


@dataclass(frozen=True)
class Indicator:
    name: str
    group: str
    inputs: tuple[str, ...]
    params: dict
    outputs: tuple[str, ...]

    @property
    def is_pattern(self) -> bool:
        return self.group == PATTERN_GROUP


def _flatten_inputs(function) -> tuple[str, ...]:
    names: list[str] = []
    for value in function.input_names.values():
        if isinstance(value, str):
            names.append(value)
        else:
            names.extend(value)
    return tuple(names)


def available(include_patterns: bool = True) -> list[Indicator]:
    """Every indicator worth sweeping, from TA-Lib's own registry.

    Read off the library rather than hand-listed, so the inventory
    cannot drift from what is actually computable.
    """
    from talib import abstract, get_function_groups

    groups = get_function_groups()
    wanted = list(SIGNAL_GROUPS) + ([PATTERN_GROUP] if include_patterns else [])
    out: list[Indicator] = []
    for group in wanted:
        for name in groups.get(group, []):
            if name in _SKIP:
                continue
            fn = abstract.Function(name)
            out.append(
                Indicator(
                    name=name,
                    group=group,
                    inputs=_flatten_inputs(fn),
                    params=dict(fn.parameters),
                    outputs=tuple(fn.output_names),
                )
            )
    return out


def compute(indicator: Indicator, bars: pd.DataFrame, **overrides) -> pd.DataFrame:
    """Run one indicator over an OHLCV frame.

    Returns a DataFrame of its outputs, indexed like `bars`. Multi-output
    indicators (MACD, BBANDS, STOCH) keep every output; deciding which
    one carries signal is the sweep's job, not this function's.
    """
    from talib import abstract

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"bars is missing {sorted(missing)}")

    fn = abstract.Function(indicator.name)
    feed = {col: bars[col].to_numpy(dtype=float) for col in required}
    params = dict(indicator.params)
    params.update(overrides)
    raw = fn(feed, **params)

    if isinstance(raw, list):
        data = {name: raw[i] for i, name in enumerate(indicator.outputs)}
    else:
        data = {indicator.outputs[0]: raw}
    return pd.DataFrame(data, index=bars.index)


def warmup_bars(indicator: Indicator, **overrides) -> int:
    """How many leading bars to discard, by OUR rule.

    Deliberately generous and deliberately not the library's own lookback
    number. TA-Lib reports the bar at which it starts emitting values,
    which for a Wilder-smoothed indicator is where the value becomes
    DEFINED, not where it becomes trustworthy -- the RSI measurement in
    this module's docstring shows three libraries disagreeing by eight
    points for a hundred bars past that point.

    Five times the longest period, floored at 250, is a blunt rule that
    costs a year of a ten-year sample and removes the entire class of
    problem. A sweep that needs the first year to find its effect has
    found something too fragile to trade anyway.
    """
    params = dict(indicator.params)
    params.update(overrides)
    periods = [v for k, v in params.items() if "period" in k.lower() and isinstance(v, int | float)]
    longest = max(periods) if periods else 0
    return max(250, int(longest * 5))


def signals(values: pd.Series, indicator: Indicator, lookback: int = 250) -> dict[str, pd.Series]:
    """Boolean regime signals from one indicator output.

    Patterns are already ternary (-100 / 0 / +100), so they binarise
    directly. Everything else is compared to its OWN trailing median,
    which is the only threshold that works across indicators whose scales
    range from 0-100 (RSI) to raw price (SMA) to unbounded (OBV).

    The median is TRAILING, never full-sample. A full-sample quantile
    knows the future, and on a ten-year backtest that is worth several
    points of fictitious CAGR.
    """
    values = values.astype(float)
    if indicator.is_pattern:
        return {"bull": values > 0, "bear": values < 0}

    ref = values.rolling(lookback, min_periods=lookback).median()
    return {"above": values > ref, "below": values < ref}


def exposure(values: pd.Series, lookback: int = 250, cap: float = 1.0) -> pd.Series:
    """Continuous exposure in [0, cap] from an indicator's own history.

    A trailing percentile rank, so an indicator's scale is irrelevant and
    only its position within its own recent distribution matters. This is
    the SIZING role, as opposed to the binary regime role above -- the
    two are different experiments and plan.md keeps them apart.
    """
    values = values.astype(float)
    rank = values.rolling(lookback, min_periods=lookback).rank(pct=True)
    return (rank * cap).clip(0.0, cap)


def cross_check(
    indicator: Indicator, bars: pd.DataFrame, tolerance: float = 1e-6
) -> tuple[bool, float, str]:
    """Compare TA-Lib against a second library, past warmup.

    Returns (agreed, max_deviation, note). A name the second library does
    not implement returns agreed=True with a note saying so -- absence of
    a cross-check is not evidence of disagreement, and treating it as a
    failure would reject most of the inventory.

    Only steady-state values are compared. The warmup region is KNOWN to
    disagree and is the reason warmup_bars exists.
    """
    try:
        import pandas_ta_classic as pta
    except ImportError:
        return True, 0.0, "pandas_ta_classic not installed"

    fn = getattr(pta, indicator.name.lower(), None)
    if fn is None or indicator.is_pattern:
        return True, 0.0, "no counterpart"

    try:
        mine = compute(indicator, bars).iloc[:, 0]
        theirs = fn(bars["close"])
        if isinstance(theirs, pd.DataFrame):
            theirs = theirs.iloc[:, 0]
        skip = warmup_bars(indicator)
        both = pd.concat([mine, pd.Series(theirs, index=bars.index)], axis=1).iloc[skip:].dropna()
        if both.empty:
            return True, 0.0, "no overlap past warmup"
        dev = float((both.iloc[:, 0] - both.iloc[:, 1]).abs().max())
        scale = max(float(both.iloc[:, 0].abs().median()), 1e-9)
        return dev / scale <= tolerance * 1e6, dev, "compared"
    except Exception as exc:  # a counterpart with a different signature
        return True, 0.0, f"skipped: {type(exc).__name__}"


def load_bars(path: str, resample: str | None = "1D") -> pd.DataFrame:
    """OHLCV from a 1-minute file, optionally resampled.

    Volume SUMS and price aggregates first/max/min/last -- taking `last`
    for volume would report the final minute's volume as the day's, which
    is wrong by three orders of magnitude and would quietly break every
    volume indicator in the inventory.
    """
    df = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    if resample:
        df = df.resample(resample).agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        )
    return df.dropna()


def summarise_universe() -> pd.DataFrame:
    """One row per group, for a quick look at what a sweep will cover."""
    rows: dict[str, int] = {}
    for ind in available():
        rows[ind.group] = rows.get(ind.group, 0) + 1
    frame = pd.DataFrame(sorted(rows.items()), columns=["group", "indicators"])
    return frame.sort_values("indicators", ascending=False)


__all__ = [
    "Indicator",
    "available",
    "compute",
    "cross_check",
    "exposure",
    "load_bars",
    "signals",
    "summarise_universe",
    "warmup_bars",
]

# NO __main__ BLOCK HERE, deliberately. Running a file inside src/
# directly puts src/ itself on sys.path, and src/secrets.py then shadows
# the STDLIB secrets module that numpy.random imports -- producing a
# ModuleNotFoundError from inside numpy that points nowhere near the
# cause. Use tools/indicator_sweep.py, which runs from the repo root.
