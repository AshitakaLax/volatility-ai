"""Cross-asset and macro features, aligned to a minute-bar index.

--------------------------------------------------------------------
TWO RULES, AND EVERYTHING HERE FOLLOWS FROM THEM

1. CAUSAL TRANSFORMS. A z-score computed with pandas' default
   .std() over a whole column uses the whole column -- including the
   future. Every rolling statistic here is computed with a trailing
   window and then shifted, so the value attached to day D is built
   only from days < D. This is the single easiest way to manufacture a
   beautiful backtest, and it is silent when you get it wrong.

2. AS-OF JOIN, NEVER AN INTERPOLATION. A daily series joined onto
   minute bars must step, holding the last PUBLISHED value until the
   next one prints. Interpolating between two daily closes slides part
   of tomorrow's value into today, which is look-ahead wearing the
   costume of smoothing. ExternalIndexSeries.vectorized does the step
   join and returns NaN before a series' first print; that NaN is kept
   rather than filled, so a model can tell "no data yet" from "zero".

The publication lag is already baked into the timestamps by
src/ml/sources.py. This module must not undo it, which is why nothing
here shifts a timestamp forward.

--------------------------------------------------------------------
WHY RATIOS AND TERM STRUCTURE, NOT JUST LEVELS

The funds this is pointed at -- RSP, COWZ, SPYD -- are defensive tilts,
and the objective is risk reduction rather than maximum return. A raw
level ("VIX is 14") barely constrains anything. What carries regime
information is RELATIVE:

    VIX9D / VIX      -- near-term stress against the 30-day benchmark
    VIX / VIX3M      -- contango vs backwardation, the classic
                        risk-on/risk-off switch
    XLU / XLK        -- defensive over cyclical: money leaving risk
    HYG / IEF        -- credit appetite against duration
    RSP / SPY        -- equal weight over cap weight, i.e. breadth

Those ratios are the reason the offsetting legs (XLK, SPY, QQQ) were
collected at all. They are denominators, not trade candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.external_index_series import ExternalIndexSeries
from src.ml.sources import default_directory

# Trading days. 21 ~ a month, 63 ~ a quarter, 252 ~ a year.
_MONTH, _QUARTER, _YEAR = 21, 63, 252


@dataclass(frozen=True)
class ExternalFeature:
    """One derived column, and the file(s) it is derived from."""

    name: str
    numerator: str
    transform: str
    denominator: str | None = None
    category: str = "macro"

    @property
    def files(self) -> tuple[str, ...]:
        return (self.numerator,) if self.denominator is None else (self.numerator, self.denominator)


def _causal_zscore(series: pd.Series, window: int) -> pd.Series:
    """Standardised against its own TRAILING window only.

    .shift(1) after the rolling statistic is the part that matters: a
    rolling window in pandas includes the current observation, so
    without the shift the value at D is standardised using D itself.
    """
    mean = series.rolling(window, min_periods=window // 4).mean().shift(1)
    deviation = series.rolling(window, min_periods=window // 4).std().shift(1)
    # A dead series (a peg, a constant) has zero deviation; the z-score
    # is 0.0 there rather than an infinity that would poison a model.
    return ((series - mean) / deviation.replace(0.0, np.nan)).fillna(0.0)


def _causal_percentile(series: pd.Series, window: int) -> pd.Series:
    """Where the current value sits in its own trailing distribution.

    Robust where a z-score is not: credit spreads and VIX are strongly
    right-skewed, and a 6-sigma print in 2020 says less than "higher
    than any day in the last year" does.
    """
    return series.rolling(window, min_periods=window // 4).rank(pct=True).fillna(0.5)


def _apply(series: pd.Series, transform: str) -> pd.Series:
    if transform == "level":
        return series
    if transform == "log":
        # Prices and balance-sheet aggregates span orders of magnitude.
        return np.log(series.where(series > 0))
    if transform.startswith("change_"):
        return series.diff(int(transform.split("_")[1]))
    if transform.startswith("return_"):
        return series.pct_change(int(transform.split("_")[1]), fill_method=None)
    if transform.startswith("zscore_"):
        return _causal_zscore(series, int(transform.split("_")[1]))
    if transform.startswith("percentile_"):
        return _causal_percentile(series, int(transform.split("_")[1]))
    if transform.startswith("realized_vol_"):
        window = int(transform.split("_")[-1])
        returns = np.log(series).diff()
        return returns.rolling(window, min_periods=window // 2).std() * np.sqrt(252)
    raise ValueError(f"unknown transform {transform!r}")


def catalogue() -> list[ExternalFeature]:
    """Every derived feature. Deliberately over-broad; prune by measurement."""
    features: list[ExternalFeature] = []

    def add(name, numerator, transform, denominator=None, category="macro"):
        features.append(ExternalFeature(name, numerator, transform, denominator, category))

    # -- Volatility term structure. The most direct read on whether the
    #    market is pricing near-term stress above or below its baseline.
    add("vix_level", "cboe_VIX.csv", "level", category="vol")
    add("vix_pctile_1y", "cboe_VIX.csv", "percentile_252", category="vol")
    add("vix_change_5d", "cboe_VIX.csv", "change_5", category="vol")
    add("vix_term_9d_30d", "cboe_VIX9D.csv", "level", "cboe_VIX.csv", "vol")
    add("vix_term_30d_3m", "cboe_VIX.csv", "level", "cboe_VIX3M.csv", "vol")
    add("vix_term_3m_6m", "cboe_VIX3M.csv", "level", "cboe_VIX6M.csv", "vol")
    add("vvix_over_vix", "cboe_VVIX.csv", "level", "cboe_VIX.csv", "vol")
    add("skew_level", "cboe_SKEW.csv", "level", category="vol")
    add("skew_pctile_1y", "cboe_SKEW.csv", "percentile_252", category="vol")
    add("vxn_over_vix", "cboe_VXN.csv", "level", "cboe_VIX.csv", "vol")
    add("rvx_over_vix", "cboe_RVX.csv", "level", "cboe_VIX.csv", "vol")
    add("ovx_level", "cboe_OVX.csv", "level", category="vol")
    add("gvz_level", "cboe_GVZ.csv", "level", category="vol")

    # -- Credit. Spreads widen before equity vol reacts more often than
    #    the reverse, which is exactly the lead a risk-reduction
    #    objective wants.
    # Moody's first: these reach 1986, where the ICE BofA series below
    # are capped by FRED at a rolling three years and so cover barely
    # a quarter of a 2016-2026 training window.
    add("baa_spread", "fred_BAA10Y.csv", "level", category="credit")
    add("baa_spread_pctile_1y", "fred_BAA10Y.csv", "percentile_252", category="credit")
    add("baa_spread_change_21d", "fred_BAA10Y.csv", "change_21", category="credit")
    add("aaa_spread", "fred_AAA10Y.csv", "level", category="credit")
    add("baa_minus_aaa", "fred_DBAA.csv", "level", "fred_DAAA.csv", "credit")
    add("curve_10y_ff", "fred_T10YFF.csv", "level", category="curve")
    add("hy_oas", "fred_BAMLH0A0HYM2.csv", "level", category="credit")
    add("hy_oas_pctile_1y", "fred_BAMLH0A0HYM2.csv", "percentile_252", category="credit")
    add("hy_oas_change_21d", "fred_BAMLH0A0HYM2.csv", "change_21", category="credit")
    add("ig_oas", "fred_BAMLC0A0CM.csv", "level", category="credit")
    add("ccc_oas", "fred_BAMLH0A3HYC.csv", "level", category="credit")
    add("ccc_over_hy", "fred_BAMLH0A3HYC.csv", "level", "fred_BAMLH0A0HYM2.csv", "credit")
    add("em_oas", "fred_BAMLEMCBPIOAS.csv", "level", category="credit")

    # -- Rates and curve
    add("dgs10", "fred_DGS10.csv", "level", category="rates")
    add("dgs2", "fred_DGS2.csv", "level", category="rates")
    add("dgs3mo", "fred_DGS3MO.csv", "level", category="rates")
    add("curve_10y2y", "fred_T10Y2Y.csv", "level", category="curve")
    add("curve_10y3m", "fred_T10Y3M.csv", "level", category="curve")
    add("dgs10_change_21d", "fred_DGS10.csv", "change_21", category="rates")
    add("dgs10_zscore_1y", "fred_DGS10.csv", "zscore_252", category="rates")
    add("breakeven_10y", "fred_T10YIE.csv", "level", category="inflation")
    add("breakeven_5y", "fred_T5YIE.csv", "level", category="inflation")
    add("real_yield_10y", "fred_DGS10.csv", "level", "fred_T10YIE.csv", "rates")

    # -- Financial conditions and stress
    add("nfci", "fred_NFCI.csv", "level", category="stress")
    add("anfci", "fred_ANFCI.csv", "level", category="stress")
    add("stlfsi", "fred_STLFSI4.csv", "level", category="stress")

    # -- Risk appetite as ratios of things that actually trade.
    add("defensive_xlu_xlk", "yahoo_XLU.csv", "level", "yahoo_XLK.csv", "rotation")
    add("defensive_xlp_xly", "yahoo_XLP.csv", "level", "yahoo_XLY.csv", "rotation")
    add("defensive_xlv_xlk", "yahoo_XLV.csv", "level", "yahoo_XLK.csv", "rotation")
    add("breadth_rsp_spy", "yahoo_RSP.csv", "level", "yahoo_SPY.csv", "rotation")
    add("credit_hyg_ief", "yahoo_HYG.csv", "level", "yahoo_IEF.csv", "rotation")
    add("duration_tlt_shy", "yahoo_TLT.csv", "level", "yahoo_SHY.csv", "rotation")
    add("gold_over_spy", "yahoo_GLD.csv", "level", "yahoo_SPY.csv", "rotation")
    add("smallcap_iwm_spy", "yahoo_IWM.csv", "level", "yahoo_SPY.csv", "rotation")
    add("intl_efa_spy", "yahoo_EFA.csv", "level", "yahoo_SPY.csv", "rotation")
    add("em_eem_spy", "yahoo_EEM.csv", "level", "yahoo_SPY.csv", "rotation")

    # -- Factor tilts: what these three funds ARE, measured against the
    #    cap-weighted market they are a tilt away from.
    add("value_vlue_spy", "yahoo_VLUE.csv", "level", "yahoo_SPY.csv", "factor")
    add("momentum_mtum_spy", "yahoo_MTUM.csv", "level", "yahoo_SPY.csv", "factor")
    add("quality_qual_spy", "yahoo_QUAL.csv", "level", "yahoo_SPY.csv", "factor")
    add("minvol_usmv_spy", "yahoo_USMV.csv", "level", "yahoo_SPY.csv", "factor")
    add("highdiv_vym_spy", "yahoo_VYM.csv", "level", "yahoo_SPY.csv", "factor")

    # -- Realized volatility of the broad market at three horizons, so a
    #    model can see whether vol is rising or falling rather than only
    #    where it stands.
    add("spy_rvol_21d", "yahoo_SPY.csv", "realized_vol_21", category="vol")
    add("spy_rvol_63d", "yahoo_SPY.csv", "realized_vol_63", category="vol")
    add("spy_return_21d", "yahoo_SPY.csv", "return_21", category="trend")
    add("spy_return_63d", "yahoo_SPY.csv", "return_63", category="trend")
    add("spy_return_252d", "yahoo_SPY.csv", "return_252", category="trend")

    # -- Dollar, commodities, liquidity
    add("dollar_broad", "fred_DTWEXBGS.csv", "level", category="fx")
    add("dollar_change_21d", "fred_DTWEXBGS.csv", "change_21", category="fx")
    add("wti", "fred_DCOILWTICO.csv", "level", category="commodity")
    add("wti_return_21d", "fred_DCOILWTICO.csv", "return_21", category="commodity")
    add("fed_assets_log", "fred_WALCL.csv", "log", category="liquidity")
    add("reverse_repo", "fred_RRPONTSYD.csv", "level", category="liquidity")

    # -- Slow macro. Heavily lagged by construction, so these describe
    #    the backdrop rather than the day.
    add("unemployment", "fred_UNRATE.csv", "level", category="labour")
    add("claims", "fred_ICSA.csv", "level", category="labour")
    add("claims_change_21d", "fred_ICSA.csv", "change_21", category="labour")
    add("sahm", "fred_SAHMREALTIME.csv", "level", category="labour")
    add("cpi_yoy", "fred_CPIAUCSL.csv", "return_12", category="macro")
    add("indpro_yoy", "fred_INDPRO.csv", "return_12", category="macro")
    add("sentiment", "fred_UMCSENT.csv", "level", category="macro")
    add("recession_flag", "fred_USREC.csv", "level", category="macro")

    return features


def _load(path: Path) -> pd.Series:
    """A daily series indexed by its publication timestamp."""
    frame = pd.read_csv(path, parse_dates=["timestamp"])
    series = frame.set_index("timestamp")["close"]
    # Same-stamp duplicates would make the join order-dependent.
    return series[~series.index.duplicated(keep="last")].sort_index()


def transformed_sources(
    features: list[ExternalFeature],
    *,
    directory: Path | None = None,
) -> dict[str, ExternalIndexSeries]:
    """Every feature's fully-transformed series, wrapped for as-of lookup.

    This is the ONE place the ratio-then-transform pipeline is written.
    build() below calls it and then does a bulk .vectorized(bar_index)
    over the result; src/ml/live_features.py calls it and does
    per-timestamp .scalar() lookups instead, from a SizingStrategy that
    sees one bar at a time and has no bar_index to vectorize against.
    Both get IDENTICAL numbers for identical inputs because both run
    the SAME code up to this point -- which is the only way "the live
    strategy computes what the offline dataset computed" is actually
    true rather than merely intended.

    Missing source files are SKIPPED rather than raising, same as
    build() -- a feature catalogue wider than any one machine's data
    directory is the whole point of src/ml/sources.py's registry.
    """
    directory = directory or default_directory()
    cache: dict[str, pd.Series] = {}
    result: dict[str, ExternalIndexSeries] = {}

    for feature in features:
        paths = [directory / name for name in feature.files]
        if not all(path.exists() for path in paths):
            continue

        for name, path in zip(feature.files, paths, strict=True):
            if name not in cache:
                cache[name] = _load(path)

        numerator = cache[feature.numerator]
        if feature.denominator is not None:
            denominator = cache[feature.denominator]
            # Combined on the union of publication stamps and forward
            # filled, so a ratio updates whenever EITHER leg prints --
            # then the transform runs on the ratio itself.
            joined = (
                pd.concat({"n": numerator, "d": denominator}, axis=1, sort=False)
                .sort_index()
                .ffill()
                .dropna()
            )
            if joined.empty:
                continue
            series = joined["n"] / joined["d"].replace(0.0, np.nan)
        else:
            series = numerator

        transformed = _apply(series.astype(float), feature.transform).replace(
            [np.inf, -np.inf], np.nan
        )
        transformed = transformed.dropna()
        if transformed.empty:
            continue

        result[feature.name] = ExternalIndexSeries(transformed.rename("close").to_frame())

    return result


def build(
    bar_index: pd.DatetimeIndex,
    *,
    directory: Path | None = None,
    features: list[ExternalFeature] | None = None,
) -> pd.DataFrame:
    """As-of join every available feature onto a bar index.

    Missing source files are SKIPPED rather than raising: the registry
    is intentionally broader than any one machine's data directory, and
    a partial feature matrix is more useful than an exception. What was
    skipped is reported by `coverage()`.
    """
    features = features if features is not None else catalogue()

    if bar_index.tz is None:
        raise ValueError("build() needs a tz-aware bar index; publication lag is in UTC.")
    bar_index = bar_index.sort_values()

    sources = transformed_sources(features, directory=directory)
    columns = {name: series.vectorized(bar_index) for name, series in sources.items()}
    return pd.DataFrame(columns, index=bar_index)


def coverage(matrix: pd.DataFrame) -> pd.DataFrame:
    """How much of each column is actually present, worst first.

    A column that is 90% NaN over the training window is not a feature,
    it is a source that starts too late -- and the point of building
    wide first is to find that out by measurement.
    """
    present = matrix.notna().mean().sort_values()
    return pd.DataFrame(
        {
            "present_fraction": present,
            "first_valid": [matrix[c].first_valid_index() for c in present.index],
        }
    )


# ------------------------------------------------------------------
# Bar-local features.
#
# The macro block above updates once a day at best. These come from the
# minute bars themselves and are what actually moves between one entry
# and the next. Every window is trailing and every statistic is shifted
# so that bar i is described only by bars < i -- the same rule as the
# macro transforms, and the same failure mode if it is broken.

_BAR_WINDOWS = (5, 15, 60, 390)  # 5m, 15m, 1h, one RTH session


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI.

    Deliberately recomputed here rather than imported from
    src/sizing_indicators.py: that module's _rsi is private, scalar and
    stateful for the live loop, and reaching into it would couple the
    offline dataset to the live sizing path. The definition is fixed
    enough that two implementations are cheaper than that coupling --
    and tests/unit/test_ml_features.py pins them against each other.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    average_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    average_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    strength = average_gain / average_loss.replace(0.0, np.nan)
    return (100 - 100 / (1 + strength)).fillna(50.0)


def bar_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Trend, volatility, position and session features from the bars."""
    for column in ("open", "high", "low", "close", "volume"):
        if column not in bars.columns:
            raise ValueError(f"bars is missing {column!r}; have {list(bars.columns)}")

    close = bars["close"].astype(float)
    log_return = np.log(close).diff()
    out: dict[str, pd.Series] = {}

    for window in _BAR_WINDOWS:
        out[f"return_{window}b"] = close.pct_change(window, fill_method=None)
        # Annualised on a 390-minute session, 252 sessions.
        out[f"rvol_{window}b"] = log_return.rolling(
            window, min_periods=window // 2
        ).std() * np.sqrt(390 * 252)

    # Volatility of volatility, and whether vol is rising or falling --
    # the grid's edge comes from oscillation, so the SHAPE of the
    # volatility path matters more than its level.
    fast, slow = out["rvol_15b"], out["rvol_390b"]
    out["rvol_ratio_15_390"] = fast / slow.replace(0.0, np.nan)
    out["rvol_of_rvol"] = fast.rolling(390, min_periods=100).std()

    # Where price sits inside its own recent range. This is the closest
    # bar-local analogue of the strategy's own local reference, and the
    # stranding failure this project has already measured is exactly a
    # loss of that reference.
    for window in (60, 390, 1950):
        high = bars["high"].rolling(window, min_periods=window // 4).max()
        low = bars["low"].rolling(window, min_periods=window // 4).min()
        out[f"position_in_range_{window}b"] = (
            (close - low) / (high - low).replace(0.0, np.nan)
        ).clip(0.0, 1.0)
        out[f"drawdown_from_high_{window}b"] = close / high.replace(0.0, np.nan) - 1.0

    out["rsi_14"] = _rsi(close, 14)
    out["rsi_60"] = _rsi(close, 60)

    # True range, normalised, which is what the grid step is denominated
    # against: a 0.5% step means something different at 8% NATR than at 1%.
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            bars["high"] - bars["low"],
            (bars["high"] - previous_close).abs(),
            (bars["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["natr_390b"] = (true_range.rolling(390, min_periods=100).mean() / close) * 100

    volume = bars["volume"].astype(float)
    out["volume_ratio_390b"] = volume / volume.rolling(390, min_periods=100).median().replace(
        0.0, np.nan
    )

    # Session position. Open and close are structurally the most
    # volatile parts of the day, and a grid fills differently in each.
    index = pd.DatetimeIndex(bars.index)
    minutes = index.tz_convert("America/New_York")
    out["minute_of_session"] = pd.Series(
        (minutes.hour * 60 + minutes.minute) - (9 * 60 + 30), index=bars.index, dtype=float
    )
    out["day_of_week"] = pd.Series(minutes.dayofweek, index=bars.index, dtype=float)

    frame = pd.DataFrame(out, index=bars.index)
    # SHIFTED BY ONE BAR, and this is the load-bearing line. Every
    # statistic above includes bar i's own close; a model choosing
    # whether to buy AT bar i cannot have seen it. Without this shift
    # the dataset leaks the present into its own inputs.
    return frame.shift(1).replace([np.inf, -np.inf], np.nan)
