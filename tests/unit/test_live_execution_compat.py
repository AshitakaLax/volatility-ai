"""
Tests for the live-execution compatibility work done to unblock
src/live_execution.py, pushed directly to main mid-session -- see the
chat this was produced in.
"""

import pytest

from src.exceptions import ConfigurationError
from src.order_management_system import Mode, OrderManagementSystem
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage


# --- FixedPortfolioPercentage: percentage / allocation_pct dual support ---

def test_percentage_kwarg_works_same_as_allocation_pct():
    a = FixedPortfolioPercentage(allocation_pct=0.1)
    b = FixedPortfolioPercentage(percentage=0.1)
    assert a.allocation_pct == b.allocation_pct == 0.1


def test_both_kwargs_agreeing_is_allowed():
    s = FixedPortfolioPercentage(allocation_pct=0.1, percentage=0.1)
    assert s.allocation_pct == 0.1


def test_both_kwargs_disagreeing_raises():
    with pytest.raises(ConfigurationError, match="disagree"):
        FixedPortfolioPercentage(allocation_pct=0.1, percentage=0.2)


def test_neither_kwarg_raises():
    with pytest.raises(ConfigurationError):
        FixedPortfolioPercentage()


def test_percentage_kwarg_still_validates_bounds():
    with pytest.raises(ConfigurationError):
        FixedPortfolioPercentage(percentage=1.5)


# --- RiskManager: max_total_exposure / max_total_exposure_pct dual support ---

def test_max_total_exposure_works_same_as_pct_variant():
    a = RiskManager(max_total_exposure_pct=0.5)
    b = RiskManager(max_total_exposure=0.5)
    assert a.max_total_exposure_pct == b.max_total_exposure_pct == 0.5


def test_both_exposure_kwargs_disagreeing_raises():
    with pytest.raises(ConfigurationError, match="disagree"):
        RiskManager(max_total_exposure_pct=0.5, max_total_exposure=0.6)


def test_risk_manager_now_validates_bounds():
    with pytest.raises(ConfigurationError):
        RiskManager(max_total_exposure_pct=1.5)  # > 1
    with pytest.raises(ConfigurationError):
        RiskManager(max_concurrent_lots=0)  # not positive
    with pytest.raises(ConfigurationError):
        RiskManager(max_concurrent_lots=-1)


def test_risk_manager_clamping_unaffected_by_alias_used():
    a = RiskManager(max_concurrent_lots=1, max_total_exposure_pct=0.5)
    b = RiskManager(max_concurrent_lots=1, max_total_exposure=0.5)
    args = (10_000.0, 100_000.0, 90_000.0, 0)
    assert a.clamp_trade_value(*args) == b.clamp_trade_value(*args)


# --- Mode enum ---

def test_mode_enum_interoperates_with_bare_strings():
    assert Mode.SIMULATION == "SIMULATION"
    assert Mode.LIVE == "LIVE"
    assert OrderManagementSystem(mode=Mode.SIMULATION).mode == "SIMULATION"


def test_mode_enum_construction_matches_bare_string_construction():
    from_enum = OrderManagementSystem(mode=Mode.SIMULATION)
    from_string = OrderManagementSystem(mode="SIMULATION")
    assert from_enum.mode == from_string.mode


def test_invalid_mode_still_rejected_with_enum_present():
    with pytest.raises(ConfigurationError):
        OrderManagementSystem(mode="NOT_REAL")
