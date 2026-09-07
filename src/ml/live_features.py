"""One feature vector per bar, for a SizingStrategy -- bar-local plus vol.

Combines src/ml/rolling.py's IncrementalBarFeatures (21 columns, built
bar-by-bar from OHLC alone) with the volatility-block external series
(15 columns: VIX term structure, VVIX, SKEW, VXN, RVX, OVX, GVZ, and
SPY's own realized vol) via features.transformed_sources() -- the same
function tools/build_ml_dataset.py uses, so the two agree by
construction rather than by two implementations staying in sync by
hand.

--------------------------------------------------------------------
WHY THE VOL BLOCK, AND NOT THE OTHER 58 MACRO FEATURES

tools/ablate_ml_features.py measured this: on COWZ -- the one fund
where the combined "macro" signal survived a paired, purged
walk-forward check at all -- the volatility block alone accounts for
+0.039 of the +0.046 total AUC lift, and it is the only block
consistent across all 5 folds on that fund. Rates, labour, fx and
curve were inconsistent-to-negative. Carrying 58 more columns of
per-bar as-of lookups into a hot path for features the data does not
support would be cost without benefit; see ml_plan.md, "Ablation by
block" for the full table.

--------------------------------------------------------------------
WHY THIS CAN LOAD FILES AT CONSTRUCTION TIME WHEN IncrementalBarFeatures CANNOT PRECOMPUTE

The vol-block CSVs (data/external/cboe_*.csv, fred_VIXCLS.csv,
yahoo_SPY.csv) are small, DAILY, and update independently of whatever
minute-bar file a backtest happens to be replaying -- there is no
"whole history of this run" to avoid depending on, only a handful of
small files this class reads once, in full, up front. That is a
categorically different thing from needing the run's own OHLC series,
which record_tick genuinely cannot see beyond one bar at a time
without changing what MarketContext carries.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.exceptions import ConfigurationError
from src.ml.features import catalogue, default_directory, transformed_sources
from src.ml.rolling import IncrementalBarFeatures

VOL_BLOCK = tuple(feature.name for feature in catalogue() if feature.category == "vol")


class LiveFeatureSource:
    """Bar-local (21) + volatility-block (15) = 36 features, per bar."""

    def __init__(self, *, external_directory: Path | str | None = None) -> None:
        directory = Path(external_directory) if external_directory else default_directory()
        wanted = {feature.name: feature for feature in catalogue() if feature.category == "vol"}
        self._external = transformed_sources(list(wanted.values()), directory=directory)

        missing = set(VOL_BLOCK) - set(self._external)
        if missing:
            raise ConfigurationError(
                f"LiveFeatureSource: missing volatility-block source files for "
                f"{sorted(missing)} under {directory}. Run: "
                "python tools/fetch_market_inputs.py --category vol"
            )

        self._bars = IncrementalBarFeatures()

    def record(
        self, timestamp: datetime, high: float, low: float, close: float
    ) -> dict[str, float]:
        """The full 36-feature vector describing bars strictly before
        `timestamp`, in the SAME column order every time -- callers that
        hand this straight to a model (see reachability_sizing.py) need
        that order fixed, not merely present."""
        features = self._bars.record(timestamp, high, low, close)
        for name in VOL_BLOCK:
            value = self._external[name].scalar(timestamp)
            # None (no print yet at this timestamp) becomes NaN, matching
            # how every other missing value in this feature vector is
            # represented -- a caller does not need a second convention.
            features[name] = float("nan") if value is None else value
        return features


__all__ = ["VOL_BLOCK", "LiveFeatureSource"]
