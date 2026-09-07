#!/usr/bin/env python
"""Join bars, cross-asset features and MFE labels into a training set.

    python tools/build_ml_dataset.py --tickers RSP COWZ SPYD
    python tools/build_ml_dataset.py --tickers SPYD --stride 1 --out data/ml

Writes one parquet per ticker plus a JSON schema recording which
columns are features, which are labels, and what was skipped.

--------------------------------------------------------------------
WHY STRIDE DEFAULTS TO 5 RATHER THAN 1

A minute bar is not an independent observation. Adjacent bars share
almost all of their trailing windows and most of their forward window,
so a million rows carry nowhere near a million observations' worth of
information -- but they do carry a million rows' worth of memory and
of false confidence in a validation score.

Stride 5 keeps the file workable (~200k rows on a 10-year ticker) and
loses little. It is not a substitute for splitting train and test by
TIME: overlapping forward windows still leak across any random split,
which is why the plan calls for WalkForwardRunner rather than
train_test_split. Use --stride 1 when that matters more than memory.

--------------------------------------------------------------------
FLOAT32 ON DISK

~120 columns over 200k rows is ~200MB in float64 and half that in
float32. These are features standardised into a model, not prices being
compared against a limit; the precision is not doing anything. The
LABELS stay float64 for the same reason they are float64 in labels.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.backtest import KNOWN_DATA
from src.ml import features, labels

# The targets this project actually trades, and horizons spanning an
# hour to roughly a month of sessions. A lot that needs four months is
# stuck capital, not a slow winner, so the horizons stop well short.
PROFIT_TARGETS = (0.003, 0.005, 0.01)
HORIZONS = (60, 390, 1950, 7800)


def build_one(ticker: str, path: Path, stride: int, external_directory: Path | None) -> tuple:
    bars = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    if bars.index.tz is None:
        bars.index = bars.index.tz_localize("UTC")

    # LABELS ARE COMPUTED ON EVERY BAR, THEN STRIDED. Computing them on
    # a strided frame would measure the horizon in strided bars -- a
    # 390-bar horizon would silently become 1950 real minutes.
    label_frame = labels.compute_grid(
        bars, profit_targets=PROFIT_TARGETS, horizons=HORIZONS, entry_column="close"
    )
    bar_frame = features.bar_features(bars)

    sampled = bars.index[::stride]
    external_frame = features.build(sampled, directory=external_directory)

    joined = pd.concat(
        [
            bars.loc[sampled, ["open", "high", "low", "close", "volume"]].astype(np.float32),
            bar_frame.loc[sampled].astype(np.float32),
            external_frame.astype(np.float32),
            label_frame.loc[sampled],
        ],
        axis=1,
    )
    joined.insert(0, "ticker", ticker)

    feature_columns = list(bar_frame.columns) + list(external_frame.columns)
    label_columns = list(label_frame.columns)
    return joined, feature_columns, label_columns


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickers", nargs="+", default=["RSP", "COWZ", "SPYD"])
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("data/ml"))
    parser.add_argument("--external", type=Path, default=None, help="Defaults to data/external/")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    schema: dict[str, dict] = {}

    for ticker in args.tickers:
        source = KNOWN_DATA.get(ticker)
        if source is None or not Path(source).exists():
            print(f"SKIP {ticker}: no data file registered in KNOWN_DATA")
            continue

        began = time.time()
        print(f"{ticker:<6} building ... ", end="", flush=True)
        frame, feature_columns, label_columns = build_one(
            ticker, Path(source), args.stride, args.external
        )

        destination = args.out / f"{ticker}_ml.parquet"
        frame.to_parquet(destination, index=True)

        # Reported per ticker, because a fund that listed in 2016 has a
        # different macro coverage profile from one that listed in 2003
        # and the average across tickers would hide it.
        usable = frame[feature_columns].notna().mean()
        primary = f"reached_t0.5_h{HORIZONS[1]}"
        hit_rate = frame[primary].mean() if primary in frame else float("nan")

        schema[ticker] = {
            "file": destination.name,
            "rows": len(frame),
            "stride": args.stride,
            "first": str(frame.index[0]),
            "last": str(frame.index[-1]),
            "feature_columns": feature_columns,
            "label_columns": label_columns,
            "features_fully_present": int((usable > 0.99).sum()),
            "features_below_half": sorted(usable[usable < 0.5].index),
            "base_rate": {
                column: float(frame[column].mean())
                for column in label_columns
                if column.startswith("reached_")
            },
        }

        print(
            f"{len(frame):>8,} rows  {len(feature_columns):>3} features  "
            f"{len(label_columns):>2} labels  {destination.stat().st_size / 1e6:6.1f} MB  "
            f"{time.time() - began:5.1f}s   base rate({primary})={hit_rate:.3f}"
        )

    if not schema:
        print("nothing built")
        return 1

    schema_path = args.out / "schema.json"
    schema_path.write_text(json.dumps(schema, indent=2))
    print(f"\nschema: {schema_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
