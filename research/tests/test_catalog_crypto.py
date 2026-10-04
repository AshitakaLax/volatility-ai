"""research/catalog/crypto.py -- blackbird, the bitcoin-arbitrage depth
walk, triangular arbitrage and funding carry."""

from __future__ import annotations

import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.crypto import (
    Level,
    annualized_funding,
    blackbird_entry,
    blackbird_exit,
    blackbird_performance,
    conversion_rates,
    cycle_return,
    depth_arbitrage,
    find_arbitrage_cycle,
    funding_carry_pnl,
    funding_carry_positions,
)


def test_blackbird_entry_threshold_is_net_of_four_fees():
    # README: 0.20% fees on both venues + SpreadEntry 0.30% -> trigger 1.10%
    enter, spread = blackbird_entry(100.0, 101.2, 0.002, 0.002)
    assert enter and spread == pytest.approx(0.012)
    assert not blackbird_entry(100.0, 101.0, 0.002, 0.002)[0]
    assert not blackbird_entry(100.0, 101.2, 0.002, 0.002, short_allowed=False)[0]


def test_blackbird_exit_on_spread_or_time():
    assert blackbird_exit(100.0, 99.5, 60)[0]  # spread -0.5% <= -0.4%
    assert not blackbird_exit(100.0, 99.8, 60)[0]
    assert blackbird_exit(100.0, 99.8, 3600, max_length=3600)[0]


def test_blackbird_performance_legs():
    p = blackbird_performance(100, 101, 102, 100.5, 0.002, 0.002)
    assert p["long"] == pytest.approx(0.01 - 0.004)
    assert p["short"] == pytest.approx(1.5 / 102 - 0.004)
    assert p["total"] == pytest.approx((p["long"] + p["short"]) / 2)


def test_depth_arbitrage_matches_the_hand_walk():
    asks = [Level(100, 1), Level(101, 1), Level(103, 5)]
    bids = [Level(104, 0.5), Level(102, 2), Level(99, 3)]
    out = depth_arbitrage(asks, bids)
    # best pair is two asks deep and two bids deep: buy 1@100 + 1@101,
    # sell 0.5@104 + 1.5@102
    assert out["profit"] == pytest.approx(4.0) and out["volume"] == pytest.approx(2.0)
    assert out["weighted_buy_price"] == pytest.approx(100.5)
    assert out["weighted_sell_price"] == pytest.approx(102.5)
    assert (out["buy_price"], out["sell_price"]) == (101, 102)
    assert out["percent"] == pytest.approx(4 / 101 / 2 * 100)
    assert depth_arbitrage(asks, bids, max_tx_volume=0.25)["profit"] == pytest.approx(1.0)
    assert depth_arbitrage([Level(105, 1)], bids)["profit"] == 0.0


def _quotes(eurgbp_bid):
    return {
        ("EUR", "USD"): (1.10, 1.1001),
        ("GBP", "USD"): (1.30, 1.3001),
        ("EUR", "GBP"): (eurgbp_bid, eurgbp_bid + 0.0001),
    }


def test_triangular_arbitrage_finds_the_mispriced_loop():
    rates = conversion_rates(_quotes(0.86))
    cycle = find_arbitrage_cycle(rates)
    assert cycle is not None and cycle[0] == cycle[-1] and len(cycle) == 4
    assert cycle_return(rates, cycle) == pytest.approx(0.86 * 1.30 / 1.1001)
    assert find_arbitrage_cycle(conversion_rates(_quotes(0.846))) is None
    assert find_arbitrage_cycle(conversion_rates(_quotes(0.86), fee=0.01)) is None
    with pytest.raises(ConfigurationError):
        conversion_rates({("A", "B"): (2.0, 1.0)})


def test_funding_carry_hysteresis_and_pnl():
    rates = [0.0001, 0.0002, 0.00005, -0.00001, 0.0002]  # per 8 hours
    assert annualized_funding([0.0001])[0] == pytest.approx(0.1095)
    pos = funding_carry_positions(rates, entry_apr=0.15, exit_apr=0.0)
    assert list(pos) == [0, 1, 1, 0, 1]
    pnl = funding_carry_pnl([100, 101, 102, 101, 103], [100, 101.5, 102, 100.5, 103], rates, pos)
    # held over periods 2 and 3: basis (1 - 0.5) and (-1 + 1.5), plus funding
    assert pnl["basis"].tolist() == pytest.approx([0, 0, 0.5, 0.5, 0])
    assert pnl["funding"].tolist() == pytest.approx([0, 0, 0.00005 * 102, -0.00001 * 100.5, 0])
    with pytest.raises(ConfigurationError):
        funding_carry_positions(rates, entry_apr=0.1, exit_apr=0.2)
