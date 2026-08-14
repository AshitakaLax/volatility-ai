"""
Walk-forward validation. Task 5.1 (M1).

run_sweep picks a "best" combination by scoring against the exact
sample it's optimizing over -- a standard overfitting/data-snooping
setup, more consequential for a path-dependent, 3x-leveraged
instrument like TQQQ. WalkForwardRunner selects parameters on a
training window and scores them on a held-out test window that
selection never saw.

This is a first working version, following
implementation_task_specs.md Task 5.1's own given implementation
almost verbatim, per its own instruction #2 ("validate the winner-
extraction / re-run logic against the actual strategy_params_grid
dict shape once src/size_calculators.py is in view"): confirmed
against the real FixedPortfolioPercentage/run_sweep -- run_sweep
merges **params directly into each result row as columns (e.g.
allocation_pct=0.05), so {k: winner[k] for k in
strategy_params_grid[0].keys()} correctly reconstructs the winning
params dict by column name. No changes to that logic were needed.

Two additions beyond the given code, both required by the Walk-forward
fold contract immediately following it in the same task, not by the
Implementation section's code block itself:
- train_window/test_window/step must be positive (rejected otherwise)
  -- the fold contract's own "invalid/non-positive values are
  rejected", even though the contract calls these train_bars/
  test_bars/step_bars while the given code names them train_window/
  test_window/step. Kept the given code's own names (the concrete,
  literal implementation instruction) rather than renaming to match
  the more abstract contract section's wording.
- Fold boundaries reported in UTC -- the given code's fold_start is a
  bare integer bar offset, not a timestamp; added actual
  train_start/train_end/test_start/test_end timestamps pulled from
  full_data's own index (confirmed elsewhere in this codebase to
  always be UTC-aware) to satisfy "fold boundaries are ... reported
  in UTC" literally, not just as a bar count.
"""

from __future__ import annotations

import pandas as pd

from src.exceptions import ConfigurationError


class WalkForwardRunner:
    def __init__(
        self,
        controller_factory,
        train_window: int,
        test_window: int,
        step: int,
        anchored: bool = False,
    ):
        """controller_factory: callable(df_slice) -> OptimizationController,
        so each fold gets its own controller over the right data slice
        (also means a fresh AssetLotLedger/OMS/strategy per fold, per
        run_sweep's own existing per-combination isolation -- "strategy
        state is reset at the beginning of each fold" is already true
        by construction, nothing extra was needed for that)."""
        for value, name in ((train_window, "train_window"), (test_window, "test_window"), (step, "step")):
            if not (isinstance(value, int) and value > 0):
                raise ConfigurationError(f"{name} must be a positive integer, got {value!r}")
        self.controller_factory = controller_factory
        self.train_window = train_window
        self.test_window = test_window
        self.step = step
        self.anchored = anchored

    def run(
        self,
        full_data: pd.DataFrame,
        grid_steps,
        profit_targets,
        strategy_class,
        strategy_params_grid,
        rank_by: str = "Capital Velocity Index",
    ) -> pd.DataFrame:
        folds = []
        start = 0
        while start + self.train_window + self.test_window <= len(full_data):
            train_start = 0 if self.anchored else start
            train_slice = full_data.iloc[train_start : start + self.train_window]
            test_slice = full_data.iloc[start + self.train_window : start + self.train_window + self.test_window]

            train_controller = self.controller_factory(train_slice)
            train_results = train_controller.run_sweep(grid_steps, profit_targets, strategy_class, strategy_params_grid)
            winner = train_results.sort_values(by=rank_by, ascending=False).iloc[0]

            test_controller = self.controller_factory(test_slice)
            test_results = test_controller.run_sweep(
                [winner["Grid Step"]],
                [winner["Profit Target"]],
                strategy_class,
                [{k: winner[k] for k in strategy_params_grid[0].keys()}],
            )
            folds.append({
                "fold_start": start,
                "train_start": train_slice.index[0],
                "train_end": train_slice.index[-1],
                "test_start": test_slice.index[0],
                "test_end": test_slice.index[-1],
                **{f"train_{k}": v for k, v in winner.items()},
                **{f"test_{k}": v for k, v in test_results.iloc[0].items()},
            })
            start += self.step
        return pd.DataFrame(folds)
