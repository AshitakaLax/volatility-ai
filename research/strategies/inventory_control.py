"""
Inventory-aware quoting and sizing -- catalog C-G2, C-MM1, C-MM2, C-MM3
and C-S4 (docs/research/correction-strategies.md).

Never selling a lot at a loss turns losses into inventory, so inventory is
the quantity a correction strategy has to control (the catalog's rank 2).
These are the published rules for doing that, each pinned to its source:

  C-G2  inventory-skewed grid (hftbacktest, "High-Frequency Grid Trading
        -- Simplified from GLFT"):
            bid_depth = half_spread * (1 + skew * normalized_position)
            ask_depth = half_spread * (1 - skew * normalized_position)
        normalized_position is the position in order-size units -- here,
        open lots. For a long-only grid the bid side is the one that
        matters: each open lot pushes the next buy rung further down.

  C-MM1 Avellaneda & Stoikov, "High-frequency trading in a limit order
        book", Quantitative Finance 8(3), 2008:
            r(s, q, t)      = s - q * gamma * sigma^2 * (T - t)
            delta_a+delta_b = gamma * sigma^2 * (T - t)
                              + (2 / gamma) * ln(1 + gamma / k)
        quotes symmetric around r. Their simulation (s=100, T=1, sigma=2,
        k=1.5) reports average spreads of 1.49 / 1.35 / 3.02 for gamma =
        0.1 / 0.01 / 1; the tests reproduce all three.

  C-MM2 Gueant-Lehalle-Fernandez-Tapia closed form, as implemented in
        hftbacktest's "GLFT Market Making Model and Grid Trading" (Gueant,
        "Optimal market making", eqs. 4.6-4.7):
            c1 = 1 / (xi * delta) * ln(1 + xi * delta / k)
            c2 = sqrt(gamma / (2 * A * delta * k)
                      * (1 + xi * delta / k) ** (k / (xi * delta) + 1))
            half_spread = (c1 + delta / 2 * c2 * volatility) * adj1
            skew        = c2 * volatility * adj2
            reservation = mid - skew * position
        and the arrival intensity lambda(depth) = A * exp(-k * depth)
        calibrated by regressing log arrival rates on depth:
        k = -slope, A = exp(intercept).

  C-MM3 alpha-shifted quoting (hftbacktest README quick example):
            risk        = (c + volatility) * position
            half_spread = (c + volatility) * hs
            reservation = mid + a * forecast - b * risk

  C-S4  inventory-capped inverse-exposure sizing (the catalog's sizing
        form of G2, caps from riskkit): the lot shrinks geometrically with
        each open lot, and hard caps on open lots and on open exposure
        stop or trim new buys.

Pure functions: no state, no market data. The tick rounding and the
min/max against the best bid/ask in the hftbacktest code are left to a
caller that has a tick grid and a book; this project's minute bars have
neither.

None of these sells anything, so none can realize a loss: they move or
shrink BUYS only.
"""

from __future__ import annotations

import math

import numpy as np

from engine.core.exceptions import ConfigurationError

# --------------------------------------------------------------------------
# C-G2 -- inventory-skewed grid depths


def skewed_depths(
    half_spread: float, normalized_position: float, skew: float
) -> tuple[float, float]:
    """(bid_depth, ask_depth) exactly as the hftbacktest grid tutorial:
    half_spread * (1 +/- skew * normalized_position)."""
    if half_spread < 0:
        raise ConfigurationError(f"half_spread must be >= 0, got {half_spread}")
    if skew < 0:
        raise ConfigurationError(f"skew must be >= 0, got {skew}")
    return (
        half_spread * (1.0 + skew * normalized_position),
        half_spread * (1.0 - skew * normalized_position),
    )


def inventory_skewed_level(
    reference: float,
    step: float,
    open_lots: int,
    skew: float,
    max_depth: float | None = None,
) -> float:
    """The long-only grid's next buy level: the bid depth above, measured
    from `reference` as a fraction -- reference * (1 - step * (1 + skew *
    open_lots)). With no open lots it is the champion's own
    `reference * (1 - step)`. `max_depth` caps the fraction so a deep
    inventory cannot push the rung to zero."""
    if not 0 < step < 1:
        raise ConfigurationError(f"step must be in (0, 1), got {step}")
    if open_lots < 0:
        raise ConfigurationError(f"open_lots must be >= 0, got {open_lots}")
    if max_depth is not None and not step <= max_depth < 1:
        raise ConfigurationError(f"need step <= max_depth < 1, got {step}, {max_depth}")
    depth, _ = skewed_depths(step, open_lots, skew)
    if max_depth is not None:
        depth = min(depth, max_depth)
    return reference * (1.0 - depth)


# --------------------------------------------------------------------------
# C-MM1 -- Avellaneda & Stoikov (2008)


def _check_as(gamma: float, sigma: float, tau: float) -> None:
    if not gamma > 0:
        raise ConfigurationError(f"gamma must be > 0, got {gamma}")
    if sigma < 0:
        raise ConfigurationError(f"sigma must be >= 0, got {sigma}")
    if tau < 0:
        raise ConfigurationError(f"tau (T - t) must be >= 0, got {tau}")


def as_reservation_price(s: float, q: float, gamma: float, sigma: float, tau: float) -> float:
    """r = s - q * gamma * sigma^2 * (T - t). Long inventory (q > 0) lowers
    the price the agent is indifferent at, so it quotes lower on both
    sides."""
    _check_as(gamma, sigma, tau)
    return s - q * gamma * sigma**2 * tau


def as_optimal_spread(gamma: float, sigma: float, tau: float, k: float) -> float:
    """delta_a + delta_b = gamma * sigma^2 * (T - t) + (2/gamma) ln(1 + gamma/k)."""
    _check_as(gamma, sigma, tau)
    if not k > 0:
        raise ConfigurationError(f"k must be > 0, got {k}")
    return gamma * sigma**2 * tau + (2.0 / gamma) * math.log(1.0 + gamma / k)


def as_quotes(
    s: float, q: float, gamma: float, sigma: float, tau: float, k: float
) -> tuple[float, float]:
    """(bid, ask), symmetric around the reservation price."""
    r = as_reservation_price(s, q, gamma, sigma, tau)
    half = as_optimal_spread(gamma, sigma, tau, k) / 2.0
    return r - half, r + half


# --------------------------------------------------------------------------
# C-MM2 -- GLFT closed form (hftbacktest's implementation)


def glft_coefficients(
    xi: float, gamma: float, delta: float, A: float, k: float
) -> tuple[float, float]:
    """(c1, c2), transcribed from hftbacktest's compute_coeff."""
    for name, value in (("xi", xi), ("gamma", gamma), ("delta", delta), ("A", A), ("k", k)):
        if not value > 0:
            raise ConfigurationError(f"{name} must be > 0, got {value}")
    inv_k = 1.0 / k
    c1 = 1.0 / (xi * delta) * math.log(1.0 + xi * delta * inv_k)
    c2 = math.sqrt(
        gamma / (2.0 * A * delta * k) * ((1.0 + xi * delta * inv_k) ** (k / (xi * delta) + 1.0))
    )
    return c1, c2


def glft_quotes(
    mid: float,
    position: float,
    volatility: float,
    c1: float,
    c2: float,
    delta: float,
    adj1: float = 1.0,
    adj2: float = 1.0,
) -> dict[str, float]:
    """half_spread = (c1 + delta/2 * c2 * volatility) * adj1,
    skew = c2 * volatility * adj2, reservation = mid - skew * position,
    bid/ask = reservation -/+ half_spread (before tick rounding)."""
    if volatility < 0:
        raise ConfigurationError(f"volatility must be >= 0, got {volatility}")
    half_spread = (c1 + delta / 2.0 * c2 * volatility) * adj1
    skew = c2 * volatility * adj2
    reservation = mid - skew * position
    return {
        "half_spread": half_spread,
        "skew": skew,
        "reservation": reservation,
        "bid": reservation - half_spread,
        "ask": reservation + half_spread,
    }


def fit_arrival_intensity(depths, arrival_rates) -> tuple[float, float]:
    """(A, k) for lambda(depth) = A * exp(-k * depth): the source's
    least-squares line through (depth, ln rate), k = -slope,
    A = exp(intercept). Zero rates cannot be logged and are rejected."""
    x = np.asarray(depths, dtype=float)
    rates = np.asarray(arrival_rates, dtype=float)
    if x.shape != rates.shape or x.size < 2:
        raise ConfigurationError("need at least two (depth, rate) pairs of equal length")
    if np.any(rates <= 0):
        raise ConfigurationError("arrival rates must be > 0 to take their log")
    y = np.log(rates)
    w = x.size
    sx, sy, sx2, sxy = x.sum(), y.sum(), (x**2).sum(), (x * y).sum()
    denominator = w * sx2 - sx**2
    if denominator == 0:
        raise ConfigurationError("depths must not all be equal")
    slope = (w * sxy - sx * sy) / denominator
    intercept = (sy - slope * sx) / w
    return math.exp(intercept), -slope


# --------------------------------------------------------------------------
# C-MM3 -- alpha-shifted quoting (hftbacktest README)


def alpha_shifted_quotes(
    mid: float,
    forecast: float,
    position: float,
    volatility: float,
    a: float,
    b: float,
    c: float,
    hs: float,
) -> dict[str, float]:
    """risk = (c + volatility) * position; half_spread = (c + volatility)
    * hs; reservation = mid + a * forecast - b * risk. A negative forecast
    lowers the bid instead of switching quoting off."""
    if volatility < 0 or c < 0 or hs < 0:
        raise ConfigurationError("volatility, c and hs must be >= 0")
    risk = (c + volatility) * position
    half_spread = (c + volatility) * hs
    reservation = mid + a * forecast - b * risk
    return {
        "reservation": reservation,
        "half_spread": half_spread,
        "bid": reservation - half_spread,
        "ask": reservation + half_spread,
    }


# --------------------------------------------------------------------------
# C-S4 -- inventory-capped inverse-exposure sizing


def inventory_decay_multiplier(open_lots: int, decay: float) -> float:
    """decay ** open_lots: 1.0 with no inventory, smaller with each lot."""
    if open_lots < 0:
        raise ConfigurationError(f"open_lots must be >= 0, got {open_lots}")
    if not 0 < decay <= 1:
        raise ConfigurationError(f"decay must be in (0, 1], got {decay}")
    return decay**open_lots


def inventory_capped_lot(
    base_lot: float,
    open_lots: int,
    decay: float,
    exposure: float = 0.0,
    equity: float | None = None,
    max_lots: int | None = None,
    max_exposure: float | None = None,
) -> float:
    """The new lot's dollar value: base_lot * decay ** open_lots, then the
    hard caps -- zero at `max_lots` open lots, and trimmed so open exposure
    (market value of open lots) never exceeds `max_exposure` * equity."""
    if base_lot < 0:
        raise ConfigurationError(f"base_lot must be >= 0, got {base_lot}")
    if max_lots is not None and max_lots < 1:
        raise ConfigurationError(f"max_lots must be >= 1, got {max_lots}")
    lot = base_lot * inventory_decay_multiplier(open_lots, decay)
    if max_lots is not None and open_lots >= max_lots:
        return 0.0
    if max_exposure is not None:
        if not 0 < max_exposure <= 1:
            raise ConfigurationError(f"max_exposure must be in (0, 1], got {max_exposure}")
        if equity is None or equity <= 0:
            raise ConfigurationError("an exposure cap needs equity > 0")
        lot = min(lot, max(0.0, max_exposure * equity - exposure))
    return lot
