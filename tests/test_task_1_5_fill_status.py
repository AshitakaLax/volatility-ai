import pandas as pd

import optimization_controller as controller_module
from optimization_controller import OptimizationController
from src.order_management_system import OrderStatus


class RecordingStrategy:
    def record_tick(self, current_price):
        pass

    def calculate_trade_value(self, total_equity, current_price, current_dd=0.0):
        return 1000.0


class RejectingOMS:
    def __init__(self, mode="SIMULATION"):
        self.calls = []
        self._buy_count = 0

    def execute_buy(self, symbol, trade_value, current_price):
        self.calls.append(("buy", symbol, trade_value, current_price))
        self._buy_count += 1
        return {
            "id": "rejected-buy",
            "status": OrderStatus.REJECTED.value,
            "qty": trade_value / current_price,
            "filled_qty": 0.0,
            "filled_avg_price": None,
        }

    def execute_sell(self, symbol, qty, target_price):
        self.calls.append(("sell", symbol, qty, target_price))
        return {
            "id": "rejected-sell",
            "status": OrderStatus.REJECTED.value,
            "qty": qty,
            "filled_qty": 0.0,
            "filled_avg_price": None,
        }


def test_rejected_buy_does_not_decrement_cash_or_create_lot(monkeypatch):
    monkeypatch.setattr(controller_module, "OrderManagementSystem", RejectingOMS)
    data = pd.DataFrame(
        {"close": [100.0, 99.0, 99.0]},
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )

    result = OptimizationController(data).run_sweep(
        [0.01], [0.01], RecordingStrategy, [{}]
    ).iloc[0]

    assert result["Final Portfolio Value"] == 100000.0
    assert result["Trade Count"] == 0


def test_rejected_sell_does_not_credit_cash_or_close_lot(monkeypatch):
    class BuyThenRejectSellOMS(RejectingOMS):
        def execute_buy(self, symbol, trade_value, current_price):
            self.calls.append(("buy", symbol, trade_value, current_price))
            qty = trade_value / current_price
            return {
                "id": "filled-buy",
                "status": OrderStatus.FILLED.value,
                "qty": qty,
                "filled_qty": qty,
                "filled_avg_price": current_price,
            }

    monkeypatch.setattr(controller_module, "OrderManagementSystem", BuyThenRejectSellOMS)
    data = pd.DataFrame(
        {"close": [100.0, 99.0, 101.0]},
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )

    result = OptimizationController(data).run_sweep(
        [0.01], [0.01], RecordingStrategy, [{}]
    ).iloc[0]

    # The buy is confirmed, but the target sell is rejected. The lot therefore
    # remains open and no sell proceeds are credited.
    assert result["Trade Count"] == 1
    assert result["Final Portfolio Value"] < 101000.0
