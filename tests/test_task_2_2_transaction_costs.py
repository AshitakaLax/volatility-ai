import pytest

from src.transaction_cost_model import (
    SlippageCommissionModel,
    TransactionCosts,
    ZeroCostModel,
)


def test_zero_cost_model_preserves_baseline():
    costs = ZeroCostModel().calculate(10.0, 100.0, "BUY")
    assert costs == TransactionCosts()
    assert costs.total == 0.0


def test_slippage_commission_model_calculates_costs_from_notional():
    model = SlippageCommissionModel(slippage_pct=0.001, commission_pct=0.0005)
    costs = model.calculate(10.0, 100.0, "BUY")
    assert costs.slippage == pytest.approx(1.0)
    assert costs.commission == pytest.approx(0.5)
    assert costs.total == pytest.approx(1.5)


def test_cost_model_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        SlippageCommissionModel(slippage_pct=-0.01)
    with pytest.raises(ValueError):
        SlippageCommissionModel().calculate(0.0, 100.0, "BUY")
    with pytest.raises(ValueError):
        SlippageCommissionModel().calculate(1.0, 100.0, "HOLD")
