#!/usr/bin/env python
"""What each indicator says about SELLING: when, and for how much.

The Stage 1 sweep asked one question -- should I be in the market. This
asks the two that decide a grid strategy's exits:

  EXIT TRIGGER   Given a position is open, does this indicator firing
                 mean the next stretch is bad enough to leave?
  TARGET SIZE    Given it has just fired, how much upside is actually
                 available afterwards -- which is what a profit target
                 is a bet about.

--------------------------------------------------------------------
WHY EXCURSIONS AND NOT FORWARD RETURNS

`target_sell_price = buy_price * (1 + profit_target)` (src/ledger.py:92).
That order fills if price EVER touches the target inside the holding
window, not if price happens to be above it on some future day. So the
quantity that decides whether a target is reachable is the MAXIMUM
FAVOURABLE EXCURSION -- the best price seen between here and the horizon
-- and mean forward return is the wrong statistic entirely. A window that
rallies 30% and gives it all back has a forward return near zero and a
target of 30% that filled comfortably.

MAE, the mirror, is what the position had to sit through to get there.
Reported alongside because a 20% target reachable only after a 40%
drawdown is not the same instrument as one reachable smoothly, and the
no-loss guard means the second lot never sells at all.

--------------------------------------------------------------------
THE STATISTIC THAT ANSWERS "WHAT SHOULD THE TARGET BE"

`mfe_p50` is the median maximum favourable excursion: the profit target
that would have been reached about half the time within the horizon.
`mfe_p25` is the conservative one, reached three-quarters of the time.
Neither is a recommendation on its own -- a target reached 75% of the
time leaves the other 25% held indefinitely, which under enforce_no_loss
means held forever -- but they bound the sensible range, which is more
than the current champion's +75% and +110% were chosen against.

Overlapping windows, so these are NOT independent observations and no
significance test is computed from them. They describe a distribution;
they do not test a hypothesis.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from src.indicator_library import (
    available,
    compute,
    load_bars,
    signals,
    warmup_bars,
)
from tools.indicator_sweep import INSTRUMENTS

HORIZONS = (5, 20, 60)


def excursions(bars: pd.DataFrame, horizon: int) -> tuple[pd.Series, pd.Series]:
    """Best and worst price reached within `horizon` bars, as percentages.

    Forward-looking BY CONSTRUCTION -- that is the measurement, not a
    leak. Nothing here trades on it; it describes what was available to a
    position opened at each bar. The Stage 1 sweep is where signals are
    shifted and lookahead would be a bug.
    """
    close = bars["close"]
    fwd_high = bars["high"].shift(-1).rolling(horizon, min_periods=1).max().shift(-(horizon - 1))
    fwd_low = bars["low"].shift(-1).rolling(horizon, min_periods=1).min().shift(-(horizon - 1))
    return (fwd_high / close - 1) * 100, (fwd_low / close - 1) * 100


def study(symbol: str, include_patterns: bool, horizon: int) -> pd.DataFrame:
    spec = INSTRUMENTS[symbol]
    bars = load_bars(spec["path"])
    mfe, mae = excursions(bars, horizon)

    rows = []
    for ind in available(include_patterns=include_patterns):
        try:
            values = compute(ind, bars)
        except Exception:
            continue
        skip = warmup_bars(ind)
        for out in ind.outputs:
            try:
                states = signals(values[out], ind)
            except Exception:
                continue
            for state, mask in states.items():
                m = mask.iloc[skip:].fillna(False)
                f, a = mfe.iloc[skip:][m], mae.iloc[skip:][m]
                f, a = f.dropna(), a.dropna()
                if len(f) < 100:
                    continue  # too rare to describe a distribution
                rows.append(
                    {
                        "instrument": symbol,
                        "indicator": ind.name,
                        "output": out,
                        "state": state,
                        "n": len(f),
                        "pct_of_bars": round(
                            len(f) / max(len(mfe.iloc[skip:].dropna()), 1) * 100, 1
                        ),
                        "mfe_mean": round(float(f.mean()), 3),
                        "mfe_p25": round(float(f.quantile(0.25)), 3),
                        "mfe_p50": round(float(f.median()), 3),
                        "mfe_p75": round(float(f.quantile(0.75)), 3),
                        "mae_p50": round(float(a.median()), 3),
                        "edge_ratio": round(float(f.median() / abs(a.median())), 3)
                        if a.median()
                        else None,
                    }
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    # The baseline is every bar, unconditionally. An indicator state only
    # matters if the excursion available AFTER it differs from what was
    # available anyway -- a state whose MFE matches the baseline is
    # telling you nothing, however large its absolute number looks on a
    # 3x leveraged fund.
    base_f = mfe.dropna()
    base_a = mae.dropna()
    frame["baseline_mfe_p50"] = round(float(base_f.median()), 3)
    frame["mfe_lift"] = (frame["mfe_p50"] - float(base_f.median())).round(3)
    frame["baseline_mae_p50"] = round(float(base_a.median()), 3)
    frame["horizon"] = horizon
    return frame


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default="output/indicator_exits.csv")
    p.add_argument("--no-patterns", action="store_true")
    p.add_argument("--horizons", type=int, nargs="+", default=list(HORIZONS))
    args = p.parse_args(argv)

    frames = []
    for symbol in INSTRUMENTS:
        for h in args.horizons:
            f = study(symbol, not args.no_patterns, h)
            if not f.empty:
                frames.append(f)
            print(f"[exits] {symbol} h={h}: {len(f)} indicator states", flush=True)
    out = pd.concat(frames, ignore_index=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"[exits] wrote {len(out)} rows -> {args.out}\n")

    for symbol in INSTRUMENTS:
        for h in args.horizons:
            sub = out[(out.instrument == symbol) & (out.horizon == h)]
            if sub.empty:
                continue
            base = sub.baseline_mfe_p50.iloc[0]
            print(f"=== {symbol}, {h}-day horizon | baseline median MFE {base:.2f}% ===")
            cols = ["indicator", "output", "state", "pct_of_bars", "mfe_p50", "mfe_lift", "mae_p50"]
            print("  BEST to hold through (largest upside available after):")
            print(sub.nlargest(5, "mfe_lift")[cols].to_string(index=False))
            print("  WORST -- exit candidates (least upside available after):")
            print(sub.nsmallest(5, "mfe_lift")[cols].to_string(index=False))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
