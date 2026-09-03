"""
Shared plumbing for the research probes in tools/.

--------------------------------------------------------------------
WHY THIS EXISTS

Three things were copied across this directory rather than shared, and
each copy was a chance to diverge silently:

  * THE ESCALATING STRATEGY, defined independently in three probes.
    They were verified equivalent -- identical returns and trade counts
    to ten decimal places over the 2020 episode -- so every cross-probe
    comparison in this project is valid. But three copies that agree
    today are three chances to disagree tomorrow, and the failure mode
    is not an error: it is two results that look comparable and are not.

  * THE ESCALATION FORMULA itself, `max_mult ** (dd / dd_ref)`, written
    out in seven files.

  * DATASET LOADING, in eight probes, each reading a 60 MB CSV with
    parse_dates at 2.5s a time.

The strategy consolidation is the one that matters for correctness. The
loader is a convenience that happens to pay for itself.

--------------------------------------------------------------------
THE PARQUET CACHE

read_csv with parse_dates costs 2.5s on the 1,035,332-row TQQQ file;
the same frame from parquet costs 0.4s. The cache is written beside the
CSV on first use and keyed on the source file's mtime and size, so an
updated CSV invalidates it rather than being silently ignored -- a
stale cache would mean probes quietly measuring last week's data.

It is a CACHE, not a store: deleting the .parquet files costs 2.5s and
nothing else, and `data/` is gitignored either way.

--------------------------------------------------------------------
WHAT IS NOT HERE

The bootstrap that puts the repo root on sys.path stays in each script.
It has to run before this module can be imported, so it cannot live in
this module -- and the alternatives (a sitecustomize, a package
__init__ that only works under `python -m`) each break one of the two
ways these scripts are actually run.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import BacktestConfig
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing

# The datasets the probes share. Named here so a path change is one edit
# rather than eight, and so a typo fails at import rather than in the
# middle of a sweep.
TQQQ = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
SQQQ = "data/SQQQ_rth_full.csv"
VIXY = "data/VIXY_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"
PROBE_CONFIG = "config/probe_dipbuy_full.yaml"


class Escalating(HighFrequencyLocalReferenceSizing):
    """Lot size scales log-linearly with the UNDERLYING's drawdown.

    Against the underlying's own trailing peak, NOT the portfolio's --
    the portfolio's drawdown stays near zero while the book is mostly
    cash, so sizing off it would never escalate at all. That distinction
    is the whole point of the strategy and is the thing most easily got
    wrong when re-typing it.

    max_mult=1.0 disables escalation entirely and is the control used to
    separate "the escalation is working" from "the step and target are
    working". It short-circuits rather than computing 1.0 ** x, which is
    the same number by a slower route.

    THE CANONICAL DEFINITION. Three copies of this previously lived in
    probe_downturn_tactics, probe_escalating_risk and probe_regime_combo;
    tests/unit/test_tools_are_importable.py verified they computed
    identical lot sizes before they were replaced by this one.
    """

    def __init__(self, *args, max_mult: float = 1.0, dd_ref: float = 0.75, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_mult, self.dd_ref = max_mult, dd_ref
        self._price_peak: float | None = None

    def record_tick(self, context) -> None:
        super().record_tick(context)
        if context.price > 0:
            self._price_peak = (
                context.price if self._price_peak is None else max(self._price_peak, context.price)
            )

    def calculate_trade_value(self, context) -> float:
        base = super().calculate_trade_value(context)
        return base * escalation(context.price, self._price_peak, self.max_mult, self.dd_ref)


def escalation(price: float, peak: float | None, max_mult: float, dd_ref: float) -> float:
    """The multiplier, as a function rather than a formula to re-type.

    Returns 1.0 (no escalation) when there is no peak yet, no drawdown,
    or escalation is disabled. Saturates at max_mult once the drawdown
    reaches dd_ref, so the caller never has to remember the clamp.
    """
    if max_mult <= 1.0 or not peak:
        return 1.0
    drawdown = 1.0 - price / peak
    if drawdown <= 0:
        return 1.0
    return min(max_mult, max_mult ** (drawdown / dd_ref))


def load_bars(path: str = TQQQ, *, use_cache: bool = True) -> pd.DataFrame:
    """Minute bars, timestamp-indexed, via a parquet cache.

    The cache is keyed on the SOURCE file's mtime and size. A refreshed
    CSV therefore rebuilds it rather than being silently ignored, which
    is the failure that would matter: probes measuring last week's data
    while reporting today's date.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(
            f"{path} not found. Download it with `python cli.py fetch-data` -- "
            "data/ is gitignored, so a fresh clone has none of it."
        )
    stat = source.stat()
    cache = source.with_suffix(f".{int(stat.st_mtime)}.{stat.st_size}.parquet")

    if use_cache and cache.exists():
        return pd.read_parquet(cache)

    frame = pd.read_csv(source, parse_dates=["timestamp"]).set_index("timestamp")
    if use_cache:
        try:
            for stale in source.parent.glob(f"{source.stem}.*.parquet"):
                stale.unlink()
            frame.to_parquet(cache)
        except (OSError, ImportError):
            # A cache that cannot be written is not an error: the frame
            # is already in hand, and refusing to continue over a disk
            # or pyarrow problem would be worse than being slow.
            pass
    return frame


def load_config(path: str = PROBE_CONFIG) -> BacktestConfig:
    return BacktestConfig.from_yaml(path)


def daily_closes(frame: pd.DataFrame) -> pd.Series:
    """One close per calendar day present in the data.

    Written once because five probes derive regime signals from it, and
    a signal computed on a different resampling is a different signal.
    """
    return frame["close"].resample("D").last().dropna()


def cache_paths(path: str = TQQQ) -> list[str]:
    """Existing cache files for `path`. Exposed so a caller can report or
    clear them without reaching into this module's naming scheme."""
    source = Path(path)
    return [str(p) for p in sorted(source.parent.glob(f"{source.stem}.*.parquet"))]


__all__ = [
    "PROBE_CONFIG",
    "SQQQ",
    "TQQQ",
    "VIXY",
    "Escalating",
    "cache_paths",
    "daily_closes",
    "escalation",
    "load_bars",
    "load_config",
]
