#!/usr/bin/env python
"""Train and persist the model src/ml/reachability_sizing.py loads.

    python tools/train_ml_model.py --tickers RSP COWZ SPYD

Everything before this script (fetch_market_inputs, build_ml_dataset,
evaluate_ml_features, ablate_ml_features) measured whether a signal
exists. Nothing it produced is a deployable artifact -- those tools fit
throwaway LightGBM models per walk-forward fold, purely to score AUC,
and none of them are kept. This is the first script in the project that
saves a model something else actually loads.

--------------------------------------------------------------------
36 FEATURES, NOT THE 95 THE OFFLINE DATASET CARRIES

The persisted model is trained on exactly what
src/ml/live_features.LiveFeatureSource can compute FROM MarketContext
alone at inference time: the 21 bar-local features MarketContext's OHLC
supports (volume_ratio_390b is dropped -- MarketContext carries no
volume, the same gap this project already hit once for RSI-at-entry and
deferred rather than force in) plus the 15-column volatility block,
which tools/ablate_ml_features.py measured as carrying nearly all of
the macro lift that survived a paired walk-forward check at all. See
that module's own docstring for the full reasoning and the ablation
table it is measured against.

Training on the wider 95-column dataset and inferring on 36 would not
error -- LightGBM would happily score whatever columns it is handed --
it would silently mean the deployed model was never actually validated
on the inputs it runs on. Training on the SAME 36 is what makes the
evaluation upstream of this script still describe the thing this script
produces.

--------------------------------------------------------------------
THE TRAIN/TEST CUTOFF, AND WHY IT MATTERS MORE HERE THAN IT DID UPSTREAM

tools/evaluate_ml_features.py never persists a model -- every fold
trains fresh and is thrown away once its AUC is recorded, so there is
no "the deployed model saw its own test set" question to ask. This
script is different: it trains ONE model and hands it to a strategy a
user can then backtest over ANY date range the UI offers, including the
range the model was trained on. A backtest run over that range would
be partly graded on data the model memorized, and would look better
than the walk-forward numbers this project has otherwise insisted on.

So training stops at a fixed cutoff (default 2024-01-01) well short of
each ticker's most recent data, and the held-out tail's AUC is recorded
in the model's own metadata sidecar as measured_test_auc -- so a reader
does not have to trust that the cutoff was honored, they can see what
it bought. A backtest run entirely AFTER the cutoff is the fair test;
one spanning it is partly grading the model on its own training data,
and the UI's Model research tab says so.

--------------------------------------------------------------------
SAVED AS LIGHTGBM'S NATIVE TEXT FORMAT, NOT PICKLED

Booster.save_model()/Booster(model_file=...) round-trips the model as
plain text -- no arbitrary code executes on load, unlike an unpickled
object, and the file is readable enough to diff. The metadata sidecar
(feature order, cutoff, measured AUC) travels next to it as JSON for
the same reason: reachability_sizing.py should not need to trust a
pickle to know what it is loading.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.metrics import roc_auc_score

from src.ml.live_features import VOL_BLOCK
from src.ml.rolling import FEATURE_NAMES as BAR_LOCAL_FEATURES

# Exactly what LiveFeatureSource can supply at inference time -- see
# module docstring. Order matters: it is written into the metadata
# sidecar and used verbatim to build the inference-time row.
FEATURE_COLUMNS: tuple[str, ...] = (*BAR_LOCAL_FEATURES, *VOL_BLOCK)

LABEL = "reached_t0.5_h390"
DEFAULT_CUTOFF = "2024-01-01"

PARAMS = {
    "objective": "binary",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 200,
    "feature_fraction": 0.7,
    "bagging_fraction": 0.7,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "verbose": -1,
    "num_threads": 4,
}
ROUNDS = 300


def train_one(ticker: str, data_dir: Path, cutoff: str) -> dict:
    frame = pd.read_parquet(data_dir / f"{ticker}_ml.parquet")
    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        raise SystemExit(f"{ticker}: dataset is missing columns {missing} -- rebuild it first")

    cutoff_ts = pd.Timestamp(cutoff, tz="UTC")
    train = frame[frame.index < cutoff_ts]
    test = frame[frame.index >= cutoff_ts]

    y_train = train[LABEL].to_numpy()
    y_test = test[LABEL].to_numpy()
    keep_train = ~np.isnan(y_train)
    keep_test = ~np.isnan(y_test)

    if keep_train.sum() < 5000:
        raise SystemExit(
            f"{ticker}: only {keep_train.sum()} labeled training rows before {cutoff} -- "
            "too little history for this cutoff"
        )

    booster = lgb.train(
        PARAMS,
        lgb.Dataset(train[list(FEATURE_COLUMNS)].to_numpy()[keep_train], label=y_train[keep_train]),
        num_boost_round=ROUNDS,
    )

    test_auc = None
    if keep_test.sum() >= 500 and len(np.unique(y_test[keep_test])) > 1:
        prediction = booster.predict(test[list(FEATURE_COLUMNS)].to_numpy()[keep_test])
        test_auc = float(roc_auc_score(y_test[keep_test], prediction))

    return {
        "booster": booster,
        "metadata": {
            "ticker": ticker,
            "label": LABEL,
            "feature_columns": list(FEATURE_COLUMNS),
            "train_cutoff": cutoff,
            "train_rows": int(keep_train.sum()),
            "test_rows": int(keep_test.sum()),
            # None (JSON null), not a number, when there was not enough
            # held-out data to score -- a fabricated 0.5 would read as
            # "measured and found useless" rather than "not measured".
            "measured_test_auc": test_auc,
            "base_rate_train": float(np.nanmean(y_train)),
            "trained_at": pd.Timestamp.now("UTC").isoformat(),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickers", nargs="+", default=["RSP", "COWZ", "SPYD"])
    parser.add_argument("--data", type=Path, default=Path("data/ml"))
    parser.add_argument("--out", type=Path, default=Path("data/ml/models"))
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    print(
        f"{len(FEATURE_COLUMNS)} features ({len(BAR_LOCAL_FEATURES)} bar-local + {len(VOL_BLOCK)} vol)"
    )
    print(f"cutoff: train < {args.cutoff}, test >= {args.cutoff}\n")

    for ticker in args.tickers:
        began = time.time()
        result = train_one(ticker, args.data, args.cutoff)
        meta = result["metadata"]

        model_path = args.out / f"{ticker}_{LABEL}.txt"
        meta_path = args.out / f"{ticker}_{LABEL}.json"
        result["booster"].save_model(str(model_path))
        meta_path.write_text(json.dumps(meta, indent=2))

        auc_text = (
            f"{meta['measured_test_auc']:.4f}" if meta["measured_test_auc"] is not None else "n/a"
        )
        print(
            f"{ticker:<6} {meta['train_rows']:>7,} train rows, {meta['test_rows']:>6,} "
            f"held out  ->  test AUC {auc_text}  ({time.time() - began:.1f}s)"
        )
        print(f"       {model_path}\n       {meta_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
