"""
Options algorithms for the database -- all out of scope for the platform
(ledger constraint: no options), recorded and implemented here so the
database is complete.

  Black-Scholes      price, delta, gamma, vega, theta and implied volatility
                     (bisection) for European options; the pricing every
                     strategy below needs when no market quotes are given.
  Q12 straddle       je-suis-tm/quant-trading "Options Straddle backtest.py":
                     enter a long call + long put at one strike when
                     |call - put| < threshold (the strike is near the money,
                     so the straddle is cheapest to own); the script's
                     defaults are threshold = 2 and contractsize = 10.
  S1 ThetaGang wheel brndnmtthws/thetagang, rules and defaults from its
                     thetagang.toml: write puts on red days and covered calls
                     on green days at target delta 0.30, DTE >= 45 (max 180),
                     open interest >= 10, credit >= 0.05; calls only at a
                     strike >= the average cost of the shares, on
                     cap_factor of them less a cap_target_floor share of the
                     target; roll at 90% of max profit, or at <= 15 DTE with
                     P&L >= min_pnl (0); ITM calls roll, ITM puts do not by
                     default; a rolled put's strike is capped at the old
                     strike plus the premium received.
  ThetaGang VIX call hedge (VXTH methodology): allocate a share of net
                     liquidation to 30-DTE, delta-0.30 VIX calls by the VIXMO
                     band -- <15: 0, 15-30: 1%, 30-50: 0.5%, >=50: 0 -- and
                     close them when spot VIX exceeds 50.
  ThetaGang tail hedge  long puts within an annual budget (0.5% of net
                     liquidation), split into entries_per_year slices on a
                     ceil(365 / entries_per_year)-day cadence, entered only when
                     VIX <= entry_vix_max, exited at <= exit_dte, harvested
                     back toward harvest_target_weight once their value
                     exceeds harvest_trigger_weight.
  ThetaGang cash management  sweep cash above target + buy_threshold into a
                     cash fund (SGOV), sell it when cash falls below target -
                     sell_threshold.
  C-RJ1 dealer gamma exposure  the standard per-strike GEX,
                     gamma * open_interest * 100 * spot^2 * 0.01, calls
                     positive and puts negative (the convention that dealers
                     are long calls and short puts), summed over strikes; the
                     "gamma flip" is the spot where the total crosses zero.
                     Baltussen et al. (2021) is the cited source; the catalog
                     rejected it for needing option positioning data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from engine.core.exceptions import ConfigurationError

_Z = NormalDist()

# ---------------------------------------------------------------- Black-Scholes


def _d1_d2(s: float, k: float, t: float, r: float, sigma: float, q: float = 0.0):
    if s <= 0 or k <= 0 or t <= 0 or sigma <= 0:
        raise ConfigurationError("need positive spot, strike, time and volatility")
    d1 = (math.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    return d1, d1 - sigma * math.sqrt(t)


def bs_price(s, k, t, r, sigma, right: str = "call", q: float = 0.0) -> float:
    d1, d2 = _d1_d2(s, k, t, r, sigma, q)
    if right == "call":
        return s * math.exp(-q * t) * _Z.cdf(d1) - k * math.exp(-r * t) * _Z.cdf(d2)
    if right == "put":
        return k * math.exp(-r * t) * _Z.cdf(-d2) - s * math.exp(-q * t) * _Z.cdf(-d1)
    raise ConfigurationError(f"right must be 'call' or 'put', got {right!r}")


def bs_greeks(s, k, t, r, sigma, right: str = "call", q: float = 0.0) -> dict[str, float]:
    """delta, gamma, vega (per 1.00 of vol), theta (per year)."""
    d1, d2 = _d1_d2(s, k, t, r, sigma, q)
    pdf = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    disc_q, disc_r = math.exp(-q * t), math.exp(-r * t)
    gamma = disc_q * pdf / (s * sigma * math.sqrt(t))
    vega = s * disc_q * pdf * math.sqrt(t)
    if right == "call":
        delta = disc_q * _Z.cdf(d1)
        theta = (
            -s * disc_q * pdf * sigma / (2 * math.sqrt(t))
            - r * k * disc_r * _Z.cdf(d2)
            + q * s * disc_q * _Z.cdf(d1)
        )
    elif right == "put":
        delta = -disc_q * _Z.cdf(-d1)
        theta = (
            -s * disc_q * pdf * sigma / (2 * math.sqrt(t))
            + r * k * disc_r * _Z.cdf(-d2)
            - q * s * disc_q * _Z.cdf(-d1)
        )
    else:
        raise ConfigurationError(f"right must be 'call' or 'put', got {right!r}")
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta}


def implied_vol(
    price,
    s,
    k,
    t,
    r,
    right: str = "call",
    q: float = 0.0,
    lo: float = 1e-6,
    hi: float = 5.0,
    tol: float = 1e-10,
) -> float:
    """Bisection on sigma; raises if the price is outside [price(lo), price(hi)]."""
    p_lo, p_hi = bs_price(s, k, t, r, lo, right, q), bs_price(s, k, t, r, hi, right, q)
    if not p_lo <= price <= p_hi:
        raise ConfigurationError("price is outside the attainable Black-Scholes range")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if bs_price(s, k, t, r, mid, right, q) < price:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- Q12 straddle


def straddle_entry(call_price: float, put_price: float, threshold: float = 2.0) -> int:
    """The script's signal: 1 when |call - put| < threshold, else 0."""
    return 1 if abs(call_price - put_price) < threshold else 0


def straddle_pnl_at_expiry(
    spot: float, strike: float, call_premium: float, put_premium: float, contractsize: float = 10.0
) -> float:
    """Long call + long put at `strike`: contractsize * (|S - K| - premiums)."""
    return contractsize * (abs(spot - strike) - call_premium - put_premium)


# ---------------------------------------------------------------- S1 ThetaGang wheel


@dataclass(frozen=True)
class OptionQuote:
    right: str  # 'call' or 'put'
    strike: float
    dte: int
    delta: float  # signed, as quoted
    bid: float
    open_interest: int


def wheel_should_write(
    right: str, day_change: float, green: bool | None = None, red: bool | None = None
) -> bool:
    """write_when: puts on red days (green=False, red=True by default),
    calls on green days (green=True, red=False). A day is green when the
    underlying is up, red when it is down; flat days write neither."""
    defaults = {"put": (False, True), "call": (True, False)}
    if right not in defaults:
        raise ConfigurationError(f"right must be 'call' or 'put', got {right!r}")
    g, r = defaults[right]
    g = g if green is None else green
    r = r if red is None else red
    return (g and day_change > 0) or (r and day_change < 0)


def wheel_select_contract(
    chain,
    right: str,
    target_delta: float = 0.30,
    min_dte: int = 45,
    max_dte: int = 180,
    min_open_interest: int = 10,
    minimum_credit: float = 0.05,
    min_strike: float | None = None,
):
    """The eligible contract whose |delta| is closest to target_delta:
    min_dte <= DTE <= max_dte, open interest >= min_open_interest, bid >=
    minimum_credit and, for calls, strike >= min_strike (the average cost)."""
    eligible = [
        o
        for o in chain
        if o.right == right
        and min_dte <= o.dte <= max_dte
        and o.open_interest >= min_open_interest
        and o.bid >= minimum_credit
        and (min_strike is None or right != "call" or o.strike >= min_strike)
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda o: (abs(abs(o.delta) - target_delta), o.dte))


def wheel_calls_to_write(
    shares_held: int, target_shares: int = 0, cap_factor: float = 1.0, cap_target_floor: float = 0.0
) -> int:
    """Covered-call contracts: cap_factor of the shares held, never covering
    the cap_target_floor share of the target that stays uncovered."""
    if not 0 <= cap_factor <= 1 or not 0 <= cap_target_floor <= 1:
        raise ConfigurationError("cap_factor and cap_target_floor must be in [0, 1]")
    coverable = min(shares_held * cap_factor, shares_held - cap_target_floor * target_shares)
    return max(0, int(coverable // 100))


def wheel_should_roll(
    pnl: float,
    dte: int,
    right: str,
    itm: bool,
    roll_pnl: float = 0.9,
    roll_dte: int = 15,
    min_pnl: float = 0.0,
    calls_itm: bool = True,
    puts_itm: bool = False,
    close_at_pnl: float | None = None,
) -> str:
    """'close', 'roll' or 'hold' for a short option, per roll_when."""
    if close_at_pnl is not None and pnl >= close_at_pnl:
        return "close"
    if itm and not (calls_itm if right == "call" else puts_itm):
        return "hold"
    if pnl >= roll_pnl or (dte <= roll_dte and pnl >= min_pnl):
        return "roll"
    return "hold"


def wheel_put_roll_strike_cap(old_strike: float, premium_received: float) -> float:
    """A rolled put's new strike may not exceed old strike + premium."""
    return old_strike + premium_received


# ---------------------------------------------------------------- VIX call hedge

VXTH_ALLOCATION = ((None, 15.0, 0.0), (15.0, 30.0, 0.01), (30.0, 50.0, 0.005), (50.0, None, 0.0))


def vix_hedge_weight(vixmo: float, allocation=VXTH_ALLOCATION) -> float:
    """The first band with lower <= VIXMO < upper (bounds optional)."""
    for lower, upper, weight in allocation:
        if (lower is None or vixmo >= lower) and (upper is None or vixmo < upper):
            return weight
    return 0.0


def close_vix_hedges(spot_vix: float, threshold: float = 50.0) -> bool:
    return spot_vix > threshold


# ---------------------------------------------------------------- tail hedge


def tail_hedge_slice_budget(
    net_liquidation: float,
    annual_budget: float = 0.005,
    budget_weight: float = 1.0,
    entries_per_year: int = 6,
) -> float:
    if entries_per_year < 1:
        raise ConfigurationError("entries_per_year must be >= 1")
    return net_liquidation * annual_budget * budget_weight / entries_per_year


def tail_hedge_cadence_days(entries_per_year: int = 6) -> int:
    return math.ceil(365 / entries_per_year)


def tail_hedge_entry_allowed(
    days_since_last_entry: int | None,
    vix: float,
    entries_per_year: int = 6,
    entry_vix_max: float = 20.0,
) -> bool:
    due = days_since_last_entry is None or days_since_last_entry >= tail_hedge_cadence_days(
        entries_per_year
    )
    return due and vix <= entry_vix_max


def tail_hedge_harvest(
    hedge_value: float,
    regime_base: float,
    trigger_weight: float = 0.05,
    target_weight: float = 0.03,
) -> float:
    """Dollar value of puts to sell: down to target_weight * base, but only
    once the hedge exceeds trigger_weight * base."""
    if hedge_value <= trigger_weight * regime_base:
        return 0.0
    return hedge_value - target_weight * regime_base


# ---------------------------------------------------------------- cash management


def cash_management_action(
    cash: float,
    target_cash: float = 0.0,
    buy_threshold: float = 10_000,
    sell_threshold: float = 10_000,
) -> float:
    """Dollars of the cash fund to buy (positive) or sell (negative)."""
    if cash > target_cash + buy_threshold:
        return cash - target_cash
    if cash < target_cash - sell_threshold:
        return cash - target_cash
    return 0.0


# ---------------------------------------------------------------- C-RJ1 gamma exposure


def gamma_exposure(chain, spot: float, t_of=None, r: float = 0.0, iv_of=None) -> float:
    """Total GEX in dollars per 1% move: sum of gamma * OI * 100 * S^2 * 0.01,
    calls positive, puts negative. `chain` items need right/strike/open_interest
    and either a `gamma` attribute or (with t_of and iv_of callables) inputs to
    compute it by Black-Scholes at `spot`."""
    total = 0.0
    for o in chain:
        if hasattr(o, "gamma"):
            gamma = o.gamma
        else:
            gamma = bs_greeks(spot, o.strike, t_of(o), r, iv_of(o), o.right)["gamma"]
        sign = 1.0 if o.right == "call" else -1.0
        total += sign * gamma * o.open_interest * 100 * spot**2 * 0.01
    return total


def gamma_flip(chain, spots, t_of, r: float, iv_of) -> float | None:
    """The first spot (in ascending `spots`) where total GEX changes sign,
    linearly interpolated; None if it never does."""
    spots = sorted(spots)
    prev_s, prev_g = None, None
    for s in spots:
        g = gamma_exposure(chain, s, t_of, r, iv_of)
        if prev_g is not None and (prev_g <= 0 < g or prev_g >= 0 > g):
            return prev_s + (s - prev_s) * (0 - prev_g) / (g - prev_g)
        prev_s, prev_g = s, g
    return None
