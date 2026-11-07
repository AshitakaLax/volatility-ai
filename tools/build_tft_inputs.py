#!/usr/bin/env python
"""Write the TFT's outside series (s_news, s_macro, s_earnings) from the
warehouse, for a training config's `sources:`.

    python tools/fetch_market_inputs.py --refresh       # the free series
    python tools/build_warehouse.py --external          # ... into the warehouse
    python tools/build_tft_inputs.py                    # -> data/ml/inputs/*.csv
    python cli.py train --config config/ml/tft_tqqq_inputs.yaml

What each series is, and why it stands in for what the TFT's design names,
is research/ml/tft_inputs.py's docstring. Each CSV is `timestamp,value`,
every row stamped when it could first be read.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.ml import tft_inputs

DEFAULT_OUT = _REPO_ROOT / "data" / "ml" / "inputs"


def _root() -> Path:
    return Path(os.environ.get("VAI_WAREHOUSE_DIR") or _REPO_ROOT / "warehouse")


def _series(con, key: str) -> pd.Series:
    frame = con.execute(
        "SELECT timestamp, close FROM market_data.external WHERE series_key = ? ORDER BY timestamp",
        [key],
    ).fetchdf()
    if frame.empty:
        raise SystemExit(
            f"the warehouse has no {key}: run tools/fetch_market_inputs.py, then "
            "tools/build_warehouse.py --external"
        )
    index = pd.DatetimeIndex(frame["timestamp"])
    index = index.tz_localize("UTC") if index.tz is None else index.tz_convert("UTC")
    return pd.Series(frame["close"].to_numpy(float), index=index)


def build(root: Path) -> dict[str, pd.Series]:
    from engine.warehouse.connection import open_warehouse

    with open_warehouse(root, read_only=True) as con:
        news = _series(con, tft_inputs.NEWS_SERIES)
        epu = _series(con, tft_inputs.UNCERTAINTY_SERIES)
        benchmark = _series(con, tft_inputs.BENCHMARK_SERIES)
        events = con.execute(
            "SELECT ticker, event_timestamp AS release FROM market_data.market_events "
            "WHERE event_type = 'earnings' ORDER BY event_timestamp"
        ).fetchdf()
        tickers = sorted(set(events["ticker"]))
        known = set(
            con.execute("SELECT series_key FROM market_data.external_series").fetchdf()[
                "series_key"
            ]
        )
        closes = {t: _series(con, f"yahoo_{t}") for t in tickers if f"yahoo_{t}" in known}
    missing = sorted(set(tickers) - set(closes))
    if missing:
        print(f"no daily closes for {', '.join(missing)}: their releases are left out")
    return {
        "s_news": tft_inputs.news_sentiment(news),
        "s_macro": tft_inputs.uncertainty_shock(epu),
        "s_earnings": tft_inputs.earnings_reaction(events, closes, benchmark),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Defaults to data/ml/inputs/")
    parser.add_argument("--root", type=Path, default=None, help="The warehouse directory")
    args = parser.parse_args(argv)
    series = build(args.root or _root())
    args.out.mkdir(parents=True, exist_ok=True)
    for name, values in series.items():
        path = args.out / f"{name}.csv"
        tft_inputs.as_csv_frame(values).to_csv(path, index=False)
        print(
            f"{name:<11} {len(values):>6,} rows  {values.index[0].date()} -> "
            f"{values.index[-1].date()}  mean {values.mean():+.3f}  sd {values.std():.3f}  -> {path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
