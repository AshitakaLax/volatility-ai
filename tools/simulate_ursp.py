#!/usr/bin/env python
"""Build a simulated URSP history from RSP, spliced with the real URSP.

    python tools/simulate_ursp.py                     # daily CSV to data/simulated/
    python tools/simulate_ursp.py --minutes           # + minute bars (needs RSP in the warehouse)
    python tools/simulate_ursp.py --out somewhere/ --spread 0.0209

URSP is ProShares Ultra S&P 500 Equal Weight: 2x the DAILY performance of
the S&P 500 Equal Weight Index, reset daily, 0.95% net expense ratio,
trading since 2025-08-27. RSP (Invesco S&P 500 Equal Weight, since 2003)
tracks the same index, so each session t, with d calendar days since the
previous one:

    index_t = RSP total return_t + 0.20% x d/365          (RSP's fee added back)
    URSP_t  = 2 x index_t - (DFF_t + spread) x d/360       (financing the borrowed 1x)
                          - 0.95% x d/365                  (URSP's fee)

`spread` is calibrated so the simulated total return over the overlap with
the real fund equals its actual total return (2.09%/yr as of 2026-10; it
absorbs a swap spread and the dividends the fund's price-return swaps do
not pay). Open, high and low follow the same daily-reset rule relative to
the previous close -- an increasing map of RSP's own day, so highs map to
highs. Volume is RSP's, scaled to URSP's traded level over the overlap, so
volume-based signals do not jump at the splice. The simulated history is
back-cast from the real fund's first close and the real bars follow it.

Two bad RSP prints are clipped before simulating (an intraday extreme more
than 6% beyond the day's open, close and prior close): the 2010-05-06 Flash
Crash low (-58%, trades that were later cancelled) and a stray 2007-08-01
high. Doubling the first would make the fund's price negative.

Minute bars (--minutes): on sessions where the warehouse holds RSP minutes,
the URSP day is that same day's RSP path mapped monotonically onto the URSP
day's open/high/low/close; other sessions borrow the most similar RSP day
(where the open and close sit inside the range). Daily OHLC is exact. The
CSV is in the warehouse's ingest format:

    python tools/build_warehouse.py --ingest URSP_SIM --csv data/simulated/URSP_simulated_1Min.csv

Inputs are public: Yahoo's chart API (RSP, URSP) and FRED (DFF), fetched
with research.ml.sources' HTTP helper, the same one fetch_market_inputs.py
uses.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

LEVERAGE = 2.0
ER_URSP = 0.0095
ER_RSP = 0.0020
BAD_PRINT = 0.06
DEFAULT_OUT = _REPO_ROOT / "data" / "simulated"
SESSION_MINUTES = 390


# ------------------------------------------------------------ inputs


def fetch_yahoo_daily(symbol: str) -> pd.DataFrame:
    """Daily OHLCV + adjusted close since inception (ET session dates)."""
    from research.ml.sources import _http_get

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        "?period1=0&period2=9999999999&interval=1d&events=div%2Csplit"
    )
    res = json.loads(_http_get(url).decode("utf-8", "replace"))["chart"]["result"][0]
    quote = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose") or quote["close"]
    tz = res["meta"].get("exchangeTimezoneName", "America/New_York")
    dates = pd.to_datetime(pd.Series(res["timestamp"]), unit="s", utc=True)
    index = dates.dt.tz_convert(tz).dt.normalize().dt.tz_localize(None)
    frame = pd.DataFrame(
        {
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["close"],
            "volume": quote["volume"],
            "adjclose": adj,
        },
        index=pd.DatetimeIndex(index.values, name="date"),
    )
    return frame.dropna(subset=["close"])


def fetch_dff() -> pd.Series:
    """FRED's daily effective federal funds rate, as a fraction."""
    from research.ml.sources import _http_get

    raw = pd.read_csv(
        io.BytesIO(_http_get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"))
    )
    raw.columns = ["date", "dff"]
    return pd.Series(
        pd.to_numeric(raw["dff"], errors="coerce").to_numpy() / 100.0,
        index=pd.DatetimeIndex(pd.to_datetime(raw["date"]), name="date"),
        name="dff",
    ).dropna()


# ------------------------------------------------------------ the formula


def adjusted(daily: pd.DataFrame, clean: bool = True) -> pd.DataFrame:
    """Dividend/split-adjusted OHLCV; clean clips bad intraday prints."""
    factor = daily["adjclose"] / daily["close"]
    out = daily[["open", "high", "low", "close"]].mul(factor, axis=0)
    out["volume"] = daily["volume"].astype(float)
    if clean:
        prev = out["close"].shift(1).fillna(out["open"])
        trio = pd.concat([out["open"], out["close"], prev], axis=1)
        out["low"] = out["low"].clip(lower=trio.min(axis=1) * (1 - BAD_PRINT))
        out["high"] = out["high"].clip(upper=trio.max(axis=1) * (1 + BAD_PRINT))
    return out


def daily_drag(index: pd.DatetimeIndex, rate: pd.Series, spread: float) -> np.ndarray:
    """Per-session cost of the fund, from calendar days since the last session."""
    days = index.to_series().diff().dt.days.fillna(1).to_numpy()
    full = pd.date_range(min(rate.index[0], index[0]), index[-1])
    r = rate.reindex(full).ffill().bfill().reindex(index).to_numpy()
    return (
        (r + spread) * (LEVERAGE - 1) * days / 360
        + ER_URSP * days / 365
        - LEVERAGE * ER_RSP * days / 365
    )


def simulate(rsp_adjusted: pd.DataFrame, rate: pd.Series, spread: float) -> pd.DataFrame:
    """Simulated URSP OHLCV on RSP's sessions, starting at 100."""
    a = rsp_adjusted
    drag = daily_drag(a.index, rate, spread)
    prev = a["close"].shift(1).to_numpy()
    cols = {k: np.empty(len(a)) for k in ("open", "high", "low", "close")}
    level = 100.0
    for i in range(len(a)):
        if i == 0:
            for k in cols:
                cols[k][0] = 100.0 * a[k].iloc[0] / a["close"].iloc[0]
            continue
        for k in cols:
            cols[k][i] = level * (1.0 + LEVERAGE * (a[k].iloc[i] / prev[i] - 1.0) - drag[i])
        level = cols["close"][i]
    out = pd.DataFrame(cols, index=a.index)
    out["volume"] = a["volume"].to_numpy(float)
    return out


def calibrate_spread(rsp_adjusted, ursp_daily, rate, lo=-0.05, hi=0.10) -> float:
    """The spread at which the simulated total return over the overlap with
    the real fund equals its actual (adjusted-close) total return."""
    actual = ursp_daily["adjclose"]
    target = actual.iloc[-1] / actual.iloc[0]
    for _ in range(60):
        mid = (lo + hi) / 2
        sim = simulate(rsp_adjusted, rate, mid)["close"].reindex(actual.index)
        if sim.iloc[-1] / sim.iloc[0] > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def splice(
    simulated: pd.DataFrame, rsp_daily: pd.DataFrame, ursp_daily: pd.DataFrame
) -> pd.DataFrame:
    """Simulated history back-cast from the real fund's first close, then the
    real (adjusted) fund. Simulated volume is scaled to URSP's level."""
    real = adjusted(ursp_daily, clean=False)
    first = real.index[0]
    k = float((ursp_daily["volume"] / rsp_daily["volume"].reindex(ursp_daily.index)).median())
    hist = simulated.loc[simulated.index < first].copy()
    hist[["open", "high", "low", "close"]] *= real["close"].iloc[0] / simulated.loc[first, "close"]
    hist["volume"] = hist["volume"] * k
    out = pd.concat([hist.assign(source="simulated"), real.assign(source="actual")])
    out.index.name = "date"
    return out


# ------------------------------------------------------------ minute bars


def rsp_minute_library() -> dict:
    """RSP sessions from the warehouse as (n, 390) arrays (gaps filled flat)."""
    from engine.warehouse.bars import load_frame

    m = load_frame("RSP")
    et = m.index.tz_convert("America/New_York")
    minute = (et.hour * 60 + et.minute) - 570
    keep = (minute >= 0) & (minute < SESSION_MINUTES)
    m, et, minute = m[keep], et[keep], minute[keep]
    day = et.normalize().tz_localize(None)
    days = day.unique()
    pos = {d: i for i, d in enumerate(days)}
    row = np.fromiter((pos[d] for d in day), int, len(day))
    arr = {
        k: np.full((len(days), SESSION_MINUTES), np.nan)
        for k in ("open", "high", "low", "close", "volume")
    }
    for k in arr:
        arr[k][row, minute] = m[k].to_numpy(float)
    full = np.isfinite(arr["close"]).sum(axis=1) >= 300
    for k in arr:
        arr[k] = arr[k][full]
    days = days[full]
    for i in range(len(days)):
        fill = arr["open"][i, np.flatnonzero(np.isfinite(arr["close"][i]))[0]]
        for j in range(SESSION_MINUTES):
            if np.isfinite(arr["close"][i, j]):
                fill = arr["close"][i, j]
            else:
                for k in ("open", "high", "low", "close"):
                    arr[k][i, j] = fill
                arr["volume"][i, j] = 0.0
    o, h, lo, c = arr["open"][:, 0], arr["high"].max(1), arr["low"].min(1), arr["close"][:, -1]
    rng = np.where(h > lo, h - lo, np.nan)
    tot = arr["volume"].sum(1, keepdims=True)
    return {
        "pos": {d: i for i, d in enumerate(days)},
        "o": arr["open"],
        "h": arr["high"],
        "l": arr["low"],
        "c": arr["close"],
        "share": arr["volume"] / np.where(tot > 0, tot, 1.0),
        "DO": o,
        "DH": h,
        "DL": lo,
        "DC": c,
        "u": (o - lo) / rng,
        "v": (c - lo) / rng,
    }


def _monotone(x, knots_x, knots_y):
    kx, idx = np.unique(knots_x, return_index=True)
    return np.interp(x, kx, np.asarray(knots_y)[idx])


def minute_bars(daily: pd.DataFrame, lib: dict, seed: int = 1, k: int = 30) -> pd.DataFrame:
    """Minute bars whose sessions aggregate exactly to `daily`'s OHLC."""
    rng = np.random.default_rng(seed)
    U = np.concatenate([lib["u"], 1 - lib["u"]])
    V = np.concatenate([lib["v"], 1 - lib["v"]])
    up, valid, n = V >= U, np.isfinite(U) & np.isfinite(V), len(lib["u"])
    offsets = pd.to_timedelta(np.arange(SESSION_MINUTES), unit="min")
    parts = {c: [] for c in ("open", "high", "low", "close", "volume")}
    stamps = []
    for date, row in daily.iterrows():
        d_open, d_high, d_low, d_close, d_vol = (
            float(row[c]) for c in ("open", "high", "low", "close", "volume")
        )
        start = pd.Timestamp(date).tz_localize("America/New_York") + pd.Timedelta(
            hours=9, minutes=30
        )
        stamps.append((start + offsets).tz_convert("UTC"))
        if not d_high > d_low:
            for c in ("open", "high", "low", "close"):
                parts[c].append(np.full(SESSION_MINUTES, d_close))
            parts["volume"].append(np.full(SESSION_MINUTES, d_vol / SESSION_MINUTES))
            continue
        d = pd.Timestamp(date)
        if d in lib["pos"]:
            i, flip = lib["pos"][d], False
        else:
            ut, vt = (d_open - d_low) / (d_high - d_low), (d_close - d_low) / (d_high - d_low)
            cand = np.flatnonzero(valid & (up == (vt >= ut)))
            dist = (U[cand] - ut) ** 2 + (V[cand] - vt) ** 2
            pick = int(rng.choice(cand[np.argpartition(dist, min(k, len(cand) - 1))[:k]]))
            flip, i = pick >= n, pick % n
        DO, DH, DL, DC = lib["DO"][i], lib["DH"][i], lib["DL"][i], lib["DC"][i]
        o, h, lo, c = lib["o"][i], lib["h"][i], lib["l"][i], lib["c"][i]
        if flip:
            o, h, lo, c = DH + DL - o, DH + DL - lo, DH + DL - h, DH + DL - c
            DO, DC = DH + DL - DO, DH + DL - DC
        if not DH > DL:
            o = h = lo = c = np.linspace(d_open, d_close, SESSION_MINUTES)
            DO, DH, DL, DC = d_open, max(d_open, d_close), min(d_open, d_close), d_close
        kx, ky = (
            [DL, min(DO, DC), max(DO, DC), DH],
            [d_low, min(d_open, d_close), max(d_open, d_close), d_high],
        )
        mo, mh, ml, mc = (_monotone(a, kx, ky) for a in (o, h, lo, c))
        mo[0], mc[-1] = d_open, d_close
        mh = np.minimum(np.maximum.reduce([mh, mo, mc]), d_high)
        ml = np.maximum(np.minimum.reduce([ml, mo, mc]), d_low)
        mh[np.argmax(mh)] = d_high
        ml[np.argmin(ml)] = d_low
        for col, a in (("open", mo), ("high", mh), ("low", ml), ("close", mc)):
            parts[col].append(a)
        parts["volume"].append(d_vol * lib["share"][i])
    index = pd.DatetimeIndex(np.concatenate([s.values for s in stamps])).tz_localize("UTC")
    out = pd.DataFrame({c: np.concatenate(v) for c, v in parts.items()}, index=index)
    out["volume"] = out["volume"].round().astype("int64")
    out.index.name = "timestamp"
    return out


# ------------------------------------------------------------ CLI


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument(
        "--spread",
        type=float,
        default=None,
        help="financing spread over DFF (default: calibrate on the overlap)",
    )
    parser.add_argument(
        "--minutes", action="store_true", help="also write warehouse-format minute bars"
    )
    parser.add_argument(
        "--seed", type=int, default=1, help="donor choice for sessions without RSP minutes"
    )
    args = parser.parse_args(argv)

    rsp_raw, ursp_raw, dff = fetch_yahoo_daily("RSP"), fetch_yahoo_daily("URSP"), fetch_dff()
    rsp = adjusted(rsp_raw)
    spread = args.spread if args.spread is not None else calibrate_spread(rsp, ursp_raw, dff)
    series = splice(simulate(rsp, dff, spread), rsp_raw, ursp_raw)
    args.out.mkdir(parents=True, exist_ok=True)
    daily_path = args.out / "URSP_simulated_daily.csv"
    series.to_csv(daily_path, float_format="%.6f")
    sim = series[series["source"] == "simulated"]
    print(f"spread over DFF: {spread * 100:.2f}%/yr")
    print(
        f"wrote {daily_path}: {len(series)} sessions, simulated {sim.index[0].date()} -> "
        f"{sim.index[-1].date()}, actual URSP {series.index[len(sim)].date()} -> {series.index[-1].date()}"
    )
    if args.minutes:
        bars = minute_bars(series, rsp_minute_library(), seed=args.seed)
        minute_path = args.out / "URSP_simulated_1Min.csv"
        bars.to_csv(minute_path, float_format="%.6f", date_format="%Y-%m-%d %H:%M:%S+00:00")
        print(
            f"wrote {minute_path}: {len(bars):,} bars. Ingest with:\n"
            f"  python tools/build_warehouse.py --ingest URSP_SIM --csv {minute_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
