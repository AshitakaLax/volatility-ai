#!/usr/bin/env python
"""Does any of this carry signal? Walk-forward, purged, against controls.

    python tools/evaluate_ml_features.py --tickers RSP COWZ SPYD
    python tools/evaluate_ml_features.py --tickers SPYD --label reached_t0.5_h1950

The point of collecting 118 public series was to work backwards from a
wide set. This is the backwards step, and it is built to be able to
return "no".

--------------------------------------------------------------------
THREE THINGS THAT MAKE A RESULT MEAN SOMETHING

1. SPLIT BY TIME, EXPANDING. A random split over minute bars is
   meaningless: adjacent rows share nearly all of their trailing
   windows, so a shuffled test set is mostly memorised training data
   wearing a different index.

2. A PURGE GAP, WHICH IS THE PART USUALLY MISSED. A label at bar i
   looks forward `horizon` bars. Train rows within one horizon of the
   split therefore describe price action that happens INSIDE the test
   period. Dropping that band is the difference between measuring
   prediction and measuring overlap.

3. CONTROLS, BECAUSE "BETTER THAN CHANCE" IS NOT THE QUESTION. Three
   feature sets are fitted on identical folds:

       bar      the minute bars alone -- what we already had
       macro    the 118 public series alone
       both     the combination

   The question this project cares about is not whether `both` beats
   0.5. It is whether `both` beats `bar`. If it does not, the macro
   data is decoration and should be said to be, however much work it
   took to collect.

A SHUFFLED-LABEL CONTROL runs alongside, fitting the same model on
permuted training labels. It should score ~0.5; if it scores clearly
ABOVE, the harness leaks and every other number here is void.

  It is averaged over several seeds, because one seed cannot resolve
  it. Measured on RSP: fifty shuffled fits (ten seeds x five folds)
  give 0.5011 +/- 0.0047, i.e. +0.2 SE from chance -- clean. But the
  individual five-fold seed means ranged 0.480 to 0.542, so a single
  seed lands two to three SE from 0.5 routinely and reads as a
  problem when nothing is wrong. A one-seed control is not evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

warnings.filterwarnings("ignore", category=UserWarning)

import lightgbm as lgb
from sklearn.metrics import roc_auc_score

# Small and heavily regularised on purpose. The risk here is not
# underfitting -- with 95 columns and 200k rows a large model will
# happily memorise the folds and report a beautiful in-sample number.
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


def split_columns(schema: dict, ticker: str) -> tuple[list[str], list[str]]:
    """Feature columns, divided into bar-local and macro."""
    feature_columns = schema[ticker]["feature_columns"]
    macro = {
        feature.name for feature in __import__("src.ml.features", fromlist=["features"]).catalogue()
    }
    macro_columns = [c for c in feature_columns if c in macro]
    bar_columns = [c for c in feature_columns if c not in macro]
    return bar_columns, macro_columns


def folds(n: int, count: int, purge: int):
    """Expanding-window splits with a purged band before each test set."""
    edges = np.linspace(n // (count + 1), n, count + 1, dtype=int)
    for i in range(count):
        train_end = edges[i]
        test_start, test_end = edges[i], edges[i + 1]
        if train_end - purge <= 0 or test_end - test_start < 500:
            continue
        yield np.arange(0, train_end - purge), np.arange(test_start, test_end)


def evaluate(frame: pd.DataFrame, columns: list[str], label: str, fold_list, shuffle_seed=None):
    """Per-fold AUCs for one feature set.

    Returned per fold, not averaged, because the feature sets run on
    IDENTICAL folds and the comparison that matters is therefore
    paired. Comparing two means against their independent spreads
    discards that pairing and is far less sensitive: fold-to-fold
    variation here (~0.03) is larger than any lift being looked for,
    so an unpaired read cannot resolve the question being asked.
    """
    scores = []
    rng = np.random.default_rng(shuffle_seed or 0)

    for train_index, test_index in fold_list:
        train, test = frame.iloc[train_index], frame.iloc[test_index]
        y_train = train[label].to_numpy()
        y_test = test[label].to_numpy()

        keep_train = ~np.isnan(y_train)
        keep_test = ~np.isnan(y_test)
        if keep_train.sum() < 1000 or keep_test.sum() < 500:
            continue
        # A fold in which the outcome never varies has no AUC to report.
        if len(np.unique(y_test[keep_test])) < 2 or len(np.unique(y_train[keep_train])) < 2:
            continue

        target = y_train[keep_train]
        if shuffle_seed is not None:
            target = rng.permutation(target)

        model = lgb.train(
            PARAMS,
            lgb.Dataset(train[columns].to_numpy()[keep_train], label=target),
            num_boost_round=ROUNDS,
        )
        prediction = model.predict(test[columns].to_numpy()[keep_test])
        scores.append(roc_auc_score(y_test[keep_test], prediction))

    return scores


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickers", nargs="+", default=["RSP", "COWZ", "SPYD"])
    parser.add_argument("--data", type=Path, default=Path("data/ml"))
    parser.add_argument("--label", default="reached_t0.5_h390")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument(
        "--control-seeds",
        type=int,
        default=3,
        help="Permutation seeds for the shuffled control. One is not enough to resolve it.",
    )
    args = parser.parse_args(argv)

    schema = json.loads((args.data / "schema.json").read_text())
    horizon = int(args.label.split("_h")[-1])
    summary = {}

    for ticker in args.tickers:
        if ticker not in schema:
            print(f"SKIP {ticker}: not in schema")
            continue

        frame = pd.read_parquet(args.data / schema[ticker]["file"])
        stride = schema[ticker]["stride"]
        purge = int(np.ceil(horizon / stride))
        bar_columns, macro_columns = split_columns(schema, ticker)
        fold_list = list(folds(len(frame), args.folds, purge))

        base_rate = float(np.nanmean(frame[args.label].to_numpy()))
        print(
            f"\n{ticker}  {len(frame):,} rows, stride {stride}, purge {purge} rows "
            f"({horizon} bars), {len(fold_list)} folds, base rate {base_rate:.3f}"
        )
        print(f"  {len(bar_columns)} bar features, {len(macro_columns)} macro features")

        per_fold = {}
        for name, columns in (
            ("bar", bar_columns),
            ("macro", macro_columns),
            ("both", bar_columns + macro_columns),
        ):
            scores = evaluate(frame, columns, args.label, fold_list)
            per_fold[name] = scores
            print(
                f"    {name:<8} AUC {np.mean(scores):.4f} +/- {np.std(scores):.4f}  "
                f"[{', '.join(f'{s:.3f}' for s in scores)}]"
            )

        shuffled = []
        for seed in range(args.control_seeds):
            shuffled.extend(
                evaluate(frame, bar_columns + macro_columns, args.label, fold_list, 100 + seed)
            )
        per_fold["shuffled"] = shuffled
        control_se = (
            np.std(shuffled, ddof=1) / np.sqrt(len(shuffled)) if len(shuffled) > 1 else float("nan")
        )
        flag = "  LEAK?" if np.mean(shuffled) - 0.5 > 3 * control_se else ""
        print(
            f"    {'shuffled':<8} AUC {np.mean(shuffled):.4f} +/- {control_se:.4f} (SE, "
            f"{len(shuffled)} fits, {args.control_seeds} seeds){flag}"
        )

        # PAIRED. Same folds, same rows, so the difference is taken
        # fold by fold and it is the SPREAD OF THE DIFFERENCE that
        # says whether the lift is real -- not the spread of either
        # side, which is dominated by which years the fold covered.
        paired = np.array(per_fold["both"]) - np.array(per_fold["bar"])
        mean_lift, lift_deviation = float(paired.mean()), float(paired.std(ddof=1))
        # Standard error of the paired mean; with 5 folds this is a
        # weak test and is reported as such rather than as a p-value.
        standard_error = lift_deviation / np.sqrt(len(paired)) if len(paired) > 1 else float("nan")
        consistent = int((paired > 0).sum())

        if mean_lift > 2 * standard_error and consistent >= len(paired) - 1:
            verdict = "macro ADDS (consistent across folds)"
        elif mean_lift < -2 * standard_error:
            verdict = "macro HURTS"
        else:
            verdict = "INDISTINGUISHABLE from noise"

        print(
            f"    -> paired lift {mean_lift:+.4f} +/- {standard_error:.4f} (SE), "
            f"positive in {consistent}/{len(paired)} folds"
        )
        print(f"       per-fold: [{', '.join(f'{d:+.3f}' for d in paired)}]")
        print(f"       {verdict}")

        summary[ticker] = {
            "per_fold": per_fold,
            "paired_lift_mean": mean_lift,
            "paired_lift_se": float(standard_error),
            "folds_positive": consistent,
            "verdict": verdict,
            "base_rate": base_rate,
        }

    output = args.data / f"evaluation_{args.label}.json"
    output.write_text(json.dumps(summary, indent=2))
    print(f"\nwritten: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
