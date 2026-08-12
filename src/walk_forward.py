"""Walk-forward evaluation for out-of-sample strategy validation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Type

import pandas as pd

from src.exceptions import ConfigurationError
from src.size_calculators import SizingStrategy


class WalkForwardRunner:
    """Select parameters on contiguous training windows and test them out of sample."""

    def __init__(
        self,
        controller_factory: Callable[[pd.DataFrame], object],
        train_window: int,
        test_window: int,
        step: int,
        anchored: bool = False,
    ) -> None:
        self.train_window = self._positive_int("train_window", train_window)
        self.test_window = self._positive_int("test_window", test_window)
        self.step = self._positive_int("step", step)
        if not callable(controller_factory):
            raise ConfigurationError(
                f"controller_factory must be callable; got {controller_factory!r}"
            )
        self.controller_factory = controller_factory
        self.anchored = bool(anchored)

    @staticmethod
    def _positive_int(name: str, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigurationError(f"{name} must be a positive integer; got {value!r}")
        return value

    @staticmethod
    def _winner_params(winner: pd.Series, strategy_params_grid: list[dict]) -> dict:
        keys: list[str] = []
        for candidate in strategy_params_grid:
            for key in candidate:
                if key not in keys:
                    keys.append(key)
        missing = [key for key in keys if key not in winner.index]
        if missing:
            raise ConfigurationError(
                f"training winner is missing strategy parameter columns: {missing!r}"
            )
        return {key: winner[key] for key in keys}

    def run(
        self,
        full_data: pd.DataFrame,
        grid_steps,
        profit_targets,
        strategy_class: Type[SizingStrategy],
        strategy_params_grid: list[dict],
        rank_by: str = "Capital Velocity Index",
    ) -> pd.DataFrame:
        if not isinstance(full_data, pd.DataFrame):
            raise ConfigurationError(f"full_data must be a pandas DataFrame; got {type(full_data).__name__}")
        if len(full_data) < self.train_window + self.test_window:
            raise ConfigurationError(
                "full_data is too short for one walk-forward fold: "
                f"need at least {self.train_window + self.test_window} bars, got {len(full_data)}"
            )
        if not strategy_params_grid:
            raise ConfigurationError("strategy_params_grid must contain at least one parameter mapping")

        folds: list[dict] = []
        start = 0
        fold_number = 0
        while start + self.train_window + self.test_window <= len(full_data):
            train_start = 0 if self.anchored else start
            train_end = start + self.train_window
            test_end = train_end + self.test_window
            train_slice = full_data.iloc[train_start:train_end].copy()
            test_slice = full_data.iloc[train_end:test_end].copy()

            train_controller = self.controller_factory(train_slice)
            train_results = train_controller.run_sweep(
                grid_steps,
                profit_targets,
                strategy_class,
                strategy_params_grid,
                rank_by=rank_by,
            )
            if train_results.empty:
                raise ConfigurationError(f"walk-forward fold {fold_number} produced no training results")
            if rank_by not in train_results.columns:
                raise ConfigurationError(
                    f"rank_by {rank_by!r} is absent from training results; available columns: {list(train_results.columns)!r}"
                )
            valid_train = train_results[train_results[rank_by].notna()]
            if valid_train.empty:
                raise ConfigurationError(f"walk-forward fold {fold_number} has no valid training result for {rank_by!r}")
            winner = valid_train.iloc[0]
            winner_params = self._winner_params(winner, strategy_params_grid)

            test_controller = self.controller_factory(test_slice)
            test_results = test_controller.run_sweep(
                [winner["Grid Step"]],
                [winner["Profit Target"]],
                strategy_class,
                [winner_params],
                rank_by=rank_by,
            )
            if len(test_results) != 1:
                raise ConfigurationError(
                    f"walk-forward fold {fold_number} expected one test result, got {len(test_results)}"
                )

            train_record = {f"train_{k}": v for k, v in winner.items()}
            test_record = {f"test_{k}": v for k, v in test_results.iloc[0].items()}
            folds.append(
                {
                    "fold": fold_number,
                    "fold_start": start,
                    "train_start": train_slice.index[0],
                    "train_end": train_slice.index[-1],
                    "test_start": test_slice.index[0],
                    "test_end": test_slice.index[-1],
                    **train_record,
                    **test_record,
                }
            )
            fold_number += 1
            start += self.step

        return pd.DataFrame(folds)
