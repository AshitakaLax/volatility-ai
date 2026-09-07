#!/usr/bin/env python
"""Which BLOCK of macro features carries a lift, not just whether "macro" does.

    python tools/ablate_ml_features.py --tickers RSP COWZ SPYD

tools/evaluate_ml_features.py answers "does macro help": one paired
number per ticker. That is not enough to act on, because "macro" here
is 73 columns across fourteen categories (vol, credit, rotation, factor,
rates, ...), and a lift attributed to all of them together could be
coming from one. This adds each CATEGORY to the bar-only baseline
separately, on the same purged folds, and reports which ones actually
move the needle.

Writes data/ml/ablation_<label>.json, read by server/ml_insights.py --
this is a precomputed artifact, not something served live, because
fitting ~14 categories x N tickers x 5 folds of LightGBM is minutes of
work and an HTTP request is not the place for that.

--------------------------------------------------------------------
WHY THIS IS NOT A CLEAN MULTIPLE-COMPARISONS TEST, AND SAYS SO

Fourteen categories times however many tickers is that many comparisons,
and "5/5 folds positive" by chance alone happens on the order of 1 in 32
times per comparison. With this many comparisons run, roughly one
"consistent" block is expected from chance alone. No p-value correction
is applied here, because the categories are not independent -- vol and
credit both move on the same broad risk-off days -- and a standard
Bonferroni-style correction assumes independence it does not have. The
honest position is: more consistent blocks than the ~1 chance would
supply is suggestive, not proof, and it is reported as exactly that
rather than dressed up with a correction that does not apply.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

warnings.filterwarnings("ignore", category=UserWarning)

from src.ml.features import catalogue
from tools.evaluate_ml_features import evaluate, folds, split_columns


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickers", nargs="+", default=["RSP", "COWZ", "SPYD"])
    parser.add_argument("--data", type=Path, default=Path("data/ml"))
    parser.add_argument("--label", default="reached_t0.5_h390")
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args(argv)

    schema = json.loads((args.data / "schema.json").read_text())
    horizon = int(args.label.split("_h")[-1])

    by_category: dict[str, list[str]] = {}
    for feature in catalogue():
        by_category.setdefault(feature.category, []).append(feature.name)

    result: dict[str, dict] = {}
    started = time.time()

    for ticker in args.tickers:
        if ticker not in schema:
            print(f"SKIP {ticker}: not in schema")
            continue

        frame = pd.read_parquet(args.data / schema[ticker]["file"])
        stride = schema[ticker]["stride"]
        purge = int(np.ceil(horizon / stride))
        bar_columns, macro_columns = split_columns(schema, ticker)
        fold_list = list(folds(len(frame), args.folds, purge))

        baseline = np.array(evaluate(frame, bar_columns, args.label, fold_list))
        print(f"\n{ticker}  bar-only baseline AUC {baseline.mean():.4f}  ({len(fold_list)} folds)")

        blocks = []
        for category in sorted(by_category):
            columns = [c for c in by_category[category] if c in macro_columns]
            if not columns:
                continue
            scores = np.array(evaluate(frame, bar_columns + columns, args.label, fold_list))
            if len(scores) != len(baseline):
                # A category that made a fold degenerate (e.g. every
                # value identical in that window) is skipped for that
                # ticker rather than compared against a mismatched
                # baseline length.
                continue
            lift = scores - baseline
            mean, se = float(lift.mean()), float(lift.std(ddof=1) / np.sqrt(len(lift)))
            positive = int((lift > 0).sum())
            consistent = bool(mean > 2 * se and positive >= len(lift) - 1)
            blocks.append(
                {
                    "category": category,
                    "columns": len(columns),
                    "lift_mean": mean,
                    "lift_se": se,
                    "folds_positive": positive,
                    "folds_total": len(lift),
                    "consistent": consistent,
                }
            )
            flag = "  <-- consistent" if consistent else ""
            print(
                f"    +{category:<14} ({len(columns):>2} cols)  lift {mean:+.4f} +/- {se:.4f}  "
                f"{positive}/{len(lift)} folds{flag}"
            )

        blocks.sort(key=lambda b: b["lift_mean"], reverse=True)
        result[ticker] = {
            "baseline_auc": float(baseline.mean()),
            "blocks": blocks,
            "consistent_count": sum(1 for b in blocks if b["consistent"]),
            "total_blocks": len(blocks),
        }

    output = args.data / f"ablation_{args.label}.json"
    output.write_text(json.dumps(result, indent=2))
    print(f"\nwritten: {output}  ({time.time() - started:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
