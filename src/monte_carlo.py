"""Deterministic block-bootstrap Monte Carlo validation."""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np
import pandas as pd


class MonteCarloRunner:
    """Generate synthetic price paths with a contiguous-return block bootstrap."""

    def __init__(self, controller_factory: Callable[[pd.DataFrame], object]):
        self.controller_factory = controller_factory
        self.last_percentiles = pd.DataFrame()

    @staticmethod
    def _validate(data: pd.DataFrame, n_paths: int, block_size: int) -> None:
        if not isinstance(data, pd.DataFrame) or "close" not in data.columns:
            raise ValueError("historical data must contain a 'close' column")
        if n_paths <= 0:
            raise ValueError("n_paths must be positive")
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        returns = data["close"].astype(float).pct_change().dropna()
        if len(returns) < block_size:
            raise ValueError("insufficient observations for configured block_size")
        if data["close"].iloc[0] <= 0:
            raise ValueError("starting close must be positive")

    @staticmethod
    def _bootstrap_returns(returns: np.ndarray, length: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
        if length == 0:
            return np.empty(0, dtype=float)
        starts = np.arange(0, len(returns) - block_size + 1)
        pieces = []
        total = 0
        while total < length:
            start = int(rng.choice(starts))
            block = returns[start:start + block_size]
            pieces.append(block)
            total += len(block)
        return np.concatenate(pieces)[:length]

    @staticmethod
    def reconstruct_price_path(start_price: float, bootstrapped_returns: np.ndarray, index: pd.Index) -> pd.DataFrame:
        prices = start_price * np.cumprod(np.concatenate(([1.0], 1.0 + bootstrapped_returns)))
        return pd.DataFrame({"close": prices}, index=index)

    @staticmethod
    def percentile_summary(results: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for metric in ("CAGR", "Max Drawdown %", "Final Portfolio Value"):
            if metric not in results.columns:
                continue
            values = pd.to_numeric(results[metric], errors="coerce").dropna()
            if values.empty:
                continue
            rows.append({"metric": metric, **{f"p{p:02d}": float(np.percentile(values, p)) for p in (5, 25, 50, 75, 95)}})
        return pd.DataFrame(rows).set_index("metric") if rows else pd.DataFrame()

    def run(
        self,
        full_data: pd.DataFrame,
        n_paths: int,
        block_size: int,
        step: float,
        target: float,
        strategy_class,
        strategy_params,
        seed: Optional[int] = None,
    ) -> pd.DataFrame:
        self._validate(full_data, n_paths, block_size)
        returns = full_data["close"].astype(float).pct_change().dropna().to_numpy()
        root = np.random.SeedSequence(seed)
        child_sequences = root.spawn(n_paths)
        rows = []
        for iteration, child in enumerate(child_sequences):
            rng = np.random.default_rng(child)
            bootstrapped = self._bootstrap_returns(returns, len(returns), block_size, rng)
            synthetic = self.reconstruct_price_path(float(full_data["close"].iloc[0]), bootstrapped, full_data.index)
            controller = self.controller_factory(synthetic)
            result = controller.run_sweep(
                [step], [target], strategy_class, [strategy_params]
            )
            row = result.iloc[0].to_dict()
            row["iteration"] = iteration
            rows.append(row)
        output = pd.DataFrame(rows).sort_values("iteration", kind="mergesort").reset_index(drop=True)
        self.last_percentiles = self.percentile_summary(output)
        return output
