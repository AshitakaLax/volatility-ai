"""
Task 1.5 acceptance test (B5): fill status must be validated before
cash/ledger mutation on both the buy and sell paths, and a confirmed
fill that would realize a loss must be rejected (no-loss invariant).

Uses a StubOMS test double (not a real broker/simulation path) to
force each of the four required negative-test scenarios from
implementation_task_specs.md Task 1.5, since SIMULATION mode's real
OrderManagementSystem always fills completely and profitably by
construction and can't produce these states on its own.

Scope note on the "partial sell" case: this repo's AssetLotLedger
does not support partial lot closes (close_lot(completed=False) raises
NotImplementedError -- see src/ledger.py and architecture_overview.md
Appendix 8, which ties real partial-close semantics to Task 7.2).
Given that, PARTIALLY_FILLED is handled the same conservative way as
any other non-FILLED status here: the lot stays fully open and no
cash is credited for it at all, rather than crediting the filled
portion and leaving a reduced remainder open. That's safe (nothing is
mis-credited or double-counted) but not the fuller behavior the task's
own test description names ("only filled quantity is removed... 
remaining cost basis remains open") -- flagging this rather than
quietly building partial-close ledger support to make the wording
match, which would be Task 7.2's job.
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.ledger import AssetLotLedger
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.size_calculators import FixedPortfolioPercentage

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


class StubOMS:
    """Test double standing in for OrderManagementSystem(mode="SIMULATION").
    Returns a fixed, caller-specified response for buys/sells when one
    is given; otherwise delegates to a real OrderManagementSystem so
    the untested side behaves normally (e.g. stubbing only sell
    behavior still needs buys to actually open lots first)."""

    def __init__(self, buy_response: dict | None = None, sell_response: dict | None = None):
        self._buy_response = buy_response
        self._sell_response = sell_response
        self._real = OrderManagementSystem(mode="SIMULATION")
        self.buy_calls: list[tuple] = []
        self.sell_calls: list[tuple] = []

    def execute_buy(self, symbol, trade_value, price):
        self.buy_calls.append((symbol, trade_value, price))
        if self._buy_response is not None:
            return self._buy_response
        return self._real.execute_buy(symbol, trade_value, price)

    def execute_sell(self, symbol, qty, price):
        self.sell_calls.append((symbol, qty, price))
        if self._sell_response is not None:
            return self._sell_response
        return self._real.execute_sell(symbol, qty, price)


def _run_one_bar_sweep_with_stub_oms(monkeypatch, df, buy_response=None, sell_response=None):
    """Runs run_sweep with OrderManagementSystem monkeypatched to
    StubOMS-with-fixed-responses for the duration of the call, then
    restores it. Returns (result_df, stub_instance)."""
    created: list[StubOMS] = []

    class _StubOMSFactory:
        def __call__(self, mode="SIMULATION"):
            stub = StubOMS(buy_response=buy_response, sell_response=sell_response)
            created.append(stub)
            return stub

    import optimization_controller as oc_module

    monkeypatch.setattr(oc_module, "OrderManagementSystem", _StubOMSFactory())

    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    return result, created[0]


def test_non_filled_buy_does_not_mutate_cash_or_ledger(monkeypatch):
    df = _load_fixture()
    non_filled_buy = {
        "id": "stub-1",
        "symbol": "TQQQ",
        "qty": 100.0,
        "filled_qty": 0.0,
        "filled_avg_price": 50.0,
        "status": OrderStatus.NEW,
    }
    result, stub = _run_one_bar_sweep_with_stub_oms(monkeypatch, df, buy_response=non_filled_buy)

    assert len(stub.buy_calls) > 0, "Test fixture didn't even attempt a buy -- fixture no longer triggers"
    row = result.iloc[0]
    # No buy was ever actually filled, so cash must be exactly the
    # initial 100,000 and no lots were ever registered.
    assert row["Final Equity"] == pytest.approx(100_000.0, abs=1e-8)
    assert row["Trade Count"] == 0


def test_non_filled_sell_does_not_close_lot_or_credit_cash(monkeypatch):
    df = _load_fixture()
    non_filled_sell = {
        "id": "stub-2",
        "symbol": "TQQQ",
        "qty": 0.0,
        "filled_qty": 0.0,
        "filled_avg_price": 0.0,
        "status": OrderStatus.REJECTED,
    }
    result, stub = _run_one_bar_sweep_with_stub_oms(monkeypatch, df, sell_response=non_filled_sell)

    assert len(stub.sell_calls) > 0, "Test fixture didn't even attempt a sell -- fixture no longer harvests"
    row = result.iloc[0]
    # 4 buys open (as in Task 0.1's baseline), 0 closed -- sells were
    # attempted but none filled, so every lot remains open.
    assert row["Trade Count"] == 4
    assert row["Closed Trade Count"] == 0
    assert row["Open Trade Count"] == 4


def test_partially_filled_sell_is_treated_conservatively_not_as_complete(monkeypatch):
    # See module docstring: this repo's ledger has no partial-close
    # support, so PARTIALLY_FILLED is handled the same as any other
    # non-FILLED status -- the lot stays fully open, nothing is credited.
    df = _load_fixture()
    partial_sell = {
        "id": "stub-3",
        "symbol": "TQQQ",
        "qty": 5.0,
        "filled_qty": 2.5,  # half-filled
        "filled_avg_price": 50.0,
        "status": OrderStatus.PARTIALLY_FILLED,
    }
    result, stub = _run_one_bar_sweep_with_stub_oms(monkeypatch, df, sell_response=partial_sell)
    row = result.iloc[0]
    assert row["Trade Count"] == 4
    assert row["Closed Trade Count"] == 0, "A PARTIALLY_FILLED sell must not close the lot"
    assert row["Open Trade Count"] == 4


def test_confirmed_fill_that_would_realize_a_loss_is_rejected(monkeypatch):
    df = _load_fixture()
    # status=FILLED, but filled_avg_price is far below any buy_price in
    # this fixture (bars trade in the ~$47-57 range) -- simulates a
    # hypothetical adverse-fill/slippage scenario the no-loss check
    # must catch even though the order otherwise "confirmed filled".
    loss_making_sell = {
        "id": "stub-4",
        "symbol": "TQQQ",
        "qty": 5.0,
        "filled_qty": 5.0,
        "filled_avg_price": 1.0,
        "status": OrderStatus.FILLED,
    }
    result, stub = _run_one_bar_sweep_with_stub_oms(monkeypatch, df, sell_response=loss_making_sell)
    row = result.iloc[0]
    assert len(stub.sell_calls) > 0
    assert row["Closed Trade Count"] == 0, "A loss-making fill must be rejected, not closed"
    assert row["Open Trade Count"] == 4
    # No loss recorded: cash must not have dropped below the initial
    # 100,000 minus whatever's still tied up in open (unsold) lots --
    # i.e. total equity shouldn't reflect a phantom realized loss.
    assert row["Realized PnL"] == 0


def test_simulation_mode_unaffected_task_0_1_baseline_unchanged():
    # Acceptance criterion: "Task 0.1's regression fixture output is
    # unchanged, confirming SIMULATION mode still always fills today."
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    row = result.iloc[0]
    assert row["Final Equity"] == 100099.81489816227
    assert row["Trade Count"] == 4
    assert row["Closed Trade Count"] == 4
