"""
Position-sizing rules from the correction-strategy catalog
(docs/research/correction-strategies.md): C-S2, C-G5, and the drawdown
ladder behind R5/S3 (the tiers V11's linear throttle does not have).

C-S2  Kelly and fractional Kelly. deltaray-io/kelly-criterion's README:
      for independent strategies f_i = m_i / s_i^2 (mean excess return over
      variance), from Ernie Chan's *Quantitative Trading*, whose portfolio
      form is F* = C^-1 M with compounded growth g = r + F*' C F* / 2. Long-
      only means negative leverages are clipped to zero; fractional Kelly
      (1/2 or less) trades growth for much lower drawdown. The catalog uses
      it as a CEILING on total sleeve exposure, not as a per-lot size.

C-G5  Turtle units and pyramiding, from letianzj/QuantResearch
      backtest/turtle.py:
        ATR   = mean of the 14 true ranges over the 15 bars before now
        unit  = int(equity * 0.01 / ATR) shares
        enter when price > the Donchian high and no units are held
        add one unit when price > last buy price + 0.5 * ATR, while the
        buy count is 1..3 (so at most four units)
      The source's true range pairs each bar's high and low with the NEXT
      bar's close (`Close.shift(-1)`), not the textbook previous close;
      `true_range="source"` reproduces that and `"wilder"` gives the
      textbook max(H - L, |H - C_prev|, |L - C_prev|). Its exits (Donchian
      low, entry - 2 ATR) are price stops and out of scope here; the catalog
      uses the scale-in only, to rebuild inventory after a regime exit.

R5/S3 drawdown ladder (riskkit's tiers, as the catalog records them):
      new lots shrink in steps as drawdown deepens and stop entirely at the
      last tier; optionally a drawdown past `liquidate_at` raises a regime-
      exit request (to be carried out through lots_to_liquidate +
      allow_signal_exit, the only loss-realizing path). Halted buying
      resumes only once drawdown is back under `resume_below`.
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- C-S2


def kelly_leverage(mean_excess: float, variance: float) -> float:
    """f = m / s^2 for one strategy."""
    if not variance > 0:
        raise ConfigurationError(f"variance must be > 0, got {variance}")
    return mean_excess / variance


def kelly_portfolio(mean_excess, covariance, fraction: float = 1.0, long_only: bool = True):
    """F = fraction * C^-1 M, with negative entries clipped when long_only."""
    m = np.asarray(mean_excess, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if c.shape != (m.size, m.size):
        raise ConfigurationError("covariance must be square and match the means")
    if not 0 < fraction <= 1:
        raise ConfigurationError(f"fraction must be in (0, 1], got {fraction}")
    f = fraction * np.linalg.solve(c, m)
    return np.clip(f, 0.0, None) if long_only else f


def kelly_growth_rate(risk_free: float, leverages, covariance) -> float:
    """g = r + F' C F / 2 (Chan): the compounded growth at the optimum."""
    f = np.asarray(leverages, dtype=float)
    return float(risk_free + f @ np.asarray(covariance, dtype=float) @ f / 2.0)


# ---------------------------------------------------------------- C-G5


def true_ranges(highs, lows, closes, mode: str = "source") -> np.ndarray:
    """One true range per bar but the last (mode='source': H_i, L_i against
    C_{i+1}) or per bar but the first (mode='wilder': against C_{i-1})."""
    h, lo, c = (np.asarray(x, dtype=float) for x in (highs, lows, closes))
    if not h.size == lo.size == c.size or h.size < 2:
        raise ConfigurationError("need equal-length series of at least two bars")
    if mode == "source":
        return np.maximum.reduce(
            [h[:-1] - lo[:-1], np.abs(c[1:] - h[:-1]), np.abs(c[1:] - lo[:-1])]
        )
    if mode == "wilder":
        return np.maximum.reduce([h[1:] - lo[1:], np.abs(h[1:] - c[:-1]), np.abs(lo[1:] - c[:-1])])
    raise ConfigurationError(f"mode must be 'source' or 'wilder', got {mode!r}")


def turtle_atr(highs, lows, closes, mode: str = "source") -> float:
    """The source's ATR: the plain mean of the true ranges of the last 15
    completed bars (14 values)."""
    h, lo, c = (np.asarray(x, dtype=float)[-15:] for x in (highs, lows, closes))
    if h.size < 15:
        raise ConfigurationError("need at least 15 completed bars")
    return float(np.mean(true_ranges(h, lo, c, mode)))


def turtle_unit_shares(equity: float, atr: float, risk_pct: float = 0.01) -> int:
    """int(equity * risk_pct / ATR)."""
    if not atr > 0:
        raise ConfigurationError(f"atr must be > 0, got {atr}")
    if not 0 < risk_pct <= 1:
        raise ConfigurationError(f"risk_pct must be in (0, 1], got {risk_pct}")
    return int(equity * risk_pct / atr)


class TurtlePyramid:
    """Entry and add decisions; `on_price` returns 'enter', 'add' or None."""

    def __init__(self, add_step_atr: float = 0.5, max_buys: int = 4) -> None:
        if not add_step_atr > 0:
            raise ConfigurationError(f"add_step_atr must be > 0, got {add_step_atr}")
        if not (isinstance(max_buys, int) and max_buys >= 1):
            raise ConfigurationError(f"max_buys must be an integer >= 1, got {max_buys!r}")
        self.add_step_atr = add_step_atr
        self.max_buys = max_buys
        self.buy_count = 0
        self.last_buy_price: float | None = None

    def on_price(self, price: float, donchian_high: float, atr: float) -> str | None:
        if self.buy_count == 0:
            if price > donchian_high:
                self._buy(price)
                return "enter"
            return None
        # The source allows an add while buy_count <= 3, i.e. up to 4 buys.
        if self.buy_count < self.max_buys and price > self.last_buy_price + self.add_step_atr * atr:
            self._buy(price)
            return "add"
        return None

    def reset(self) -> None:
        """Flat again (e.g. after a regime exit)."""
        self.buy_count = 0
        self.last_buy_price = None

    def _buy(self, price: float) -> None:
        self.buy_count += 1
        self.last_buy_price = price


# ---------------------------------------------------------------- drawdown ladder


class DrawdownLadder:
    """Tiered lot multiplier on portfolio drawdown, with a halt tier, an
    optional liquidation request and hysteresis on resuming."""

    def __init__(
        self,
        tiers=((0.05, 0.75), (0.10, 0.5), (0.20, 0.0)),
        liquidate_at: float | None = None,
        resume_below: float | None = None,
    ) -> None:
        tiers = tuple(sorted((float(d), float(m)) for d, m in tiers))
        if not tiers:
            raise ConfigurationError("need at least one tier")
        prev_m = 1.0
        for d, m in tiers:
            if not 0 < d < 1 or not 0 <= m <= prev_m:
                raise ConfigurationError(
                    "tiers need drawdowns in (0, 1) and non-increasing multipliers in [0, 1]"
                )
            prev_m = m
        if liquidate_at is not None and not tiers[0][0] <= liquidate_at < 1:
            raise ConfigurationError("liquidate_at must be at or beyond the first tier and < 1")
        self.tiers = tiers
        self.liquidate_at = liquidate_at
        halt = next((d for d, m in tiers if m == 0.0), None)
        if resume_below is not None and (halt is None or not 0 <= resume_below < halt):
            raise ConfigurationError("resume_below needs a halt tier and must sit below it")
        self.halt_at = halt
        self.resume_below = resume_below
        self._halted = False

    def tier_multiplier(self, drawdown: float) -> float:
        """The deepest tier reached; 1.0 above the first tier."""
        m = 1.0
        for d, mult in self.tiers:
            if drawdown >= d:
                m = mult
        return m

    def observe(self, drawdown: float) -> float:
        """The lot multiplier for this bar, with halt hysteresis."""
        if self.halt_at is not None and drawdown >= self.halt_at:
            self._halted = True
        elif self._halted:
            resume = self.halt_at if self.resume_below is None else self.resume_below
            if drawdown < resume:
                self._halted = False
        return 0.0 if self._halted else self.tier_multiplier(drawdown)

    def liquidation_requested(self, drawdown: float) -> bool:
        """True past `liquidate_at`: a regime-exit request, not a sale."""
        return self.liquidate_at is not None and drawdown >= self.liquidate_at


# ---------------------------------------------------------------- S5


def bet_size_from_probability(
    p: float, n_classes: int = 2, min_probability: float | None = None
) -> float:
    """Lopez de Prado, AFML ch. 10: z = (p - 1/K) / sqrt(p (1 - p)),
    size = 2 * Phi(z) - 1, in [-1, 1] -- the standard probability-to-size
    curve the catalog's S5 asks for (ML2's predicted success probability ->
    lot fraction). Long-only callers clip negatives to zero; `min_probability`
    zeroes any trigger the model is less sure of than that."""
    from statistics import NormalDist

    if not (isinstance(n_classes, int) and n_classes >= 2):
        raise ConfigurationError(f"n_classes must be an integer >= 2, got {n_classes!r}")
    if not 0 <= p <= 1:
        raise ConfigurationError(f"p must be in [0, 1], got {p}")
    if min_probability is not None and p < min_probability:
        return 0.0
    if p in (0.0, 1.0):
        return 1.0 if p == 1.0 else -1.0
    z = (p - 1.0 / n_classes) / np.sqrt(p * (1.0 - p))
    return 2.0 * NormalDist().cdf(z) - 1.0


def split_conformal_interval(prediction: float, calibration_residuals, alpha: float = 0.1):
    """Split-conformal interval prediction +/- q, q the ceil((n+1)(1-alpha))-th
    smallest absolute calibration residual: covers the truth with
    probability >= 1 - alpha under exchangeability (ML4T ch. 17 sizes by
    such intervals; only its README was seen, so this is the textbook
    construction)."""
    r = np.sort(np.abs(np.asarray(calibration_residuals, dtype=float)))
    n = r.size
    if n < 1 or not 0 < alpha < 1:
        raise ConfigurationError("need calibration residuals and alpha in (0, 1)")
    k = int(np.ceil((n + 1) * (1 - alpha)))
    q = np.inf if k > n else float(r[k - 1])
    return prediction - q, prediction + q


def conformal_long_size(prediction: float, calibration_residuals, alpha: float = 0.1) -> float:
    """1.0 when the whole interval is above zero (the forecast gain is
    positive with coverage 1 - alpha), else 0.0 -- an uncertain trigger gets
    no lot."""
    low, _ = split_conformal_interval(prediction, calibration_residuals, alpha)
    return 1.0 if low > 0 else 0.0
