"""Tests for Task 7.15 — no-loss sell economics guard (Rule One §2.1).

All tests use deterministic fixtures (no random seeds needed for these
unit/integration tests; the scenarios are fully specified).

The single public API under test is:
    src.ledger.validate_sell(lot, quantity, quoted_price, cost_model)
    -> SellEconomics   (success)
    raises SellEconomicsError  (rejection)

Integration tests verify that the guard is wired into the backtest sell path
(optimization_controller._simulate_single) and the live path
(LiveExecutionLoop.submit_sell / apply_sell_fill).
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.cost_models import SlippageCommissionModel, ZeroCostModel
from src.exceptions import SellEconomicsError
from src.ledger import (
    MONEY_EPSILON,
    AssetLotLedger,
    InventoryLot,
    SellEconomics,
    validate_sell,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_lot(
    buy_price: float = 100.0,
    shares: float = 10.0,
    profit_target: float = 0.05,
    buy_costs: float = 0.0,
    symbol: str = "TQQQ",
    order_id: str = "order-1",
) -> InventoryLot:
    """Build an InventoryLot directly (bypasses ledger for unit isolation)."""
    return InventoryLot(
        order_id=order_id,
        symbol=symbol,
        buy_price=buy_price,
        shares=shares,
        target_sell_price=buy_price * (1.0 + profit_target),
        buy_costs=buy_costs,
    )


# ---------------------------------------------------------------------------
# Unit tests: validate_sell — success paths
# ---------------------------------------------------------------------------

class TestValidateSellSuccess:

    def test_profitable_sell_passes_with_zero_cost_model(self):
        """Sell at target price with no costs: proceeds > cost_basis → pass."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.05)
        # target_sell_price = 105.0; cost_basis = 1000.0; proceeds = 1050.0
        econ = validate_sell(lot, 10.0, 105.0, ZeroCostModel())

        assert isinstance(econ, SellEconomics)
        assert econ.quantity == pytest.approx(10.0)
        assert econ.allocated_cost_basis == pytest.approx(1000.0)
        assert econ.sell_costs == pytest.approx(0.0)
        assert econ.net_sell_proceeds == pytest.approx(1050.0)
        assert econ.realized_pnl == pytest.approx(50.0)

    def test_exact_break_even_passes(self):
        """Proceeds exactly equal to cost basis: on the boundary, passes (≥ not >)."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        # target_sell_price = 100.0; cost_basis = 1000.0; proceeds = 1000.0
        econ = validate_sell(lot, 10.0, 100.0, ZeroCostModel())
        assert econ.realized_pnl == pytest.approx(0.0)
        assert econ.net_sell_proceeds == pytest.approx(econ.allocated_cost_basis)

    def test_break_even_within_epsilon_passes(self):
        """Proceeds within MONEY_EPSILON below basis: still passes."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        # Manufacture a price slightly below break-even but within epsilon
        tiny_loss_price = 100.0 - (MONEY_EPSILON * 0.5) / 10.0
        econ = validate_sell(lot, 10.0, tiny_loss_price, ZeroCostModel())
        # Should not raise — within epsilon tolerance
        assert econ.realized_pnl > -MONEY_EPSILON

    def test_partial_lot_profitable_passes(self):
        """Sell 4 of 10 shares at target price: proportional basis allocated."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.05, buy_costs=20.0)
        # full cost_basis = 100*10 + 20 = 1020.0
        # allocated for 4 of 10 = 1020 * 0.4 = 408.0
        # proceeds = 4 * 105 = 420.0
        econ = validate_sell(lot, 4.0, 105.0, ZeroCostModel())
        assert econ.allocated_cost_basis == pytest.approx(408.0)
        assert econ.net_sell_proceeds == pytest.approx(420.0)
        assert econ.realized_pnl == pytest.approx(12.0)

    def test_sell_economics_formula_invariants(self):
        """Verify canonical formulas: realized_pnl = net_sell_proceeds - allocated_cost_basis."""
        lot = _make_lot(buy_price=50.0, shares=20.0, profit_target=0.10, buy_costs=15.0)
        model = SlippageCommissionModel(commission_per_trade=5.0, slippage_bps=10.0)
        econ = validate_sell(lot, 15.0, 55.0, model)

        # Cross-check formula
        expected_pnl = econ.net_sell_proceeds - econ.allocated_cost_basis
        assert math.isclose(econ.realized_pnl, expected_pnl, abs_tol=MONEY_EPSILON)

    def test_buy_costs_included_in_allocated_basis(self):
        """buy_costs on the lot flow correctly into allocated_cost_basis_for(qty)."""
        # 5 shares bought at 100.0 with 10.0 buy commission
        lot = _make_lot(buy_price=100.0, shares=5.0, profit_target=0.10, buy_costs=10.0)
        # cost_basis = 500 + 10 = 510 for all 5 shares
        # allocated for 2 of 5 = 510 * (2/5) = 204.0
        econ = validate_sell(lot, 2.0, 115.0, ZeroCostModel())
        assert econ.allocated_cost_basis == pytest.approx(204.0)
        assert econ.net_sell_proceeds == pytest.approx(230.0)  # 2 * 115
        assert econ.realized_pnl == pytest.approx(26.0)


# ---------------------------------------------------------------------------
# Unit tests: validate_sell — rejection paths
# ---------------------------------------------------------------------------

class TestValidateSellRejection:

    def test_commission_causes_loss_rejected(self):
        """Nominal price is profitable, but commission tips into a loss."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        # cost_basis = 1000.0; proceeds before commission = 1000.0
        # commission = 5.0 → net = 995.0 < 1000.0 → REJECT
        model = SlippageCommissionModel(commission_per_trade=5.0, slippage_bps=0.0)
        with pytest.raises(SellEconomicsError) as exc_info:
            validate_sell(lot, 10.0, 100.0, model)
        assert "Rule One violation" in str(exc_info.value)

    def test_slippage_causes_loss_rejected(self):
        """Slippage alone (no commission) erodes proceeds below cost basis."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        # effective sell price = 100 * (1 - 200bps) = 98.0; proceeds = 980 < 1000
        model = SlippageCommissionModel(commission_per_trade=0.0, slippage_bps=200.0)
        with pytest.raises(SellEconomicsError):
            validate_sell(lot, 10.0, 100.0, model)

    def test_slippage_and_commission_together_rejected(self):
        """Combined slippage + commission erodes a small profit target."""
        # buy at 100, profit_target=0.005 → target = 100.5
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.005)
        # effective = 100.5 * (1 - 100bps) = 99.495; proceeds = 994.95
        # cost_basis = 1000.0 → REJECT
        model = SlippageCommissionModel(commission_per_trade=0.0, slippage_bps=100.0)
        with pytest.raises(SellEconomicsError):
            validate_sell(lot, 10.0, 100.5, model)

    def test_partial_lot_loss_rejected(self):
        """Partial quantity sell where proportional basis exceeds net proceeds."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0, buy_costs=50.0)
        # allocated_cost_basis for 4 of 10 shares = (1000 + 50) * 0.4 = 420.0
        # net proceeds at quoted_price=100.0, zero-cost: 4 * 100 = 400 < 420 → REJECT
        with pytest.raises(SellEconomicsError):
            validate_sell(lot, 4.0, 100.0, ZeroCostModel())

    def test_rejection_exception_is_subclass_of_execution_error(self):
        """SellEconomicsError is a domain exception subclass of ExecutionError."""
        from src.exceptions import ExecutionError
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        model = SlippageCommissionModel(commission_per_trade=100.0)
        with pytest.raises(ExecutionError):
            validate_sell(lot, 10.0, 100.0, model)

    def test_rejection_exception_contains_key_values(self):
        """SellEconomicsError message surfaces net_sell_proceeds and allocated_cost_basis."""
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0)
        model = SlippageCommissionModel(commission_per_trade=10.0)
        with pytest.raises(SellEconomicsError) as exc_info:
            validate_sell(lot, 10.0, 100.0, model)
        msg = str(exc_info.value)
        assert "net_sell_proceeds" in msg
        assert "allocated_cost_basis" in msg


# ---------------------------------------------------------------------------
# Unit tests: validate_sell — argument validation
# ---------------------------------------------------------------------------

class TestValidateSellArgValidation:

    def test_non_positive_quantity_raises_value_error(self):
        lot = _make_lot()
        with pytest.raises(ValueError, match="quantity must be positive"):
            validate_sell(lot, 0.0, 105.0, ZeroCostModel())

    def test_quantity_exceeds_lot_shares_raises_value_error(self):
        lot = _make_lot(shares=5.0)
        with pytest.raises(ValueError, match="exceeds remaining lot shares"):
            validate_sell(lot, 6.0, 105.0, ZeroCostModel())


# ---------------------------------------------------------------------------
# Integration test: backtest sell path
# ---------------------------------------------------------------------------

class TestBacktestIntegration:
    """Verify validate_sell is wired into _simulate_single."""

    def _make_data(self, prices: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {"close": prices},
            index=pd.date_range("2024-01-01", periods=len(prices), freq="D"),
        )

    def _simple_strategy(self):
        from src.size_calculators import SizingStrategy

        class FixedStrategy(SizingStrategy):
            def record_tick(self, context):
                pass

            def calculate_trade_value(self, context):
                return 1000.0

        return FixedStrategy()

    def test_zero_cost_model_sell_passes_and_credits_cash(self):
        """Standard backtest: ZeroCostModel sell passes and cash increases."""
        from optimization_controller import OptimizationController

        data = self._make_data([100.0, 99.0, 106.0])
        controller = OptimizationController(data)
        strategy = self._simple_strategy()
        result = controller._simulate_single(
            step=0.01,
            target=0.05,
            strategy_instance=strategy,
            symbol="TQQQ",
            initial_cash=100_000.0,
            cost_model=ZeroCostModel(),
            risk_manager=__import__("src.risk_manager", fromlist=["RiskManager"]).RiskManager(),
        )
        # At least one sell should have completed — trade count ≥ 1
        assert result.metrics["Trade Count"] >= 1

    def test_aggressive_cost_model_blocks_sell(self):
        """With huge slippage (5000 bps), the sell is always rejected by the guard."""
        from optimization_controller import OptimizationController

        # Aggressive model: 5000 bps = 50% slippage — effective sell price = 50% of quoted
        model = SlippageCommissionModel(slippage_bps=5000.0)
        data = self._make_data([100.0, 99.0, 106.0])
        controller = OptimizationController(data)
        strategy = self._simple_strategy()
        result = controller._simulate_single(
            step=0.01,
            target=0.05,
            strategy_instance=strategy,
            symbol="TQQQ",
            initial_cash=100_000.0,
            cost_model=model,
            risk_manager=__import__("src.risk_manager", fromlist=["RiskManager"]).RiskManager(),
        )
        # No sells should complete because the guard rejects all of them
        assert result.metrics["Trade Count"] == 0


# ---------------------------------------------------------------------------
# Integration test: live execution boundary
# ---------------------------------------------------------------------------

class TestLiveExecutionGuard:
    """Verify validate_sell is wired into submit_sell and apply_sell_fill."""

    def _make_loop(self):
        """Build a minimal LiveExecutionLoop with a mock broker and no store."""
        from src.config import (
            BacktestConfig,
            BacktestSection,
            GridConfig,
            LiveConfig,
            RiskConfig,
            StrategyConfig,
        )
        from src.live_execution import LiveExecutionLoop
        from src.size_calculators import FixedPortfolioPercentage

        config = BacktestConfig(
            strategy=StrategyConfig(strategy_id="test-strategy"),
            backtest=BacktestSection(symbol="TQQQ", initial_cash=100_000.0),
            grid=GridConfig(steps=(0.01,), profit_targets=(0.05,)),
            risk=RiskConfig(),
            live=LiveConfig(enabled=True, paper_trading=True),
        )
        strategy = FixedPortfolioPercentage(percentage=0.05)
        loop = LiveExecutionLoop(config, strategy, broker_factory=None)
        loop._started = True
        loop.runtime_state = __import__(
            "src.live_execution", fromlist=["RuntimeState"]
        ).RuntimeState.READY
        # Attach a mock broker directly
        loop.broker = MagicMock()
        loop.broker.submit_sell = MagicMock(return_value="broker-order-id")
        return loop

    def test_submit_sell_with_lot_passes_guard_and_calls_broker(self):
        """submit_sell with profitable lot calls broker.submit_sell exactly once."""
        loop = self._make_loop()
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.05)
        result = loop.submit_sell(10.0, 105.0, lot=lot, cost_model=ZeroCostModel())
        assert result == "broker-order-id"
        loop.broker.submit_sell.assert_called_once()

    def test_submit_sell_with_loss_lot_rejected_and_broker_not_called(self):
        """submit_sell with a loss-making scenario returns None without calling broker."""
        loop = self._make_loop()
        # buy at 100 with heavy buy_costs; sell at 100 will be a loss after cost allocation
        lot = _make_lot(buy_price=100.0, shares=10.0, profit_target=0.0, buy_costs=50.0)
        model = SlippageCommissionModel(commission_per_trade=10.0)
        result = loop.submit_sell(10.0, 100.0, lot=lot, cost_model=model)
        assert result is None
        loop.broker.submit_sell.assert_not_called()
        assert loop.no_loss_guard_violations == 1

    def test_submit_sell_without_lot_still_calls_broker_with_warning(self, caplog):
        """submit_sell without lot skips guard (backward compat) and logs warning."""
        import logging
        loop = self._make_loop()
        with caplog.at_level(logging.WARNING, logger="LiveExecution"):
            result = loop.submit_sell(10.0, 105.0)  # no lot= supplied
        assert result == "broker-order-id"
        assert "no-loss guard skipped" in caplog.text

    def test_apply_sell_fill_profitable_fill_increments_cash(self):
        """A profitable fill properly increments cash using SellEconomics proceeds."""
        loop = self._make_loop()
        lot = loop.ledger.register_buy("o1", "TQQQ", 100.0, 10.0, 0.05)
        order = SimpleNamespace(id="o1", filled_qty="10.0", filled_avg_price="105.0")
        new_cash, proceeds = loop.apply_sell_fill(
            order, lot, cash=1000.0, cost_model=ZeroCostModel()
        )
        # ZeroCostModel: effective = 105.0, costs = 0; net = 10 * 105 = 1050
        assert new_cash == pytest.approx(1000.0 + 1050.0)
        assert proceeds == pytest.approx(1050.0)
        assert loop.no_loss_guard_violations == 0

    def test_apply_sell_fill_loss_fill_records_violation(self):
        """A fill at a loss-making price records violation and still closes lot."""
        loop = self._make_loop()
        # buy at 100 with 0.1% profit target; sell fill at 99 is a loss
        lot = loop.ledger.register_buy("o2", "TQQQ", 100.0, 10.0, 0.001)
        # Artificially modify the lot to simulate a fill at a price below cost
        # We close the lot at 90 (clear loss)
        order = SimpleNamespace(id="o2", filled_qty="10.0", filled_avg_price="90.0")
        new_cash, proceeds = loop.apply_sell_fill(
            order, lot, cash=0.0, cost_model=ZeroCostModel()
        )
        # Should have processed the fill (recording reality)
        assert proceeds > 0  # some proceeds recorded
        # Violation counter incremented
        assert loop.no_loss_guard_violations == 1


# ---------------------------------------------------------------------------
# Single-guard contract: verify there is only ONE implementation
# ---------------------------------------------------------------------------

class TestSingleGuardContract:

    def test_only_one_no_loss_comparison_in_codebase(self, tmp_path):
        """No module other than src/ledger.py should contain the
        net_sell_proceeds < allocated_cost_basis comparison expression.

        The pattern searched is the actual comparison operator (not just the
        identifier), so docstrings and comments that reference the term but do
        not re-implement the guard are excluded.

        This test is a contract test: if a second implementation appears,
        this test fails and the developer must consolidate it into
        validate_sell.
        """
        import os

        # Search for the actual comparison expression, not just the identifier.
        # Docstrings and prose naturally mention net_sell_proceeds by name;
        # only an executable comparison reproduces the guard logic.
        pattern = "net_sell_proceeds <"
        root = os.path.join(os.path.dirname(__file__), "..")
        files_containing_pattern = []

        for dirpath, _dirnames, filenames in os.walk(root):
            # Skip test files, pycache, .git
            if any(skip in dirpath for skip in ["__pycache__", ".git", ".pytest_cache"]):
                continue
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        content = f.read()
                    if pattern in content:
                        rel = os.path.relpath(fpath, root)
                        files_containing_pattern.append(rel)
                except (OSError, UnicodeDecodeError):
                    pass

        # Only ledger.py and this test file itself may contain the comparison
        allowed = {
            os.path.join("src", "ledger.py"),
            os.path.join("tests", "test_task_7_15_no_loss_sell.py"),
        }
        unexpected = [f for f in files_containing_pattern if f not in allowed]
        assert unexpected == [], (
            f"Found net_sell_proceeds < comparison outside the canonical guard: {unexpected}. "
            "Consolidate into validate_sell in src/ledger.py."
        )
