"""
Enhancement 3/5: screen candidate instruments for this strategy's real
character, rather than assuming one from familiarity.

--------------------------------------------------------------------
WHY THESE CANDIDATES, AND WHY NOT JUST MORE TQQQ TUNING

The frontier sweep's own regime breakdown is the argument: this
strategy wins decisively in down/crash months (100% win rate, crash
< -15%) and loses badly in rallies (6% win rate, rally > +15%). TQQQ
over 2016-2026 had far more up/rally months than crash/down ones, so
the strategy is fighting its own instrument's secular trend the whole
time. A mean-reverting, range-bound instrument is structurally the
better fit -- not a bigger parameter search on the same fight.

TNA (3x Russell 2000) and SOXL (3x semiconductors) are the two
candidates: small-caps have been far more range-bound over this window
than the Nasdaq-100, and semis are more cyclical than secularly
trending. FAS (3x financials) is a third, similarly cyclical
comparison point. SPXL (3x S&P 500) is included as a CONTROL -- large-
cap-broad, structurally similar to TQQQ's own trend character -- so the
screen has something to confirm against, not just new candidates to
hope about.

--------------------------------------------------------------------
WHAT THIS MEASURES, AND WHY EACH ONE

Buy-and-hold CAGR and max drawdown: is this instrument's own baseline
even survivable at 3x leverage over the window -- a candidate that
decayed to near zero already answers the question regardless of what a
strategy could do with it.

Variance ratio (VR), the actual mean-reversion/trend test: for k-bar
returns, VR(k) = Var(k-bar return) / (k * Var(1-bar return)). VR < 1
means returns partially cancel over longer horizons (mean-reverting);
VR > 1 means they compound (trending); VR = 1 is a random walk. This is
the real answer to "is this instrument more mean-reverting than TQQQ,"
measured rather than assumed from sector reputation.

Annualized realized volatility: this strategy's sizing scales with it
(vol_scale_exponent) and its no-loss guard needs SOME volatility to
harvest at all -- a candidate calmer than TQQQ may simply not retrigger
enough regardless of trend character (the exact problem
HighFrequencyLocalReferenceSizing's own module docstring documents
about the default trigger on quiet instruments).

--------------------------------------------------------------------
THIS PULLS DATA. It does not run the trading strategy against these
candidates -- that is a second, separate step once a screen result
justifies spending sweep budget on a specific symbol, mirroring how
this project always measures before tuning.
"""

from __future__ import annotations

import logging

# tools/ scripts import from src/, and Python puts THIS file's directory
# on sys.path[0] -- not the working directory -- so `python
# tools/screen_instruments.py` would otherwise fail on `from src...` while
# `python -m tools.screen_instruments` succeeded. Same bootstrap as
# tests/fixtures/regression_baseline.py, so both invocations work.
import os as _os
import sys
import sys as _sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

from src.data_validation import validate
from src.hf_market_data import HFMarketData
from src.historical_data import FetchSpec, write_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("screen")

# TQQQ is the reference point the whole comparison is against, not a
# fifth candidate -- its own numbers are already known from the
# frontier sweep's regime table.
CANDIDATES = {
    "TNA": "3x Russell 2000 (small-cap) -- candidate: more range-bound?",
    "SOXL": "3x semiconductors -- candidate: cyclical, less secular trend",
    "FAS": "3x financials -- candidate: cyclical, rate-sensitive",
    "SPXL": "3x S&P 500 -- CONTROL: broad large-cap, trend character like TQQQ",
}

START = datetime(2016, 1, 1, tzinfo=UTC)
END = datetime(2026, 8, 21, tzinfo=UTC)
PARTS_DIR = Path("data/screen_parts")

# Generous retry budget: the provider was observed unresponsive on
# every endpoint for an extended stretch this session, including
# endpoints confirmed working minutes earlier. Each request will wait
# up to max_retries * mean(backoff schedule) rather than fail fast into
# a script meant to run unattended.
CLIENT_KW = {"max_retries": 20, "retry_backoff_seconds": 15.0}


def variance_ratio(returns: np.ndarray, k: int) -> float:
    """VR(k) = Var(k-bar return) / (k * Var(1-bar return)).

    < 1 mean-reverting, > 1 trending, ~1 random walk. Computed on
    NON-OVERLAPPING k-bar blocks (not a rolling window), which is the
    standard Lo-MacKinlay construction -- overlapping blocks understate
    the variance and bias the ratio toward 1 regardless of the true
    process.
    """
    n_blocks = len(returns) // k
    if n_blocks < 30:
        return float("nan")
    trimmed = returns[: n_blocks * k]
    k_bar_returns = trimmed.reshape(n_blocks, k).sum(axis=1)
    var_1 = np.var(returns, ddof=1)
    var_k = np.var(k_bar_returns, ddof=1)
    if var_1 <= 0:
        return float("nan")
    return float(var_k / (k * var_1))


def pull_symbol(symbol: str, client: HFMarketData) -> Path:
    out = PARTS_DIR / f"{symbol}_1Min_hf_splitdiv_rth_{START.date()}_{END.date()}.csv"
    if out.exists():
        logger.info(f"{symbol}: already pulled, skipping")
        return out

    spec = FetchSpec(
        symbol=symbol,
        start=START,
        end=END,
        timeframe="1Min",
        feed="hf",
        adjustment="splitdiv",
        regular_hours_only=True,
    )
    df, dropped_eh, dupes = client.fetch_bars(spec)
    validate(df)
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(df, out, force=True)
    logger.info(f"{symbol}: {len(df):,} bars, dropped_eh={dropped_eh} dupes={dupes}")
    return out


def characterize(symbol: str, csv_path: Path) -> dict:
    df = pd.read_csv(csv_path, parse_dates=["timestamp"], index_col="timestamp")
    close = df["close"].to_numpy()
    log_returns = np.diff(np.log(close))

    years = (df.index[-1] - df.index[0]).days / 365.25
    total_return = close[-1] / close[0] - 1.0
    cagr = (close[-1] / close[0]) ** (1.0 / years) - 1.0 if years > 0 else float("nan")

    running_peak = np.maximum.accumulate(close)
    drawdown = (running_peak - close) / running_peak
    max_dd = float(drawdown.max())

    annualization = np.sqrt(252 * 390)  # trading days x RTH minutes/day
    realized_vol = float(np.std(log_returns, ddof=1) * annualization)

    return {
        "symbol": symbol,
        "bars": len(df),
        "years": round(years, 2),
        "total_return_pct": round(total_return * 100, 1),
        "cagr_pct": round(cagr * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "annualized_vol_pct": round(realized_vol * 100, 1),
        "vr_30min": round(variance_ratio(log_returns, 30), 3),
        "vr_390min_1day": round(variance_ratio(log_returns, 390), 3),
        "vr_1950min_5day": round(variance_ratio(log_returns, 1950), 3),
    }


def main() -> None:
    client = HFMarketData(**CLIENT_KW)
    results = []
    for symbol in CANDIDATES:
        try:
            csv_path = pull_symbol(symbol, client)
            results.append(characterize(symbol, csv_path))
        except Exception as e:
            logger.error(f"{symbol}: FAILED {type(e).__name__}: {e}")

    if not results:
        logger.error("No candidates succeeded.")
        sys.exit(1)

    out = pd.DataFrame(results)
    out.to_csv("output/instrument_screen.csv", index=False)
    logger.info("\n" + out.to_string(index=False))
    logger.info(
        "\nVR < 1.0 = mean-reverting over that horizon (candidate for this strategy); "
        "VR > 1.0 = trending (works against a target-and-hold approach); "
        "VR ~= 1.0 = random walk. Compare each candidate's VR against SPXL's (the control) "
        "and against TQQQ's own known character, not against 1.0 in isolation -- "
        "3x leveraged ETFs all carry volatility-decay-driven mean reversion at SOME horizon."
    )
    logger.info("wrote output/instrument_screen.csv")


if __name__ == "__main__":
    main()
