"""
Crypto arbitrage and carry (ledger A7 and C-RJ2, both ❌: wrong asset
class, multiple venues and short legs). Transcribed so the database has
them.

Sources:

  * A7 blackbird (butor/blackbird; read from the Buanderie/blackbird fork:
    check_entry_exit.cpp, result.cpp, README.md) -- long/short
    market-neutral arbitrage between two exchanges.
  * A7 maxme/bitcoin-arbitrage, arbitrage/arbitrer.py -- the order-book
    depth walk that sizes a cross-exchange opportunity.
  * A7 triangular arbitrage -- the textbook negative-cycle formulation
    (Sedgewick & Wayne, *Algorithms* 4th ed., section 4.4, "Arbitrage"):
    a cycle of conversions is profitable iff the sum of -ln(rate) around
    it is negative; Bellman-Ford finds one.
  * C-RJ2 funding-rate (cash-and-carry) arbitrage on perpetual futures --
    the ML4T crypto-perps case study the catalog cites; the mechanics are
    the exchanges' (funding paid every 8 hours, longs pay shorts when the
    rate is positive), the thresholds are parameters.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- blackbird


def blackbird_entry(
    ask_long: float,
    bid_short: float,
    fee_long: float,
    fee_short: float,
    spread_entry: float = 0.0030,
    short_allowed: bool = True,
) -> tuple[bool, float]:
    """checkEntry: buy on the cheap exchange at its ask, short on the dear
    one at its bid, when spread_in = (bid_short - ask_long) / ask_long
    reaches 2*fee_long + 2*fee_short + SpreadEntry -- SpreadEntry is the
    target NET of the four fees (README: 0.30% on two 0.20%-fee venues sets
    the trigger at 1.10%). Needs a venue that allows shorting. Returns
    (enter?, spread_in)."""
    if ask_long <= 0 or bid_short <= 0:
        return False, float("nan")
    spread_in = (bid_short - ask_long) / ask_long
    limit = 2 * fee_long + 2 * fee_short + spread_entry
    return short_allowed and spread_in >= limit, spread_in


def blackbird_exit(
    bid_long: float,
    ask_short: float,
    seconds_open: float,
    spread_exit: float = -0.0040,
    max_length: float = float("inf"),
) -> tuple[bool, float]:
    """checkExit: unwind (sell the long at its bid, cover the short at its
    ask) when spread_out = (ask_short - bid_long) / bid_long falls to
    SpreadExit (README default -0.40%), or when the trade has been open for
    MaxLength seconds. Returns (exit?, spread_out)."""
    spread_out = (ask_short - bid_long) / bid_long if bid_long > 0 else float("nan")
    if seconds_open >= max_length:
        return True, spread_out
    return bid_long > 0 and ask_short > 0 and spread_out <= spread_exit, spread_out


def blackbird_performance(
    long_in: float,
    long_out: float,
    short_in: float,
    short_out: float,
    fee_long: float,
    fee_short: float,
) -> dict[str, float]:
    """result.cpp perfLong/perfShort: each leg's return net of two fees; with
    equal exposure on both venues the trade's return (totPerf, balance
    change over 2 x exposure) is their average."""
    perf_long = (long_out - long_in) / long_in - 2 * fee_long
    perf_short = (short_in - short_out) / short_in - 2 * fee_short
    return {"long": perf_long, "short": perf_short, "total": (perf_long + perf_short) / 2}


# ---------------------------------------------------------------- bitcoin-arbitrage


@dataclass(frozen=True)
class Level:
    price: float
    amount: float


def _max_depth(asks: list[Level], bids: list[Level]) -> tuple[int, int]:
    """arbitrer.get_max_depth: how deep each book crosses the other's top."""
    i = 0
    if asks and bids:
        while asks[i].price < bids[0].price and i < len(asks) - 1:
            i += 1
    j = 0
    if asks and bids:
        while asks[0].price < bids[j].price and j < len(bids) - 1:
            j += 1
    return i, j


def _profit_for(mi, mj, asks, bids, max_tx_volume):
    """arbitrer.get_profit_for: buy asks[0..mi], sell bids[0..mj], volume
    capped by both books and max_tx_volume; volume-weighted prices."""
    if asks[mi].price >= bids[mj].price:
        return 0.0, 0.0, 0.0, 0.0
    max_amount = min(
        sum(a.amount for a in asks[: mi + 1]),
        sum(b.amount for b in bids[: mj + 1]),
        max_tx_volume,
    )
    buy_total = w_buy = 0.0
    for a in asks[: mi + 1]:
        amount = min(max_amount, buy_total + a.amount) - buy_total
        if amount <= 0:
            break
        buy_total += amount
        w_buy = (
            a.price if w_buy == 0 else (w_buy * (buy_total - amount) + a.price * amount) / buy_total
        )
    sell_total = w_sell = 0.0
    for b in bids[: mj + 1]:
        amount = min(max_amount, sell_total + b.amount) - sell_total
        if amount < 0:
            break
        sell_total += amount
        if w_sell == 0 or sell_total == 0:
            w_sell = b.price
        else:
            w_sell = (w_sell * (sell_total - amount) + b.price * amount) / sell_total
    return sell_total * w_sell - buy_total * w_buy, sell_total, w_buy, w_sell


def depth_arbitrage(asks: list[Level], bids: list[Level], max_tx_volume: float = 10.0) -> dict:
    """arbitrer.arbitrage_depth_opportunity + arbitrage_opportunity: try
    every (ask depth, bid depth) pair up to where the books stop crossing
    and keep the most profitable (ties to the deeper pair, `>=`). `asks` is
    the cheap venue's ask ladder, `bids` the dear venue's bid ladder, both
    best first. `percent` is the source's perc2, profit as a share of the
    volume bought."""
    if not asks or not bids:
        raise ConfigurationError("both books need at least one level")
    maxi, maxj = _max_depth(asks, bids)
    best = (0.0, 0.0, 0, 0, 0.0, 0.0)
    for i in range(maxi + 1):
        for j in range(maxj + 1):
            profit, volume, wb, ws = _profit_for(i, j, asks, bids, max_tx_volume)
            if profit >= 0 and profit >= best[0]:
                best = (profit, volume, i, j, wb, ws)
    profit, volume, i, j, wb, ws = best
    buyprice = asks[i].price
    percent = (1 - (volume - profit / buyprice) / volume) * 100 if volume else 0.0
    return {
        "profit": profit,
        "volume": volume,
        "buy_price": buyprice,
        "sell_price": bids[j].price,
        "weighted_buy_price": wb,
        "weighted_sell_price": ws,
        "percent": percent,
    }


# ---------------------------------------------------------------- triangular arbitrage


def conversion_rates(quotes: dict[tuple[str, str], tuple[float, float]], fee: float = 0.0) -> dict:
    """From quotes {(base, quote): (bid, ask)} -- price of one base in
    quote units -- build the directed conversion graph: selling base for
    quote at the bid, buying base with quote at 1/ask, each net of `fee`."""
    rates: dict = {}
    for (base, quote), (bid, ask) in quotes.items():
        if bid <= 0 or ask <= 0 or bid > ask:
            raise ConfigurationError(f"bad quote for {base}/{quote}: bid {bid}, ask {ask}")
        rates[(base, quote)] = bid * (1 - fee)
        rates[(quote, base)] = (1 / ask) * (1 - fee)
    return rates


def cycle_return(rates: dict, path: list[str]) -> float:
    """Gross multiple from converting around `path` (first == last)."""
    out = 1.0
    for a, b in itertools.pairwise(path):
        out *= rates[(a, b)]
    return out


def find_arbitrage_cycle(rates: dict) -> list[str] | None:
    """Bellman-Ford on edge weights -ln(rate): a negative cycle is a loop of
    conversions that multiplies money. Returns one such cycle (closed,
    first == last) or None."""
    nodes = sorted({a for a, _ in rates} | {b for _, b in rates})
    dist = dict.fromkeys(nodes, 0.0)  # virtual source to every node
    pred: dict = dict.fromkeys(nodes)
    edges = [(a, b, -math.log(r)) for (a, b), r in rates.items()]
    last = None
    for _ in range(len(nodes)):
        last = None
        for a, b, w in edges:
            if dist[a] + w < dist[b] - 1e-15:
                dist[b], pred[b], last = dist[a] + w, a, b
        if last is None:
            return None
    v = last
    for _ in range(len(nodes)):  # step back onto the cycle
        v = pred[v]
    cycle, u = [v], pred[v]
    while u != v:
        cycle.append(u)
        u = pred[u]
    cycle.append(v)
    return cycle[::-1]


# ---------------------------------------------------------------- C-RJ2 funding carry


def annualized_funding(rate_per_period, periods_per_day: int = 3) -> np.ndarray:
    """A perpetual's funding rate (per 8-hour period by default) as an
    annual rate: rate x periods/day x 365."""
    return np.asarray(rate_per_period, dtype=float) * periods_per_day * 365


def funding_carry_positions(
    funding_rate, entry_apr: float, exit_apr: float = 0.0, periods_per_day: int = 3
) -> np.ndarray:
    """Cash-and-carry with hysteresis: hold long spot / short perpetual (+1)
    once the last observed funding, annualised, reaches entry_apr; unwind
    when it drops below exit_apr. Positive funding is paid by longs to
    shorts, so the short perp collects it. The position decided on
    period t's print earns period t+1's funding."""
    if exit_apr > entry_apr:
        raise ConfigurationError("exit_apr must not exceed entry_apr")
    apr = annualized_funding(funding_rate, periods_per_day)
    pos = np.zeros(len(apr), dtype=int)
    held = 0
    for t, a in enumerate(apr):
        if not held and a >= entry_apr:
            held = 1
        elif held and a < exit_apr:
            held = 0
        pos[t] = held
    return pos


def funding_carry_pnl(spot, perp, funding_rate, positions) -> pd.DataFrame:
    """Per-period P&L of one unit of the hedge held from t-1 to t: spot
    change minus perp change (the basis move) plus the funding the short
    collects, rate_t x perp_t."""
    s, p, f = (np.asarray(v, dtype=float) for v in (spot, perp, funding_rate))
    held = np.r_[0, np.asarray(positions)[:-1]]
    basis = np.r_[0.0, np.diff(s) - np.diff(p)]
    funding = f * p
    return pd.DataFrame(
        {"basis": held * basis, "funding": held * funding, "pnl": held * (basis + funding)}
    )
