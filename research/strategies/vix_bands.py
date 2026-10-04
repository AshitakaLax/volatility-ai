"""
VIX-level bands -- the unbuilt part of catalog R4
(docs/research/correction-strategies.md): "the VIX at the open is used as
data only (volatility ETFs remain excluded) ... VIX bands (for example below
20, 20-30, above 30)". The realized-volatility and ATR half of R4 already
exists (N5's NATR regime, V7/S4's volatility sizing); the level gate did
not, because the VIX was never ingested -- fred_VIXCLS and CBOE's VIX now
sit in data/external/ after the ML input fetch.

  vix_band          0 below the first edge, 1 between, 2 at or above the
                    last (edges ascending; any number of them)
  bands_by_session  the band of each session's VIX CLOSE applied to the
                    NEXT session (lag 1), the same causal rule as every
                    other regime here; lag 0 exists only to measure the
                    difference.

M1's finding is what makes a high band interesting: intraday-momentum
Sharpe rose with the opening VIX, so a high band tilts the platform from
grid buying toward momentum gating. What to DO in each band is a decision
for whoever wires this in; this module only classifies.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

DEFAULT_EDGES: tuple[float, ...] = (20.0, 30.0)


def _check_edges(edges) -> tuple[float, ...]:
    edges = tuple(float(e) for e in edges)
    if not edges or any(b <= a for a, b in pairwise(edges)):
        raise ConfigurationError(f"edges must be strictly ascending, got {edges}")
    return edges


def vix_band(level: float, edges=DEFAULT_EDGES) -> int:
    """Band index of one VIX level."""
    edges = _check_edges(edges)
    if not np.isfinite(level):
        raise ConfigurationError(f"VIX level must be finite, got {level}")
    return int(np.searchsorted(edges, level, side="right"))


def bands_by_session(vix_close: pd.Series, edges=DEFAULT_EDGES, lag: int = 1) -> dict[date, int]:
    """{session: band} keyed by the session the band APPLIES to."""
    edges = _check_edges(edges)
    if lag not in (0, 1):
        raise ConfigurationError(f"lag must be 0 or 1, got {lag}")
    clean = vix_close.dropna()
    bands = np.searchsorted(edges, clean.to_numpy(dtype=float), side="right")
    days = [ts.date() for ts in clean.index]
    if lag == 0:
        return dict(zip(days, (int(b) for b in bands), strict=True))
    return {days[i + 1]: int(bands[i]) for i in range(len(days) - 1)}
