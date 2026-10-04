"""
Grid lifecycle rules from the correction-strategy catalog
(docs/research/correction-strategies.md): C-G4, C-G6 and C-X2.

C-G4  Dynamic grid reset -- Chen, Chen & Jang, "Dynamic Grid Trading
      Strategy: From Zero Expectation to Market Outperformance", 2025
      (arXiv 2506.11921). Their construction, verbatim: "Assume there are n
      grids, resulting in n+1 grid levels. Given that the grid intervals
      have equal ratios, let the grid size be k" -- levels P*(1+k)^j. "The
      strategy resets the grid whenever the price breaks above the upper
      limit or falls below the lower limit, with the current price
      becoming the new center." On an upside break the capital is
      recovered and reinvested; on a downside break "the strategy holds"
      its position. Holding on the way down is what keeps the reset
      compatible with the no-loss ledger -- but a downside reset then adds
      rungs below lots already held, which is averaging down; the catalog
      pairs it with C-G2/C-G3 and a regime exit.

C-G6  Grid ruin analysis -- Taranto & Khan (2020) model a grid as a walk
      between absorbing barriers; only their abstract was seen, so this is
      the classical result their framing rests on. A walk in rung units
      that steps up with probability p and down with q = 1 - p, starting
      `down` rungs above capital exhaustion and `up` rungs below the profit
      target, reaches the target first with probability
          (1 - (q/p)^down) / (1 - (q/p)^(down+up))   (p != q)
          down / (down + up)                          (p == q)
      and the expected number of steps before either barrier is
          down * up                                   (p == q)
          down/(q-p) - (down+up)/(q-p) * P_target     (p != q).

C-X2  Profit-only time-limit exit -- the catalog's admissible variant of
      a time exit: a lot older than `max_hold_bars` is exited only when the
      sale clears its cost basis. That decision is NOT made here: it is
      engine/trading/no_loss_guard.compute_sell_economics(...).permitted,
      the single place a sell is checked against cost, so no comparison is
      re-implemented.
"""

from __future__ import annotations

import math

from engine.core.exceptions import ConfigurationError
from engine.trading.no_loss_guard import compute_sell_economics

# ---------------------------------------------------------------- C-G4


def geometric_levels(center: float, n_grids: int, ratio: float) -> list[float]:
    """n + 1 levels center * (1 + ratio)^j for j in -n/2 .. n/2 (n even),
    ascending; the centre is the middle level."""
    if not center > 0:
        raise ConfigurationError(f"center must be > 0, got {center}")
    if not (isinstance(n_grids, int) and n_grids >= 2 and n_grids % 2 == 0):
        raise ConfigurationError(f"n_grids must be an even integer >= 2, got {n_grids!r}")
    if not ratio > 0:
        raise ConfigurationError(f"ratio must be > 0, got {ratio}")
    half = n_grids // 2
    return [center * (1.0 + ratio) ** j for j in range(-half, half + 1)]


class DynamicGrid:
    """A geometric grid that re-centres on the price when it breaks out."""

    def __init__(self, center: float, n_grids: int, ratio: float) -> None:
        self.n_grids = n_grids
        self.ratio = ratio
        self.levels = geometric_levels(center, n_grids, ratio)
        self.resets_up = 0
        self.resets_down = 0

    @property
    def center(self) -> float:
        return self.levels[self.n_grids // 2]

    def on_price(self, price: float) -> str | None:
        """'up' or 'down' when `price` breaks out and the grid is re-centred
        on it, else None. The caller applies the paper's position rule:
        recover and reinvest on 'up', hold on 'down'."""
        if price > self.levels[-1]:
            self.levels = geometric_levels(price, self.n_grids, self.ratio)
            self.resets_up += 1
            return "up"
        if price < self.levels[0]:
            self.levels = geometric_levels(price, self.n_grids, self.ratio)
            self.resets_down += 1
            return "down"
        return None


# ---------------------------------------------------------------- C-G6


def _check_walk(down: int, up: int, p_up: float) -> None:
    for name, value in (("down", down), ("up", up)):
        if not (isinstance(value, int) and value >= 1):
            raise ConfigurationError(f"{name} must be an integer >= 1, got {value!r}")
    if not 0 < p_up < 1:
        raise ConfigurationError(f"p_up must be in (0, 1), got {p_up}")


def target_first_probability(down: int, up: int, p_up: float = 0.5) -> float:
    """Probability of reaching the profit target before capital exhaustion."""
    _check_walk(down, up, p_up)
    q = 1.0 - p_up
    if math.isclose(p_up, q):
        return down / (down + up)
    r = q / p_up
    return (1.0 - r**down) / (1.0 - r ** (down + up))


def ruin_probability(down: int, up: int, p_up: float = 0.5) -> float:
    """1 - target_first_probability: capital runs out first."""
    return 1.0 - target_first_probability(down, up, p_up)


def expected_steps(down: int, up: int, p_up: float = 0.5) -> float:
    """Expected number of rung moves before either barrier."""
    _check_walk(down, up, p_up)
    q = 1.0 - p_up
    if math.isclose(p_up, q):
        return float(down * up)
    return down / (q - p_up) - (down + up) / (q - p_up) * target_first_probability(down, up, p_up)


def rungs_for_decline(decline: float, step: float) -> int:
    """Buy rungs a fall of `decline` crosses on a grid of relative `step`
    (each rung is (1 - step) of the one above): the smallest m with
    (1 - step)^m <= 1 - decline."""
    if not 0 < decline < 1 or not 0 < step < 1:
        raise ConfigurationError("decline and step must both be in (0, 1)")
    return math.ceil(math.log(1.0 - decline) / math.log(1.0 - step) - 1e-12)


# ---------------------------------------------------------------- C-X2


def profit_only_time_exits(lots, now_bar: int, price: float, max_hold_bars: int, cost_model):
    """Lots that have been held at least `max_hold_bars` AND whose sale at
    `price` the no-loss guard permits. `lots` is an iterable of
    (lot, entry_bar) pairs; each lot needs `buy_price` and `quantity`, as
    the ledger's lots do. Losing lots are never returned, however old."""
    if not (isinstance(max_hold_bars, int) and max_hold_bars >= 1):
        raise ConfigurationError(f"max_hold_bars must be an integer >= 1, got {max_hold_bars!r}")
    eligible = []
    for lot, entry_bar in lots:
        if now_bar - entry_bar < max_hold_bars:
            continue
        economics = compute_sell_economics(lot, lot.quantity, price, cost_model)
        if economics.permitted:
            eligible.append(lot)
    return eligible


# ---------------------------------------------------------------- M6 as an exit


def psar_profit_exits(
    lots, daily, price: float, cost_model, step: float = 0.02, max_step: float = 0.2
):
    """Catalog M6's use of the Parabolic SAR: a PROFIT-ONLY trailing exit.
    When the latest completed session's SAR has turned to its falling phase
    (price broke the rising stop), lots whose sale at `price` the no-loss
    guard permits are returned; losing lots never are -- a SAR is never a
    loss stop here. The SAR is trend_regimes.parabolic_sar (Wilder), the
    same implementation the psar regime uses. `lots` yields objects with
    `buy_price` and `quantity`."""
    from research.strategies.trend_regimes import parabolic_sar

    _, rising = parabolic_sar(daily, step, max_step)
    if len(rising) < 2 or rising[-1]:
        return []
    return [
        lot
        for lot in lots
        if compute_sell_economics(lot, lot.quantity, price, cost_model).permitted
    ]
