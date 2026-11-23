#!/usr/bin/env python
"""
Every time a 3x Nasdaq-100 fell 43% since 1985, and what an opening seed
ladder bought there would have done -- the long-history half of
docs/research/forecast-harvest.md's "How to start".

    python tools/probe_crash_entries.py [--out FILE.csv]

The warehouse's minute bars begin in 2016, four crossings ago. To see the
crashes a 3x fund did not survive in its own history (2000-02, 2008), this
builds a DAILY 3x Nasdaq-100 from data/external/yahoo_NDX.csv (VAI_EXTERNAL_DIR):

    r_3x = 3 r_NDX - 2 x the effective fed funds rate / 252 - 0.95% / 252

(the rate from fred_EFFR, fred_DGS3MO before it, 6% before both), checked
against TQQQ's own closes from 2010. A crossing is the first session the fund
closes 43% below its 504-session high; the next needs a recovery to within
20% of that high first. From each crossing, over three years at most:

  the fund      held from the crossing's close
  a seed plan   tranches of `pct` of the capital bought at falls of `levels`
                below the crossing's close, each sold at +target (or held:
                target None); the rest stays in cash

Reported as multiples of the starting capital. This is the seed sleeve
alone; the trading book beside it is the minute engine's
(tools/probe_forecast_harvest.py --stage entry).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
FALL = 0.43
HIGH_WINDOW = 504
RESET = 0.20
HORIZON = 756
EXPENSE = 0.0095
PLANS: dict[str, tuple[tuple[float, ...], float]] = {
    "all-in at 0": ((0.0,), 1.0),
    "seed 40% at 0": ((0.0,), 0.4),
    "ladder 3x20% 0/15/30": ((0.0, 0.15, 0.30), 0.2),
    "ladder 3x15% 0/20/40": ((0.0, 0.20, 0.40), 0.15),
    "deep 3x15% 10/25/40": ((0.10, 0.25, 0.40), 0.15),
    "ladder 4x10% 0/10/20/30": ((0.0, 0.10, 0.20, 0.30), 0.1),
}
TARGETS = (0.5, 1.0, None)


def _series(name: str) -> pd.Series:
    folder = Path(os.environ.get("VAI_EXTERNAL_DIR") or _REPO_ROOT / "data" / "external")
    d = pd.read_csv(folder / f"{name}.csv")
    idx = pd.to_datetime(d["timestamp"], utc=True).dt.tz_convert("America/New_York")
    return pd.Series(
        d["close"].astype(float).to_numpy(), index=idx.dt.tz_localize(None).dt.normalize()
    )


def simulated_3x() -> pd.Series:
    ndx = _series("yahoo_NDX")
    rate = _series("fred_EFFR").reindex(ndx.index, method="ffill")
    rate = rate.fillna(_series("fred_DGS3MO").reindex(ndx.index, method="ffill")).fillna(6.0) / 100
    r = ndx.pct_change().fillna(0.0)
    return (1 + 3 * r - 2 * rate.shift(1).fillna(0.06) / 252 - EXPENSE / 252).cumprod()


def validation(sim: pd.Series) -> dict:
    tqqq = _series("yahoo_TQQQ")
    both = pd.concat([sim, tqqq], axis=1, keys=["sim", "tqqq"]).dropna()
    both = both[both.index >= "2010-03-01"]
    years = (both.index[-1] - both.index[0]).days / 365.25

    def cagr(s):
        return (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1

    return {
        "daily_corr": float(both["sim"].pct_change().corr(both["tqqq"].pct_change())),
        "sim_cagr": cagr(both["sim"]) * 100,
        "tqqq_cagr": cagr(both["tqqq"]) * 100,
    }


def crossings(px: pd.Series) -> list[pd.Timestamp]:
    dd = px / px.rolling(HIGH_WINDOW, min_periods=1).max() - 1
    out, inside = [], False
    for day, v in dd.items():
        if not inside and v <= -FALL:
            inside = True
            out.append(day)
        elif inside and v >= -RESET:
            inside = False
    return out


def seed_path(seg: pd.Series, levels, pct: float, target: float | None) -> pd.Series:
    anchor = float(seg.iloc[0])
    cash, lots, filled, values = 1.0, [], 0, []
    for p in seg.to_numpy(float):
        while filled < len(levels) and p <= anchor * (1 - levels[filled]):
            lots.append([pct / p, p])
            cash -= pct
            filled += 1
        if target is not None:
            for lot in lots:
                if lot[0] > 0 and p >= lot[1] * (1 + target):
                    cash += lot[0] * p
                    lot[0] = 0.0
        values.append(cash + sum(lot[0] for lot in lots) * p)
    return pd.Series(values, index=seg.index)


def run() -> tuple[dict, pd.DataFrame]:
    px = simulated_3x()
    rows = []
    for start in crossings(px):
        seg = px[px.index >= start].iloc[: HORIZON + 1]
        fund = seg / seg.iloc[0]
        for plan, (levels, pct) in PLANS.items():
            for target in TARGETS:
                v = seed_path(seg, levels, pct, target)

                def at(series, n):
                    return float(series.iloc[min(n, len(series) - 1)])

                rows.append(
                    {
                        "start": str(start.date()),
                        "plan": plan,
                        "target": target,
                        "sessions": len(seg) - 1,
                        "low": float(v.min()),
                        "y1": at(v, 252),
                        "y2": at(v, 504),
                        "y3": at(v, 756),
                        "fund_low": float(fund.min()),
                        "fund_y1": at(fund, 252),
                        "fund_y3": at(fund, 756),
                    }
                )
    return validation(px), pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    check, df = run()
    print(
        f"validation 2010-2026: daily corr {check['daily_corr']:.4f}, CAGR {check['sim_cagr']:.1f}% "
        f"simulated vs {check['tqqq_cagr']:.1f}% TQQQ"
    )
    if args.out:
        df.to_csv(args.out, index=False)
    full = df[df["sessions"] >= 252]
    summary = full.groupby(["plan", "target"], dropna=False).agg(
        crossings=("y1", "size"),
        worst_low=("low", "min"),
        worst_y1=("y1", "min"),
        median_y1=("y1", "median"),
        best_y1=("y1", "max"),
        worst_y3=("y3", "min"),
        median_y3=("y3", "median"),
        best_y3=("y3", "max"),
    )
    pd.set_option("display.width", 200)
    print(summary.round(2).to_string())
    fund = full[(full["plan"] == "all-in at 0") & full["target"].isna()]
    print(fund[["start", "fund_low", "fund_y1", "fund_y3"]].round(2).to_string(index=False))
    return 0


if __name__ == "__main__":
    np.seterr(all="ignore")
    raise SystemExit(main())
