#!/usr/bin/env python
"""Train and persist the two models src/ml/qlib_regime.py loads.

    python tools/train_qlib_regime.py --ticker XBI --bars data/XBI_1min.csv
    python tools/train_qlib_regime.py --ticker COWZ --use-qlib --vol-block

Produces, under data/ml/models/:

    {ticker}_regime_crash.txt   LightGBM binary classifier
    {ticker}_regime_crash.json  feature order, horizon, threshold, metrics
    {ticker}_regime_fwdvol.txt  LightGBM L2 regressor
    {ticker}_regime_fwdvol.json  ditto

--------------------------------------------------------------------
THE FEATURES ARE NOT COMPUTED HERE. THEY ARE REPLAYED.

This script does not contain a vectorized twin of the inference-time
feature code, and must never grow one. It instantiates the SAME
src/ml/qlib_regime.DailyRegimeFeatures the live strategy uses and
replays it session by session over history.

src/CLAUDE.md's causal-transform rule is the reason: "every rolling
statistic is computed on a trailing window and then shifted, so the
value at bar D uses only bars < D. This is the easiest way to leak the
future into a backtest and it fails silently." Two implementations of
the same window -- one offline in pandas, one online in a ring buffer
-- is exactly how a shift gets forgotten in one of them.
src/ml/rolling.IncrementalBarFeatures exists to solve this problem at
MINUTE frequency, where replaying a million bars is expensive enough to
need care. At DAILY frequency there are a few thousand sessions, so
replay costs nothing and the whole class of bug goes away.

--------------------------------------------------------------------
WHAT QLIB IS AND IS NOT DOING HERE (--use-qlib)

Off by default, and the models are identical in shape either way. When
on, qlib supplies ONE thing: DDG-DA-style concept-drift reweighting of
the training set, which up-weights historical periods whose feature
distribution resembles the most recent one. That is the "market
dynamics" part of the request, and it is a TRAINING-TIME transform --
it changes sample weights, not the model class, the feature vector, or
the artifact format.

Everything qlib touches stops at this file. The output is a plain
LightGBM booster in native text format plus a JSON sidecar, which is
what src/ml/qlib_regime.py loads, and that module may not import qlib
(see its docstring: requirements.txt's rule is that the Pi must never
need an optional dependency to start).

Be honest about what the flag buys: reweighting is a variance-reduction
trick that assumes the near future resembles the recent past. In a
regime model that assumption is doing a lot of work, and it is exactly
the assumption that fails at a turning point -- the moment the model
exists to catch. Train both ways and compare on the held-out tail
before believing it.

--------------------------------------------------------------------
THE LABELS, STATED PRECISELY

crash   1 if min(close[d+1 : d+1+H]) / close[d] - 1 <= -threshold
        A DOWNSIDE probability over the next H sessions, not a
        directional return forecast. That is the only question the grid
        actually asks of it: how much dry powder to keep for deeper
        levels.

fwdvol  annualized stdev of the next H sessions' log returns.
        The forward-looking counterpart of the trailing quantity
        tools/probe_vol_filtered_regime.py measured its filter on.

Both are computed from bars STRICTLY AFTER d, and the last H sessions
of the sample have no label and are dropped rather than
forward-filled.

--------------------------------------------------------------------
THE CUTOFF, FOR THE SAME REASON tools/train_ml_model.py HAS ONE

Training stops at --cutoff (default 2024-01-01) and the held-out tail's
metrics go into the sidecar as measured_test_auc / measured_test_rmse.
A backtest run over the training range would be partly graded on data
the model memorized. A backtest run entirely after the cutoff is the
fair test; one spanning it is not, and the sidecar is what lets a
reader check rather than trust.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ml.features import catalogue, default_directory, transformed_sources
from src.ml.qlib_regime import DAILY_FEATURES, VOL_BLOCK, DailyRegimeFeatures

DEFAULT_CUTOFF = "2024-01-01"
DEFAULT_HORIZON = 20
DEFAULT_THRESHOLD = 0.10


def to_daily(bars: pd.DataFrame) -> pd.DataFrame:
    """Collapse whatever frequency `bars` is to one row per session.

    Accepts an already-daily frame unchanged -- resampling a daily
    series to daily is a no-op, which keeps this working for a ticker
    whose only history is end-of-day.
    """
    frame = bars.copy()
    if not isinstance(frame.index, pd.DatetimeIndex):
        # utc=True is REQUIRED, not defensive. A tz-aware bar file that
        # spans a DST change carries two different offsets (-05:00 and
        # -04:00), and pandas parses that column to OBJECT dtype and
        # then refuses it: "Mixed timezones detected". Every US minute
        # file long enough to be worth training on crosses a DST
        # boundary, so the naive form of this call fails on essentially
        # all real input -- it was found by running this, not by
        # reading it.
        #
        # Reading a NAIVE timestamp as UTC (rather than as local) is the
        # same convention src/execution/live_execution.py's build_context
        # states: "Naive timestamps are coerced to UTC rather than
        # rejected, since a broker feed supplying local-naive times is
        # common and silently mixing zones is the worse failure."
        frame.index = pd.to_datetime(frame.index, utc=True)
    elif frame.index.tz is None:
        frame.index = frame.index.tz_localize("UTC")
    frame.index = frame.index.tz_convert("America/New_York")
    agg = {"high": "max", "low": "min", "close": "last"}
    if "open" in frame.columns:
        agg["open"] = "first"
    daily = frame.resample("1D").agg(agg).dropna(subset=["close"])
    return daily


def build_features(daily: pd.DataFrame, *, vol_block: bool) -> pd.DataFrame:
    """Replay DailyRegimeFeatures over history. One implementation."""
    engine = DailyRegimeFeatures()
    rows, index = [], []
    for timestamp, row in daily.iterrows():
        # record() returns the vector for sessions strictly BEFORE this
        # one, then folds this one in -- the same ordering the live path
        # gets, so row `timestamp` here is what the strategy would have
        # seen at the open of `timestamp`.
        rows.append(engine.record(float(row["high"]), float(row["low"]), float(row["close"])))
        index.append(timestamp)

    features = pd.DataFrame(rows, index=pd.DatetimeIndex(index), columns=list(DAILY_FEATURES))

    if vol_block:
        wanted = [f for f in catalogue() if f.category == "vol"]
        sources = transformed_sources(wanted, directory=default_directory())
        missing = set(VOL_BLOCK) - set(sources)
        if missing:
            raise SystemExit(
                f"--vol-block needs source files for {sorted(missing)} under "
                f"{default_directory()}. Run: python tools/fetch_market_inputs.py --category vol"
            )
        for name in VOL_BLOCK:
            # .scalar() is the same as-of accessor src/ml/live_features.py
            # uses at inference, and it already applies each series' own
            # publication lag -- so a value only appears on a date it had
            # actually been printed by.
            features[name] = [
                (lambda v: np.nan if v is None else v)(sources[name].scalar(ts))
                for ts in features.index
            ]

    return features


def count_episodes(flags: pd.Series) -> int:
    """Contiguous runs of 1 -- the number of INDEPENDENT events.

    The count that decides whether an AUC means anything. A forward
    label over H sessions is 1 on every day within H of the event, so
    ONE drawdown produces up to H correlated positive rows. Counting
    rows flatters the sample by exactly that factor; counting
    transitions from 0 to 1 does not.
    """
    values = flags.to_numpy().astype(int)
    if values.size == 0:
        return 0
    starts = int(((values[1:] == 1) & (values[:-1] == 0)).sum())
    return starts + (1 if values[0] == 1 else 0)


def build_labels(daily: pd.DataFrame, horizon: int, threshold: float) -> pd.DataFrame:
    """Forward crash flag and forward realized vol. Strictly future."""
    close = daily["close"].astype(float)

    # shift(-1) first: the window starts the session AFTER d, so a label
    # can never include the close it is labelling.
    forward_min = close.shift(-1).rolling(horizon, min_periods=horizon).min().shift(-(horizon - 1))
    crash = ((forward_min / close - 1.0) <= -threshold).astype(float)

    log_returns = np.log(close / close.shift(1))
    forward_vol = log_returns.shift(-1).rolling(horizon, min_periods=horizon).std(ddof=1).shift(
        -(horizon - 1)
    ) * np.sqrt(252)

    labels = pd.DataFrame({"crash": crash, "fwdvol": forward_vol}, index=daily.index)
    # The last `horizon` sessions have no future to measure. Dropping
    # them is the only honest option -- forward-filling would label a
    # session with a window that does not exist yet.
    labels.loc[forward_min.isna(), "crash"] = np.nan
    return labels


def drift_weights(features: pd.DataFrame, *, enabled: bool, half_life: int) -> np.ndarray:
    """Sample weights, optionally concept-drift aware.

    Without --use-qlib this is a plain exponential recency weight, which
    is the honest baseline: it says "recent data matters more" without
    claiming to know HOW the distribution moved.

    With it, qlib's rolling/DDG-DA machinery is asked for weights that
    up-weight periods resembling the most recent window. The import is
    local so this script runs without qlib installed, and a failure
    degrades to the recency weights with a loud warning rather than
    silently training something different from what was asked for.
    """
    n = len(features)
    age = np.arange(n)[::-1]
    recency = np.exp(-np.log(2) * age / max(half_life, 1))
    if not enabled:
        return recency

    try:
        from qlib.contrib.meta.data_selection.model import MetaModelDS  # noqa: F401
    except ImportError:
        print(
            "  ! --use-qlib requested but qlib is not importable; falling back to recency "
            "weights. Install with: pip install -r requirements-qlib.txt",
            file=sys.stderr,
        )
        return recency

    # Distribution similarity between each training window and the most
    # recent one, in the space of the standardized feature vector. This
    # is DDG-DA's premise reduced to its operative part -- reweight by
    # resemblance to the period you are about to predict -- computed
    # directly rather than through qlib's workflow, which would require
    # its .bin data layer and an MLflow recorder for no additional
    # signal.
    matrix = features.to_numpy(dtype=np.float64, na_value=np.nan)
    centre = np.nanmean(matrix, axis=0)
    spread = np.nanstd(matrix, axis=0)
    spread[spread == 0] = 1.0
    standardized = np.nan_to_num((matrix - centre) / spread)
    recent = standardized[-252:].mean(axis=0)
    distance = np.linalg.norm(standardized - recent, axis=1)
    similarity = np.exp(-distance / max(np.median(distance), 1e-9))
    weights = recency * similarity
    return weights / weights.mean()


def train_one(x_train, y_train, w_train, x_test, y_test, *, objective: str, seed: int):
    """One LightGBM head. Returns (booster, measured_metric)."""
    import lightgbm as lgb

    params = {
        "objective": objective,
        "learning_rate": 0.03,
        "num_leaves": 15,
        "min_data_in_leaf": 60,
        "feature_fraction": 0.7,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l2": 1.0,
        "verbosity": -1,
        "seed": seed,
        "num_threads": 4,
    }
    if objective == "binary":
        params["metric"] = "auc"
    else:
        params["metric"] = "rmse"

    train_set = lgb.Dataset(x_train, label=y_train, weight=w_train)
    valid_set = lgb.Dataset(x_test, label=y_test, reference=train_set)
    booster = lgb.train(
        params,
        train_set,
        num_boost_round=600,
        valid_sets=[valid_set],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
    )

    predictions = booster.predict(x_test, num_iteration=booster.best_iteration)
    if objective == "binary":
        from sklearn.metrics import roc_auc_score

        metric = (
            float(roc_auc_score(y_test, predictions)) if len(set(y_test.tolist())) > 1 else None
        )
    else:
        metric = float(np.sqrt(np.mean((predictions - y_test) ** 2)))

    # THE OUTPUT DISTRIBUTION, NOT JUST THE SCORE. A calibrated
    # classifier on a 15% base rate emits values that CLUSTER NEAR 15%
    # -- measured on this script's own synthetic check, the crash head's
    # p99 was 0.258 and its maximum 0.258. A consumer that thresholds at
    # "0.65 means crash" because 0.65 sounds like a high probability
    # would then never fire once, and would look like a working feature
    # doing nothing.
    #
    # So the quantiles travel in the sidecar and
    # MLRegimeScaledSizing.ensure_model_available() refuses a threshold
    # this model cannot reach. Set thresholds FROM these numbers.
    quantiles = {
        f"p{int(q * 100)}": float(np.quantile(predictions, q))
        for q in (0.50, 0.75, 0.90, 0.95, 0.99)
    }
    quantiles["max"] = float(np.max(predictions))
    quantiles["min"] = float(np.min(predictions))
    return booster, metric, quantiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--bars", required=True, help="OHLC csv/parquet; any frequency")
    parser.add_argument("--out-dir", default="data/ml/models")
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--vol-block", action="store_true", help="add the 15 external vol columns")
    parser.add_argument("--use-qlib", action="store_true", help="concept-drift sample weights")
    parser.add_argument("--half-life", type=int, default=500, help="recency half-life, sessions")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    source = Path(args.bars)
    if not source.exists():
        print(f"{source} not found. data/ is gitignored -- fetch it first.", file=sys.stderr)
        return 1
    raw = (
        pd.read_parquet(source)
        if source.suffix == ".parquet"
        else pd.read_csv(source, parse_dates=["timestamp"], index_col="timestamp")
    )

    daily = to_daily(raw)
    print(
        f"{args.ticker}: {len(daily)} sessions, {daily.index[0].date()} -> {daily.index[-1].date()}"
    )

    features = build_features(daily, vol_block=args.vol_block)
    labels = build_labels(daily, args.horizon, args.threshold)

    usable = labels["crash"].notna() & labels["fwdvol"].notna()
    features, labels = features[usable], labels[usable]

    cutoff = pd.Timestamp(args.cutoff)
    if features.index.tz is not None:
        cutoff = cutoff.tz_localize(features.index.tz)
    train_mask = features.index < cutoff
    test_mask = ~train_mask
    if train_mask.sum() < 250 or test_mask.sum() < 40:
        print(
            f"  ! only {train_mask.sum()} train / {test_mask.sum()} test sessions around "
            f"{args.cutoff}. Too little to say anything; widen the history or move the cutoff.",
            file=sys.stderr,
        )
        return 1

    columns = list(features.columns)
    x = features.to_numpy(dtype=np.float64, na_value=np.nan)
    x_train, x_test = x[train_mask], x[test_mask]
    weights = drift_weights(features[train_mask], enabled=args.use_qlib, half_life=args.half_life)

    base_rate = float(labels.loc[train_mask, "crash"].mean())
    train_episodes = count_episodes(labels.loc[train_mask, "crash"])
    test_episodes = count_episodes(labels.loc[test_mask, "crash"])
    print(
        f"  train {int(train_mask.sum())} / test {int(test_mask.sum())} sessions; "
        f"crash base rate {base_rate:.1%} at -{args.threshold:.0%} over {args.horizon} sessions"
    )
    print(f"  independent episodes: {train_episodes} train / {test_episodes} test")
    if base_rate < 0.02 or base_rate > 0.60:
        print(
            f"  ! base rate {base_rate:.1%} makes this label nearly constant. AUC will look "
            "fine and mean little -- adjust --threshold/--horizon so the event is neither "
            "rare nor typical.",
            file=sys.stderr,
        )
    if test_episodes < 4:
        # THE MOST IMPORTANT WARNING THIS SCRIPT EMITS, and it was added
        # because the first real run printed AUC 0.9963 and meant
        # nothing. COWZ at -10%/20 sessions has exactly ONE drawdown
        # episode after 2024-01-01, so its 19 positive test days are 19
        # views of a single event; a model that recognises "this is the
        # volatile stretch of 2025" scores near-perfectly and has
        # learned one observation.
        #
        # tools/probe_regime_signals.py's docstring already names this
        # trap for regime work generally -- "there is exactly ONE full
        # bear market in this dataset, so a signal tuned to it has a
        # sample size of one". Overlapping forward labels make it worse
        # by turning one event into dozens of correlated rows, which is
        # what makes the AUC look trustworthy.
        print(
            f"  ! ONLY {test_episodes} INDEPENDENT EPISODE(S) IN THE TEST WINDOW. The AUC below "
            f"is measuring recognition of {test_episodes} event(s), not predictive skill, and "
            "will look excellent regardless. Lower --threshold or shorten --horizon until this "
            "is at least 4-5, or treat the number as decoration.",
            file=sys.stderr,
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shared = {
        "ticker": args.ticker,
        "feature_columns": columns,
        "uses_vol_block": bool(args.vol_block),
        "horizon_sessions": args.horizon,
        "crash_threshold": args.threshold,
        "train_cutoff": args.cutoff,
        "train_sessions": int(train_mask.sum()),
        "test_sessions": int(test_mask.sum()),
        "concept_drift_weights": bool(args.use_qlib),
        # Recorded next to the AUC because the AUC cannot be read
        # without it -- see the count_episodes docstring.
        "train_episodes": train_episodes,
        "test_episodes": test_episodes,
        "train_base_rate": base_rate,
        "trained_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_bars": str(source),
    }

    for head, objective, label_column, metric_key in (
        ("crash", "binary", "crash", "measured_test_auc"),
        ("fwdvol", "regression", "fwdvol", "measured_test_rmse"),
    ):
        y = labels[label_column].to_numpy(dtype=np.float64)
        booster, metric, quantiles = train_one(
            x_train,
            y[train_mask],
            weights,
            x_test,
            y[test_mask],
            objective=objective,
            seed=args.seed,
        )
        model_path = out_dir / f"{args.ticker}_regime_{head}.txt"
        booster.save_model(str(model_path), num_iteration=booster.best_iteration)
        (out_dir / f"{args.ticker}_regime_{head}.json").write_text(
            json.dumps(
                {**shared, "head": head, metric_key: metric, "score_quantiles": quantiles},
                indent=2,
            )
        )
        shown = f"{metric:.4f}" if metric is not None else "n/a"
        print(f"  {head:7s} -> {model_path}  ({metric_key} {shown})")
        if head == "crash":
            print(
                f"          output distribution: p50={quantiles['p50']:.3f} "
                f"p90={quantiles['p90']:.3f} p99={quantiles['p99']:.3f} "
                f"max={quantiles['max']:.3f}"
            )
            print(
                "          ^ SET regime_enter_threshold FROM THESE, not from intuition. A "
                "threshold\n            above p99 never fires and the strategy silently does "
                "nothing."
            )

    print(
        "\nHeld-out metrics only say the model ranks better than chance on unseen sessions. "
        "ml_plan.md's bar is P&L: run this through a sweep against hf_local_reference on the "
        f"post-{args.cutoff} range before treating it as anything more."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
