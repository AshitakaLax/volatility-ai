"""
CBOE VIX methodology from an option chain (je-suis-tm/quant-trading
#15) -- a DATA tool, not a strategy.

Why it is here: volatility-ai's implied-vol lever wants VXN (Nasdaq-100
volatility) and could not source it, so it uses VIXY as a proxy. With
Nasdaq-100 (NDX) or QQQ option quotes, this computes the VIX-style
30-day model-free implied volatility directly.

  sigma^2 = (2/T) sum_i (dK_i / K_i^2) e^{rT} Q(K_i)  -  (1/T) (F/K0 - 1)^2

  F   forward from put-call parity at the strike where |call - put| is
      smallest:  F = K + e^{rT} (call - put)
  K0  the first strike at or below F
  Q   out-of-the-money mid quotes: puts below K0, calls above, the
      average of both at K0; each side stops after two consecutive
      zero bids, per the CBOE white paper
  dK  half the distance between the neighbouring strikes (one-sided at
      the ends)

Two expiries bracketing 30 days are interpolated to a constant 30-day
horizon and annualised: VIX = 100 sqrt(variance x 365/30). Times are in
calendar days here (CBOE uses minutes; the difference is a rounding of
the interpolation weights).

The chain is a DataFrame with columns strike, call_bid, call_ask,
put_bid, put_ask. Ingesting quotes is out of scope here.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

COLUMNS = ("strike", "call_bid", "call_ask", "put_bid", "put_ask")


def _otm_side(strikes, bids, mids, start: int, direction: int) -> list[tuple[float, float]]:
    out, zeros, i = [], 0, start
    while 0 <= i < len(strikes):
        if bids[i] <= 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            out.append((strikes[i], mids[i]))
        i += direction
    return out


def expiry_variance(chain: pd.DataFrame, t_years: float, rate: float) -> float:
    """Model-free implied variance for one expiry (annualised)."""
    missing = set(COLUMNS) - set(chain.columns)
    if missing:
        raise ConfigurationError(f"chain is missing {sorted(missing)}")
    if t_years <= 0:
        raise ConfigurationError(f"time to expiry must be positive, got {t_years}")
    c = chain.sort_values("strike").reset_index(drop=True)
    k = c["strike"].to_numpy(float)
    call_mid = ((c["call_bid"] + c["call_ask"]) / 2).to_numpy(float)
    put_mid = ((c["put_bid"] + c["put_ask"]) / 2).to_numpy(float)
    both = (c["call_bid"] > 0) & (c["put_bid"] > 0)
    if not both.any():
        raise ConfigurationError("no strike has both a call and a put bid")
    diff = np.where(both, np.abs(call_mid - put_mid), np.inf)
    atm = int(np.argmin(diff))
    growth = math.exp(rate * t_years)
    forward = k[atm] + growth * (call_mid[atm] - put_mid[atm])
    k0_idx = int(np.searchsorted(k, forward, side="right") - 1)
    if k0_idx < 0:
        raise ConfigurationError("no strike at or below the forward")
    k0 = k[k0_idx]
    puts = _otm_side(k, c["put_bid"].to_numpy(float), put_mid, k0_idx - 1, -1)
    calls = _otm_side(k, c["call_bid"].to_numpy(float), call_mid, k0_idx + 1, +1)
    points = sorted([*puts, (k0, (call_mid[k0_idx] + put_mid[k0_idx]) / 2), *calls])
    ks = np.array([p[0] for p in points])
    qs = np.array([p[1] for p in points])
    dk = np.empty_like(ks)
    dk[1:-1] = (ks[2:] - ks[:-2]) / 2
    dk[0] = ks[1] - ks[0]
    dk[-1] = ks[-1] - ks[-2]
    total = float(np.sum(dk / ks**2 * growth * qs))
    return (2.0 / t_years) * total - (1.0 / t_years) * (forward / k0 - 1.0) ** 2


def vix(
    near: pd.DataFrame,
    near_days: float,
    next_: pd.DataFrame,
    next_days: float,
    rate: float,
    target_days: float = 30.0,
) -> float:
    """30-day constant-maturity index from two expiries bracketing it."""
    if not near_days < target_days <= next_days:
        raise ConfigurationError(
            f"expiries must bracket {target_days} days, got {near_days} and {next_days}"
        )
    t1, t2 = near_days / 365.0, next_days / 365.0
    v1 = expiry_variance(near, t1, rate)
    v2 = expiry_variance(next_, t2, rate)
    w1 = (next_days - target_days) / (next_days - near_days)
    w2 = (target_days - near_days) / (next_days - near_days)
    blended = (t1 * v1 * w1 + t2 * v2 * w2) * 365.0 / target_days
    return 100.0 * math.sqrt(max(blended, 0.0))


__all__ = ["COLUMNS", "expiry_variance", "vix"]
