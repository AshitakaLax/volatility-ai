"""research/catalog/options.py -- Black-Scholes, straddle, ThetaGang, GEX."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.options import (
    OptionQuote,
    bs_greeks,
    bs_price,
    cash_management_action,
    close_vix_hedges,
    gamma_exposure,
    gamma_flip,
    implied_vol,
    straddle_entry,
    straddle_pnl_at_expiry,
    tail_hedge_cadence_days,
    tail_hedge_entry_allowed,
    tail_hedge_harvest,
    tail_hedge_slice_budget,
    vix_hedge_weight,
    wheel_calls_to_write,
    wheel_put_roll_strike_cap,
    wheel_select_contract,
    wheel_should_roll,
    wheel_should_write,
)


def test_black_scholes_matches_hulls_textbook_values():
    assert bs_price(100, 100, 1.0, 0.05, 0.2, "call") == pytest.approx(10.4506, abs=1e-4)
    assert bs_price(100, 100, 1.0, 0.05, 0.2, "put") == pytest.approx(5.5735, abs=1e-4)


def test_put_call_parity():
    c, p = bs_price(95, 100, 0.5, 0.03, 0.3, "call"), bs_price(95, 100, 0.5, 0.03, 0.3, "put")
    assert c - p == pytest.approx(95 - 100 * math.exp(-0.03 * 0.5))


@pytest.mark.parametrize("right", ["call", "put"])
def test_greeks_match_finite_differences(right):
    s, k, t, r, v = 100.0, 105.0, 0.75, 0.02, 0.25
    g = bs_greeks(s, k, t, r, v, right)
    h = 1e-3
    price = lambda **kw: bs_price(kw.get("s", s), k, kw.get("t", t), r, kw.get("v", v), right)  # noqa: E731
    assert g["delta"] == pytest.approx((price(s=s + h) - price(s=s - h)) / (2 * h), rel=1e-5)
    assert g["gamma"] == pytest.approx(
        (price(s=s + h) - 2 * price() + price(s=s - h)) / h**2, rel=1e-3
    )
    assert g["vega"] == pytest.approx((price(v=v + h) - price(v=v - h)) / (2 * h), rel=1e-5)
    assert g["theta"] == pytest.approx(-(price(t=t + h) - price(t=t - h)) / (2 * h), rel=1e-4)


def test_implied_vol_recovers_the_input():
    price = bs_price(100, 110, 0.4, 0.01, 0.37, "put")
    assert implied_vol(price, 100, 110, 0.4, 0.01, "put") == pytest.approx(0.37, abs=1e-8)
    with pytest.raises(ConfigurationError):
        implied_vol(500.0, 100, 110, 0.4, 0.01, "put")


def test_straddle_signal_and_expiry_pnl():
    assert straddle_entry(5.2, 4.0) == 1 and straddle_entry(8.0, 4.0) == 0
    assert straddle_pnl_at_expiry(120, 100, 6, 4) == pytest.approx(10 * (20 - 10))
    assert straddle_pnl_at_expiry(100, 100, 6, 4) == pytest.approx(-100)


# ---------------------------------------------------------------- wheel


def test_wheel_writes_puts_on_red_days_and_calls_on_green_days():
    assert wheel_should_write("put", -0.01) and not wheel_should_write("put", 0.01)
    assert wheel_should_write("call", 0.01) and not wheel_should_write("call", -0.01)
    assert not wheel_should_write("put", 0.0)
    assert wheel_should_write("put", 0.01, green=True)


def _chain():
    return [
        OptionQuote("put", 90, 45, -0.20, 1.0, 50),
        OptionQuote("put", 95, 45, -0.31, 2.0, 50),
        OptionQuote("put", 98, 30, -0.30, 3.0, 50),  # too short
        OptionQuote("put", 97, 60, -0.29, 2.5, 5),  # thin open interest
        OptionQuote("call", 99, 45, 0.30, 2.0, 50),  # below average cost
        OptionQuote("call", 105, 45, 0.28, 1.5, 50),
    ]


def test_wheel_selects_the_eligible_contract_nearest_the_target_delta():
    assert wheel_select_contract(_chain(), "put").strike == 95
    assert wheel_select_contract(_chain(), "call", min_strike=100.0).strike == 105
    assert wheel_select_contract(_chain(), "put", minimum_credit=5.0) is None


def test_wheel_call_count_respects_cap_factor_and_floor():
    assert wheel_calls_to_write(1000) == 10
    assert wheel_calls_to_write(1000, cap_factor=0.5) == 5
    assert wheel_calls_to_write(1000, target_shares=1000, cap_target_floor=0.5) == 5


def test_wheel_roll_rules():
    assert wheel_should_roll(0.9, 30, "put", itm=False) == "roll"
    assert wheel_should_roll(0.2, 15, "put", itm=False) == "roll"
    assert wheel_should_roll(-0.2, 15, "put", itm=False) == "hold"  # below min_pnl
    assert wheel_should_roll(0.95, 30, "put", itm=True) == "hold"  # ITM puts are not rolled
    assert wheel_should_roll(0.95, 30, "call", itm=True) == "roll"
    assert wheel_should_roll(0.99, 90, "put", itm=False, close_at_pnl=0.99) == "close"
    assert wheel_put_roll_strike_cap(95.0, 1.8) == pytest.approx(96.8)


# ---------------------------------------------------------------- hedges and cash


def test_vxth_allocation_bands_and_close_rule():
    assert [vix_hedge_weight(v) for v in (12, 15, 29.9, 30, 49.9, 50, 80)] == [
        0.0,
        0.01,
        0.01,
        0.005,
        0.005,
        0.0,
        0.0,
    ]
    assert close_vix_hedges(50.1) and not close_vix_hedges(50.0)


def test_tail_hedge_budget_cadence_entry_and_harvest():
    assert tail_hedge_slice_budget(1_000_000) == pytest.approx(1_000_000 * 0.005 / 6)
    assert tail_hedge_cadence_days(6) == 61
    assert tail_hedge_entry_allowed(None, 18.0) and not tail_hedge_entry_allowed(None, 25.0)
    assert not tail_hedge_entry_allowed(30, 15.0) and tail_hedge_entry_allowed(61, 15.0)
    assert tail_hedge_harvest(40_000, 1_000_000) == 0.0
    assert tail_hedge_harvest(60_000, 1_000_000) == pytest.approx(30_000)


def test_cash_management_sweeps_beyond_the_thresholds():
    assert cash_management_action(25_000) == pytest.approx(25_000)
    assert cash_management_action(5_000) == 0.0
    assert cash_management_action(-15_000) == pytest.approx(-15_000)


# ---------------------------------------------------------------- GEX


def _gex_chain():
    return [
        SimpleNamespace(right="call", strike=110, open_interest=1000),
        SimpleNamespace(right="put", strike=90, open_interest=1000),
    ]


def test_gamma_exposure_sign_convention():
    calls = [SimpleNamespace(right="call", strike=100, open_interest=10, gamma=0.02)]
    puts = [SimpleNamespace(right="put", strike=100, open_interest=10, gamma=0.02)]
    assert gamma_exposure(calls, 100) == pytest.approx(0.02 * 10 * 100 * 100**2 * 0.01)
    assert gamma_exposure(puts, 100) == pytest.approx(-gamma_exposure(calls, 100))


def test_gamma_flips_between_the_put_and_call_walls():
    flip = gamma_flip(_gex_chain(), range(80, 121), t_of=lambda o: 0.1, r=0.0, iv_of=lambda o: 0.2)
    assert flip is not None and 90 < flip < 110
