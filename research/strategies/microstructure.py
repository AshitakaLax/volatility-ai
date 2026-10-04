"""
Microstructure measures from the correction-strategy catalog
(docs/research/correction-strategies.md): C-MS1, C-MS2, C-MS5, C-MS6,
C-MS7, C-MM4 and C-MM5. Pure functions and one small estimator; no data
feed. Several need L1/L2 quotes or trades this project's minute bars do
not carry -- they are built and pinned so they are ready if that data is
added, and each docstring says what it needs.

C-MS1 order-flow imbalance -- Cont, Kukanov & Stoikov, "The Price Impact of
      Order Book Events", J. Financial Econometrics 12(1), 2014 (as quoted by
      twowaymind/orderflow-metrics):
        e_n = q_bid_n * 1{P_bid_n >= P_bid_n-1} - q_bid_n-1 * 1{P_bid_n <= P_bid_n-1}
            - q_ask_n * 1{P_ask_n <= P_ask_n-1} + q_ask_n-1 * 1{P_ask_n >= P_ask_n-1}
      OFI over an interval is the sum of e_n. Needs L1 quote updates.

C-MS2 micro-price and depth imbalance (hftbacktest's "Market Making with
      Alpha -- Order Book Imbalance"):
        micro_price = (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
        imbalance   = (bid_depth - ask_depth) / (bid_depth + ask_depth)
      standardised over a rolling window. Needs L1 sizes / L2 depth.

C-MS5 bar-only proxies (orderflow-metrics implements these by name):
        roll_spread    Roll (1984): 2 * sqrt(-cov(dP_t, dP_t-1)), 0 if cov >= 0
        corwin_schultz Corwin & Schultz (2012) two-day high-low estimator
        abdi_ranaldo   Abdi & Ranaldo (2017): 2 * sqrt(E[(c_t - eta_t)(c_t - eta_t+1)]),
                       c = ln close, eta = (ln H + ln L) / 2
        amihud         mean of |return| / volume
        kyle_lambda    OLS slope of price change on signed volume
        bvc_buy_fraction  Phi(dP / sigma)  (bulk volume classification)

C-MS6 leveraged-ETF rebalancing demand -- Cheng & Madhavan, "The Dynamics
      of Leveraged and Inverse ETFs", 2009: a daily-reset fund of leverage L
      and assets A must trade A_{t-1} * (L^2 - L) * r_t at the close, in
      the direction of the day's move for both leveraged (L > 1) and
      inverse (L < 0) funds. Ivanov & Lenkey (2018) find fund flows offset
      most of it; it is a hypothesis input, not a signal.

C-MS7 volume profile -- letianzj/QuantResearch market/market_profile.ipynb:
      fixed-width price buckets from floor(min close / pace) * pace,
      closes histogrammed with volume weights, bucket midpoints as prices;
      the TPO profile marks every bucket a period's [low, high] spans. The
      notebook stops there. The point of control (highest-volume bucket)
      and the value area (the standard 70% rule: grow from the POC one row
      at a time toward the larger neighbour) are standard practice, not
      from the notebook.

C-MM4 VPIN -- Easley, Lopez de Prado & O'Hara, "Flow Toxicity and
      Liquidity in a High Frequency World", RFS 25(5), 2012: bars are
      poured into equal-volume buckets, each bucket's volume split buy/sell
      by bulk classification, and
        VPIN = sum over the last n buckets of |V_sell - V_buy| / (n * V)
      Andersen & Bondarenko find this bar-level version adds little beyond
      volume and volatility -- recorded in the catalog.

C-MM5 queue-position estimate -- Rigtorp, "Estimating Order Queue
      Position" (2013), the model hftbacktest's probability queue models
      follow:
        p = f(V) / (f(V) + f(max(Q - S - V, 0)))
        a trade:         V <- max(V + dQ, 0)
        a cancellation:  V <- max(V + p * dQ, 0)
      V = quantity ahead of our order, Q = level size, S = our size, f an
      increasing function with f(0) = 0 (identity, ln(1 + x), or x^n).
      Additions join behind us and leave V alone. Needs L2 data.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

_Z = NormalDist()

# ---------------------------------------------------------------- C-MS1


def ofi_events(bid_px, bid_sz, ask_px, ask_sz) -> np.ndarray:
    """e_n for n = 1..N-1 (one per update after the first)."""
    bp, bq, ap, aq = (np.asarray(x, dtype=float) for x in (bid_px, bid_sz, ask_px, ask_sz))
    if not bp.size == bq.size == ap.size == aq.size or bp.size < 2:
        raise ConfigurationError("need four equal-length quote series of at least two updates")
    return (
        bq[1:] * (bp[1:] >= bp[:-1])
        - bq[:-1] * (bp[1:] <= bp[:-1])
        - aq[1:] * (ap[1:] <= ap[:-1])
        + aq[:-1] * (ap[1:] >= ap[:-1])
    )


def ofi(bid_px, bid_sz, ask_px, ask_sz) -> float:
    return float(ofi_events(bid_px, bid_sz, ask_px, ask_sz).sum())


# ---------------------------------------------------------------- C-MS2


def micro_price(bid: float, ask: float, bid_qty: float, ask_qty: float) -> float:
    total = bid_qty + ask_qty
    if total <= 0:
        raise ConfigurationError("need a positive total size")
    return (bid * ask_qty + ask * bid_qty) / total


def depth_imbalance(bid_depth: float, ask_depth: float) -> float:
    total = bid_depth + ask_depth
    if total <= 0:
        raise ConfigurationError("need positive total depth")
    return (bid_depth - ask_depth) / total


def standardized(series: pd.Series, window: int) -> pd.Series:
    """(x - rolling mean) / rolling std over `window` -- the tutorial's
    standardisation of the imbalance."""
    mean = series.rolling(window, min_periods=window).mean()
    std = series.rolling(window, min_periods=window).std(ddof=0)
    return (series - mean) / std


# ---------------------------------------------------------------- C-MS5


def roll_spread(prices) -> float:
    dp = np.diff(np.asarray(prices, dtype=float))
    if dp.size < 3:
        raise ConfigurationError("need at least four prices")
    cov = float(np.cov(dp[1:], dp[:-1], ddof=1)[0, 1])
    return 2.0 * math.sqrt(-cov) if cov < 0 else 0.0


def corwin_schultz(highs, lows) -> np.ndarray:
    """One estimate per pair of consecutive bars; negatives set to zero."""
    h, lo = (np.asarray(x, dtype=float) for x in (highs, lows))
    if h.size != lo.size or h.size < 2 or np.any(lo <= 0) or np.any(h < lo):
        raise ConfigurationError("need matching positive highs >= lows, at least two bars")
    beta = np.log(h[1:] / lo[1:]) ** 2 + np.log(h[:-1] / lo[:-1]) ** 2
    gamma = np.log(np.maximum(h[1:], h[:-1]) / np.minimum(lo[1:], lo[:-1])) ** 2
    k = 3.0 - 2.0 * math.sqrt(2.0)
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    spread = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    return np.maximum(spread, 0.0)


def abdi_ranaldo(highs, lows, closes) -> float:
    h, lo, c = (np.log(np.asarray(x, dtype=float)) for x in (highs, lows, closes))
    if not h.size == lo.size == c.size or h.size < 3:
        raise ConfigurationError("need equal-length series of at least three bars")
    eta = (h + lo) / 2.0
    product = float(np.mean((c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])))
    return 2.0 * math.sqrt(product) if product > 0 else 0.0


def amihud_illiquidity(returns, volumes) -> float:
    r, v = (np.asarray(x, dtype=float) for x in (returns, volumes))
    mask = v > 0
    if r.size != v.size or not mask.any():
        raise ConfigurationError("need matching returns and some positive volume")
    return float(np.mean(np.abs(r[mask]) / v[mask]))


def kyle_lambda(price_changes, signed_volumes) -> float:
    y, x = (np.asarray(a, dtype=float) for a in (price_changes, signed_volumes))
    if y.size != x.size or y.size < 3 or np.ptp(x) == 0:
        raise ConfigurationError("need matching series with varying signed volume")
    design = np.column_stack([np.ones(x.size), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(beta[1])


def bvc_buy_fraction(price_change: float, sigma: float) -> float:
    """Phi(dP / sigma); 0.5 when sigma is zero."""
    if sigma < 0:
        raise ConfigurationError(f"sigma must be >= 0, got {sigma}")
    return 0.5 if sigma == 0 else _Z.cdf(price_change / sigma)


# ---------------------------------------------------------------- C-MS6


def letf_rebalance_demand(assets: float, leverage: float, daily_return: float) -> float:
    """A * (L^2 - L) * r: dollars the fund must trade at the close (positive
    = buy). Zero for an unleveraged fund (L = 1)."""
    return assets * (leverage**2 - leverage) * daily_return


# ---------------------------------------------------------------- C-MS7


def price_buckets(closes, pace: float) -> np.ndarray:
    """The notebook's bucket edges."""
    if not pace > 0:
        raise ConfigurationError(f"pace must be > 0, got {pace}")
    c = np.asarray(closes, dtype=float)
    cmin_int = int(c.min() / pace) * pace
    cmax_int = int(c.max() / pace) * pace
    if cmax_int < c.max():
        cmax_int += pace
    cmax_int += pace
    return np.arange(cmin_int, cmax_int, pace)


def volume_profile(closes, volumes, pace: float) -> pd.Series:
    """Volume per bucket, indexed by bucket midpoint (the notebook's
    price_coors and vol_bars)."""
    edges = price_buckets(closes, pace)
    vol, _ = np.histogram(
        np.asarray(closes, dtype=float), bins=edges, weights=np.asarray(volumes, dtype=float)
    )
    mids = pd.Series(edges).rolling(2).mean().dropna().to_numpy()
    return pd.Series(vol, index=mids)


def tpo_profile(highs, lows, edges) -> np.ndarray:
    """Periods touching each bucket: a period marks every bucket from its
    low's to its high's, as the notebook fills between the two."""
    counts = np.zeros(len(edges) - 1, dtype=int)
    for hi, lo in zip(highs, lows, strict=True):
        marks, _ = np.histogram([lo, hi], bins=edges)
        idx = np.where(marks > 0)[0]
        if idx.size:
            counts[idx[0] : idx[-1] + 1] += 1
    return counts


def point_of_control(profile: pd.Series) -> float:
    return float(profile.idxmax())


def value_area(profile: pd.Series, share: float = 0.70) -> tuple[float, float]:
    """(low, high) bucket midpoints of the value area: start at the POC and
    add the larger adjacent bucket until `share` of volume is covered."""
    if not 0 < share <= 1:
        raise ConfigurationError(f"share must be in (0, 1], got {share}")
    v = profile.to_numpy(dtype=float)
    total = v.sum()
    if total <= 0:
        raise ConfigurationError("profile has no volume")
    lo = hi = int(np.argmax(v))
    covered = v[lo]
    while covered < share * total - 1e-12:
        below = v[lo - 1] if lo > 0 else -1.0
        above = v[hi + 1] if hi < v.size - 1 else -1.0
        if above >= below:
            hi += 1
            covered += v[hi]
        else:
            lo -= 1
            covered += v[lo]
    return float(profile.index[lo]), float(profile.index[hi])


# ---------------------------------------------------------------- C-MM4


def volume_buckets(price_changes, volumes, bucket_volume: float) -> list[list[tuple[float, float]]]:
    """Pour bars into buckets of exactly `bucket_volume`, splitting a bar
    across buckets; each bucket is a list of (price_change, volume) pieces.
    The final, partial bucket is dropped."""
    if not bucket_volume > 0:
        raise ConfigurationError(f"bucket_volume must be > 0, got {bucket_volume}")
    buckets, current, room = [], [], bucket_volume
    for dp, vol in zip(price_changes, volumes, strict=True):
        vol = float(vol)
        while vol > 1e-12:
            take = min(vol, room)
            current.append((float(dp), take))
            vol -= take
            room -= take
            if room <= 1e-12:
                buckets.append(current)
                current, room = [], bucket_volume
    return buckets


def vpin(
    price_changes, volumes, bucket_volume: float, n_buckets: int = 50, sigma: float | None = None
) -> float | None:
    """VPIN over the last `n_buckets` full buckets (None if fewer). sigma
    defaults to the stdev of the bar price changes."""
    dp = np.asarray(price_changes, dtype=float)
    if sigma is None:
        sigma = float(np.std(dp, ddof=1)) if dp.size > 1 else 0.0
    buckets = volume_buckets(dp, volumes, bucket_volume)
    if len(buckets) < n_buckets:
        return None
    imbalance = 0.0
    for bucket in buckets[-n_buckets:]:
        buy = sum(v * bvc_buy_fraction(d, sigma) for d, v in bucket)
        imbalance += abs((bucket_volume - buy) - buy)
    return imbalance / (n_buckets * bucket_volume)


# ---------------------------------------------------------------- C-MM5

PROB_FUNCTIONS = {
    "identity": lambda x: x,
    "log": lambda x: math.log1p(x),
}


class QueuePositionEstimator:
    """Rigtorp's queue-position estimate for one resting order."""

    def __init__(
        self,
        order_size: float,
        queue_ahead: float,
        level_size: float,
        prob: str = "identity",
        power: float | None = None,
    ) -> None:
        if not order_size > 0 or queue_ahead < 0 or level_size < queue_ahead + order_size:
            raise ConfigurationError(
                "need order_size > 0 and level_size >= queue_ahead + order_size"
            )
        if power is not None:
            if not power > 0:
                raise ConfigurationError(f"power must be > 0, got {power}")
            self._f = lambda x, n=power: x**n
        elif prob in PROB_FUNCTIONS:
            self._f = PROB_FUNCTIONS[prob]
        else:
            raise ConfigurationError(f"prob must be one of {tuple(PROB_FUNCTIONS)}, got {prob!r}")
        self.order_size = float(order_size)
        self.ahead = float(queue_ahead)
        self.level = float(level_size)
        self.filled = 0.0

    def probability(self) -> float:
        """p = f(V) / (f(V) + f(max(Q - S - V, 0))); 0 at the head, 1 at the tail."""
        behind = max(self.level - self.order_size - self.ahead, 0.0)
        front, back = self._f(self.ahead), self._f(behind)
        return 0.0 if front + back == 0 else front / (front + back)

    def on_trade(self, quantity: float) -> float:
        """A trade of `quantity` at our level: it consumes the queue ahead
        first. Returns how much of our order it filled."""
        if quantity < 0:
            raise ConfigurationError("trade quantity must be >= 0")
        through = max(quantity - self.ahead, 0.0)
        fill = min(through, self.order_size - self.filled)
        self.ahead = max(self.ahead - quantity, 0.0)
        self.filled += fill
        self.level = max(self.level - quantity, 0.0)
        return fill

    def on_level_change(self, new_level_size: float) -> None:
        """A change in level size not explained by trades: a decrease is a
        cancellation, ahead of us with probability p; an increase joins
        behind and leaves V alone."""
        delta = new_level_size - self.level
        if delta < 0:
            self.ahead = max(self.ahead + self.probability() * delta, 0.0)
        self.level = max(new_level_size, self.ahead + self.order_size - self.filled)
