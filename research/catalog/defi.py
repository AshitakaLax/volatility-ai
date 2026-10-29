"""
Decentralised-exchange entries of the ranked list (ledger RK298, RK299).
Crypto is outside the owner's rules; this is research code on simulated
pools (research.catalog.crypto holds the centralised-exchange entries).

Sources:

  * Constant-product AMMs -- Adams, Zinsmeister & Robinson, "Uniswap v2
    core", 2020 (x y = k, fee taken from the input); the arbitrage that
    moves the pool to the external price and its closed-form size --
    Angeris, Kao, Chiang, Noyes & Chitra, "An analysis of Uniswap markets",
    Cryptoeconomic Systems 1, 2021.
  * Loss-versus-rebalancing -- Milionis, Moallemi, Roughgarden & Zhang,
    "Automated market making and loss-versus-rebalancing", 2022 (for a
    constant-product pool, instantaneous LVR = sigma^2 / 8 x pool value).
  * Concentrated liquidity -- Adams et al., "Uniswap v3 core", 2021 (amounts
    of a position with liquidity L on [pa, pb]); measured LP outcomes --
    Loesch, Hindman, Richardson & Welch, "Impermanent loss in Uniswap v3",
    2021 (fees below impermanent loss across the pools studied).
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- constant product (RK298)


def cpmm_out(amount_in: float, reserve_in: float, reserve_out: float, fee: float = 0.003) -> float:
    """Output of a swap into an x y = k pool (fee charged on the input)."""
    a = amount_in * (1 - fee)
    return reserve_out * a / (reserve_in + a)


def pool_price(reserve_x: float, reserve_y: float) -> float:
    """Price of X in units of Y."""
    return reserve_y / reserve_x


def optimal_arbitrage(
    reserve_x: float,
    reserve_y: float,
    cex_price: float,
    fee: float = 0.003,
    cex_fee: float = 0.001,
    gas: float = 0.0,
) -> dict:
    """Trade that takes the pool to the no-arbitrage band around the external
    price and its profit in Y after both venues' fees and gas. If the pool
    is cheap (price < cex), buy X from the pool with dy = (sqrt(g k p) - y) / g,
    g = 1 - fee, and sell it on the CEX; if rich, the mirror trade."""
    g = 1 - fee
    k = reserve_x * reserve_y
    p = pool_price(reserve_x, reserve_y)
    if p * (1 + cex_fee) < cex_price * g:  # pool cheap: Y in, X out
        dy = (np.sqrt(g * k * cex_price) - reserve_y) / g
        dx = cpmm_out(dy, reserve_y, reserve_x, fee)
        profit = dx * cex_price * (1 - cex_fee) - dy - gas
        return {
            "side": "buy_pool",
            "amount_in": float(dy),
            "amount_out": float(dx),
            "profit": float(profit),
            "execute": bool(profit > 0),
        }
    if p * g > cex_price * (1 + cex_fee):  # pool rich: X in, Y out
        dx = (np.sqrt(g * k / cex_price) - reserve_x) / g
        dy = cpmm_out(dx, reserve_x, reserve_y, fee)
        profit = dy - dx * cex_price * (1 + cex_fee) - gas
        return {
            "side": "sell_pool",
            "amount_in": float(dx),
            "amount_out": float(dy),
            "profit": float(profit),
            "execute": bool(profit > 0),
        }
    return {"side": "none", "amount_in": 0.0, "amount_out": 0.0, "profit": 0.0, "execute": False}


def lvr_rate(sigma: float, pool_value: float) -> float:
    """Milionis et al.: loss-versus-rebalancing per unit time of a CPMM."""
    return sigma**2 / 8 * pool_value


def simulate_arbitrage(
    cex_prices,
    reserve_x: float,
    reserve_y: float,
    fee: float = 0.003,
    cex_fee: float = 0.001,
    gas: float = 0.0,
) -> dict:
    """Run the arbitrageur against a CEX price path; returns its cumulative
    profit and the pool price path (which tracks the CEX within the fee band)."""
    x, y, total, path = reserve_x, reserve_y, 0.0, []
    for p in np.asarray(cex_prices, float):
        arb = optimal_arbitrage(x, y, p, fee, cex_fee, gas)
        if arb["execute"]:
            if arb["side"] == "buy_pool":
                x, y = x - arb["amount_out"], y + arb["amount_in"]
            else:
                x, y = x + arb["amount_in"], y - arb["amount_out"]
            total += arb["profit"]
        path.append(pool_price(x, y))
    return {"profit": total, "pool_price": np.array(path), "reserves": (x, y)}


# ---------------------------------------------------------------- concentrated liquidity (RK299)


def v3_amounts(liquidity: float, price: float, pa: float, pb: float) -> tuple[float, float]:
    """(x, y) held by a position with liquidity L on [pa, pb] at `price`."""
    if not 0 < pa < pb:
        raise ConfigurationError("need 0 < pa < pb")
    sp, sa, sb = np.sqrt(price), np.sqrt(pa), np.sqrt(pb)
    if price <= pa:
        return liquidity * (1 / sa - 1 / sb), 0.0
    if price >= pb:
        return 0.0, liquidity * (sb - sa)
    return liquidity * (1 / sp - 1 / sb), liquidity * (sp - sa)


def v3_liquidity(value: float, price: float, pa: float, pb: float) -> float:
    """Liquidity that a capital of `value` (in Y) buys on [pa, pb] at `price`."""
    x1, y1 = v3_amounts(1.0, price, pa, pb)
    return value / (x1 * price + y1)


def v3_value(liquidity: float, price: float, pa: float, pb: float) -> float:
    x, y = v3_amounts(liquidity, price, pa, pb)
    return x * price + y


def lp_backtest(
    prices,
    volumes,
    width: float = 0.1,
    fee_tier: float = 0.003,
    pool_liquidity: float = 1e6,
    capital: float = 1000.0,
    rebalance: bool = True,
    rebalance_cost: float = 0.001,
) -> dict:
    """RK299: provide `capital` on [p (1 - width), p (1 + width)]; each period
    the position earns fee_tier x volume x its share L / (L + pool_liquidity)
    while in range; when the price leaves the range and `rebalance` is on,
    the position is re-centred (paying rebalance_cost of its value). Returns
    the LP's final value, the buy-and-hold value of the initial tokens, the
    fees earned and the impermanent loss (hold - LP excluding fees)."""
    p = np.asarray(prices, float)
    v = np.asarray(volumes, float)
    pa, pb = p[0] * (1 - width), p[0] * (1 + width)
    liq = v3_liquidity(capital, p[0], pa, pb)
    x0, y0 = v3_amounts(liq, p[0], pa, pb)
    fees, rebalances = 0.0, 0
    for t in range(1, len(p)):
        if pa < p[t] < pb:
            fees += fee_tier * v[t] * liq / (liq + pool_liquidity)
        elif rebalance:
            value = v3_value(liq, p[t], pa, pb) * (1 - rebalance_cost)
            pa, pb = p[t] * (1 - width), p[t] * (1 + width)
            liq = v3_liquidity(value, p[t], pa, pb)
            rebalances += 1
    lp = v3_value(liq, p[-1], pa, pb)
    hold = x0 * p[-1] + y0
    return {
        "lp_value": float(lp + fees),
        "hold_value": float(hold),
        "fees": float(fees),
        "impermanent_loss": float(hold - lp),
        "rebalances": rebalances,
    }
