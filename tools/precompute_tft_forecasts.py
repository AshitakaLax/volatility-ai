#!/usr/bin/env python
"""Make a trained TFT's forecast for every bar of its fund once, so a sweep of
ml_tft / tft_take_profit runs looks them up instead of running the model
on every trigger (research/ml/tft_cache.py: exact, keyed by the inputs).

    python tools/precompute_tft_forecasts.py --model data/ml/models/tft_tqqq
    # then: strategy_params.forecast_cache: data/ml/models/tft_tqqq/forecasts.npz

The bars are the warehouse's for the model's fund, from --start (default:
the model's valid_from) -- the date the runs that read the table must start
on, since the ring's first row is the first bar's. Needs requirements-dl.txt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.ml import tft_cache
from research.ml.meta_training import window
from research.ml.tft_model import read_manifest

DEFAULT_FILE = "forecasts.npz"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="A directory tft_training.py wrote")
    parser.add_argument("--start", default=None, help="First session (default: valid_from)")
    parser.add_argument("--end", default=None, help="Last session (default: the latest bar)")
    parser.add_argument("--out", type=Path, default=None, help=f"Default: <model>/{DEFAULT_FILE}")
    parser.add_argument("--workers", type=int, default=None, help="Processes (default: all cores)")
    args = parser.parse_args(argv)

    from engine.warehouse.bars import load_frame

    manifest = read_manifest(args.model)
    start = args.start or manifest["valid_from"][:10]
    bars = window(load_frame(manifest["symbol"]), start, args.end)
    if bars.empty:
        raise SystemExit(f"no {manifest['symbol']} bars in the warehouse from {start}")
    print(f"{manifest['symbol']}: {len(bars):,} bars {bars.index[0]} .. {bars.index[-1]}")
    out = args.out or Path(args.model) / DEFAULT_FILE
    tft_cache.precompute(args.model, bars, out, workers=args.workers)
    print(tft_cache.summary(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
