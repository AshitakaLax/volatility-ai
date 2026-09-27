"""
A historically-real proxy for money-market yield (SPAXX-like), as an
as-of-joinable signal for ExecutionConfig.cash_yield_pct's "smart"
default -- see optimization_controller.py's _smart_cash_yield_series /
_smart_cash_yield_pct for how a bar actually consumes this.

--------------------------------------------------------------------
WHY A PROXY, NOT SPAXX'S OWN PUBLISHED NUMBER

SPAXX's NAV is pinned to $1.00 and it publishes no price series a
normal market-data feed carries -- there is no ticker history to pull
the way there is for an ETF, and its historical 7-day SEC yield is not
available as a clean, freely fetchable time series anywhere this
project's other sources come from (FRED, CBOE, Yahoo).

What SPAXX DOES do, mechanically, is earn very close to the overnight
rate the Fed sets -- it holds short Treasuries and repo backed by
them -- minus its own expense ratio. The Effective Federal Funds Rate
(EFFR) is exactly that overnight rate, and it is already in this
project's FRED registry (research/ml/sources.py), fetched the same way
as every other macro input:

    python tools/fetch_market_inputs.py --provider fred --category rates

Published daily back to 2000-07-04 with no API key -- long enough to
cover every backtest window this project runs (TQQQ itself starts
2010). Absent entirely on a checkout that never ran that command (a
Pi, a shard, a fresh clone) -- see the FLOOR fallback below, the same
"optional, exact no-op when missing" shape as
engine/data/implied_vol_signal.py's implied_vol_path.

--------------------------------------------------------------------
THE HAIRCUT AND THE FLOOR

SPAXX_EXPENSE_RATIO_PCT (0.42, per its prospectus dated 2026-06-26) is
subtracted from EFFR to approximate what a holder is actually credited,
not what the fund's underlying repo/Treasury book gross-yields.
Calibration check, both read the same day this was written: EFFR was
3.88% on 2026-09-24 (this project's own fetch); SPAXX's own published
7-day yield was ~3.32-3.33% in August 2026 -- before the 2026-09 rate
hike this proxy already reflects and that August figure could not have.
The ~0.3pp of the gap the expense ratio alone doesn't explain is that
timing mismatch, not evidence the haircut is wrong.

FLOOR_PCT (0.01, i.e. 0.01%) is the smart MINIMUM this module's name
promises: real money-market funds do not report a negative yield.
Fidelity waived fees to hold SPAXX near this exact floor through the
2009-2015 and 2020-2021 near-zero-rate stretches rather than pass a
negative number to holders, and EFFR-minus-the-expense-ratio goes
negative for exactly those stretches without one. Applied everywhere
the computed value would fall below it -- not only where the series
has no data at all -- which is what makes this "smart" rather than a
second fixed constant: every OTHER point in time still reads the real,
historically-accurate rate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.data.external_index_series import ExternalIndexSeries

SPAXX_EXPENSE_RATIO_PCT = 0.42
FLOOR_PCT = 0.01


def load_money_market_yield_history(path) -> ExternalIndexSeries:
    """Read a FRED EFFR-shaped CSV (timestamp,close, in percentage
    points, e.g. 3.88 for 3.88%) and return the joinable series.

    The expense-ratio haircut and floor are applied at the point of use
    (smart_cash_yield_pct_for_index below), not here, so this stays a
    plain, honest read of the source -- exactly the split
    engine/data/implied_vol_signal.py's load_implied_vol_change /
    changes_for_index already establishes.
    """
    return ExternalIndexSeries.from_csv(path)


def smart_cash_yield_pct_for_index(
    series: ExternalIndexSeries | None, index: pd.DatetimeIndex
) -> np.ndarray:
    """Per-bar SPAXX-proxy annual yield, in PERCENTAGE POINTS (3.3 means
    3.3%, matching EFFR's own units) -- divide by 100 at the point this
    feeds BacktestState.accrue_daily_interest, which wants a fraction.

    FLOOR_PCT where no rate is known at all: series is None (the file
    was never fetched -- a Pi or shard checkout with no data/external/,
    or a fresh clone) or the queried date is before EFFR's own history
    (2000-07-04). A date AFTER the series' last observation instead
    reuses the last known rate -- ExternalIndexSeries.vectorized's own
    as-of semantics -- which is the right behaviour for a data/external/
    snapshot that is merely a few weeks stale rather than absent.
    """
    if series is None:
        return np.full(len(index), FLOOR_PCT, dtype=float)
    net = series.vectorized(index) - SPAXX_EXPENSE_RATIO_PCT
    return np.maximum(np.nan_to_num(net, nan=FLOOR_PCT), FLOOR_PCT)
