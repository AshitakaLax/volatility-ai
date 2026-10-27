"""engine/execution/limit_pricing.py: where each kind of limit order sits."""

from __future__ import annotations

import pytest

from engine.core.quotes import Quote
from engine.execution.limit_pricing import grid_buy, marketable_buy, marketable_sell


def _quote(bid, ask):
    return Quote("RSP", bid=bid, ask=ask, last=None, at=None, source="fidelity")


def test_a_grid_buy_rests_at_its_trigger_unless_the_spread_is_wide():
    assert grid_buy(217.0, None, max_spread=0.01).price == 217.0
    assert grid_buy(217.0, _quote(216.9, 217.1), max_spread=0.01).price == 217.0
    wide = grid_buy(217.0, _quote(214.0, 219.0), max_spread=0.01)
    assert wide.price is None and "spread" in wide.why


def test_a_marketable_buy_takes_the_ask_but_does_not_chase_it():
    assert (
        marketable_buy(217.0, _quote(216.9, 217.2), max_premium=0.01, buffer=0.005).price == 217.2
    )
    chased = marketable_buy(217.0, _quote(216.9, 225.0), max_premium=0.01, buffer=0.005)
    assert chased.price is None and "not chasing" in chased.why
    blind = marketable_buy(200.0, None, max_premium=0.01, buffer=0.005)
    assert blind.price == pytest.approx(201.0)


def test_a_marketable_sell_takes_the_bid_and_is_never_refused():
    assert (
        marketable_sell(217.0, _quote(216.8, 217.1), max_premium=0.01, buffer=0.005).price == 216.8
    )
    thin = marketable_sell(200.0, _quote(150.0, 201.0), max_premium=0.01, buffer=0.005)
    assert thin.price == pytest.approx(198.0), "floored, still offered"
    assert marketable_sell(200.0, None, max_premium=0.01, buffer=0.005).price == pytest.approx(
        199.0
    )


def test_a_quote_without_both_sides_has_no_spread():
    assert _quote(None, 217.0).spread is None
    assert _quote(217.2, 217.0).mid is None, "a crossed quote is not believed"
