import pandas as pd

from optimization_controller import OptimizationController


class RecordingStrategy:
    ticks = []

    def __init__(self, **kwargs):
        self.ticks = []
        RecordingStrategy.ticks = self.ticks

    def record_tick(self, current_price: float) -> None:
        self.ticks.append(float(current_price))

    def calculate_trade_value(self, total_equity: float, current_price: float, current_dd: float = 0.0) -> float:
        return 0.0


def test_record_tick_called_once_for_every_bar():
    data = pd.DataFrame(
        {"close": [100.0, 99.0, 98.0, 101.0, 100.0]},
        index=pd.date_range("2024-01-01", periods=5, freq="D"),
    )

    controller = OptimizationController(data)
    controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=RecordingStrategy,
        strategy_params_grid=[{}],
    )

    assert RecordingStrategy.ticks == [100.0, 99.0, 98.0, 101.0, 100.0]
    assert len(RecordingStrategy.ticks) == len(data)
