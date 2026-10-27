"""
Where a limit order is priced, by what it is for.

Outside the regular session every order is a LIMIT -- Fidelity refuses a
market order there, and Alpaca takes only limit DAY orders -- and the books
are thin, so where the limit sits decides whether it fills at all. Pure:
the trading loop (engine/trading/live_trading_loop.py) asks, the broker
adapters round to the cent in the safe direction (buys down, sells up).

Three purposes, three rules:

  * A HARVEST sells a lot at its own target. That price IS the limit; it is
    priced elsewhere (the lot) and not here.
  * A GRID BUY rests at the price that triggered it -- the backtest's
    intrabar fill model fills a resting limit at its level, so this is the
    order the research measured. Skipped (not priced) while the quote's
    spread is wider than live.orders.max_spread: the last trade then says
    little about where a buy would fill, and an order far from the touch is
    one that rests until its time-to-live cancels it.
  * A MARKETABLE order -- a rebalance buy or a signal exit -- must fill, so
    it crosses to the quote's far side (a buy at the ask, a sell at the
    bid), but never more than live.orders.max_premium past the bar's price.
    Without a quote it goes exit_limit_buffer through the bar's price, as
    every signal exit always has.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.quotes import Quote


@dataclass(frozen=True)
class Limit:
    """A limit price, or None and why there is no order this bar."""

    price: float | None
    why: str


def grid_buy(price: float, quote: Quote | None, *, max_spread: float) -> Limit:
    """A grid buy: at the trigger price, unless the spread is too wide."""
    spread = quote.spread if quote is not None else None
    if spread is not None and spread > max_spread:
        return Limit(
            None,
            f"the spread is {spread:.2%} (bid {quote.bid}, ask {quote.ask}), over the "
            f"{max_spread:.2%} a grid buy is placed into",
        )
    return Limit(float(price), "at the trigger price")


def marketable_buy(
    price: float, quote: Quote | None, *, max_premium: float, buffer: float
) -> Limit:
    """A buy that must fill: at the ask, capped max_premium over the price."""
    cap = float(price) * (1.0 + max_premium)
    if quote is not None and quote.ask:
        if quote.ask > cap:
            return Limit(
                None,
                f"the ask {quote.ask} is more than {max_premium:.2%} over {price}; not chasing it",
            )
        return Limit(float(quote.ask), "at the ask")
    return Limit(min(cap, float(price) * (1.0 + buffer)), f"{buffer:.2%} over the price")


def marketable_sell(
    price: float, quote: Quote | None, *, max_premium: float, buffer: float
) -> Limit:
    """A sell that must fill (a signal exit): at the bid, floored
    max_premium under the price. An exit is never refused for a wide
    spread -- being unable to leave is the worse outcome -- so a bid below
    the floor sells at the floor, a limit that may rest a bar and be
    offered again."""
    floor = float(price) * (1.0 - max_premium)
    if quote is not None and quote.bid:
        return Limit(max(float(quote.bid), floor), "at the bid")
    return Limit(max(floor, float(price) * (1.0 - buffer)), f"{buffer:.2%} under the price")
