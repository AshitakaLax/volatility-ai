"""
Monte Carlo path simulation via block bootstrap. Task 5.2 (M2).

A single historical backtest is one point estimate; this resamples
the return series to show the distribution of outcomes a chosen
parameter combination might plausibly have produced, rather than just
the one sequence of returns that actually happened.

Monte Carlo contract (implementation_task_specs.md):
- Resampling unit: contiguous BLOCKS of the ordered daily return
  series (not individual days) -- preserves serial dependence/
  volatility clustering within a block. A per-observation bootstrap
  is explicitly rejected by that contract and not implemented here.
- Return source: simple returns (close-to-close pct change) computed
  from the input historical_data's own 'close' column.
- Block construction: block_size-length contiguous slices of the
  return series, block start positions drawn uniformly at random with
  replacement, concatenated and trimmed to exactly (n_bars - 1)
  resampled returns (one fewer than n_bars, since the first synthetic
  bar has no "return into it" -- it's the chosen starting price).
- Synthetic path reconstruction: starting from the input data's own
  first close, each subsequent synthetic close is the previous one
  compounded by the next resampled return.
- Seed handling: numpy.random.SeedSequence(seed).spawn(n_paths) gives
  each path an independent, deterministic child seed -- not the same
  seed reused n_paths times, per the contract's explicit requirement.
  Global numpy random state is never touched.
- Number of paths / percentile calculation: n_paths independent
  synthetic runs; 5th/25th/50th/75th/95th percentiles of CAGR, Max
  Drawdown %, and Final Equity computed across them via numpy.

Trade-order randomization, execution-cost perturbation, and parameter
perturbation are different techniques from block bootstrap and are
not substituted for it here, per the contract's own explicit warning.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.exceptions import ConfigurationError
from src.validation import validate_positive_int

PERCENTILES = (5, 25, 50, 75, 95)


def _block_bootstrap_returns(returns: np.ndarray, block_size: int, n_needed: int, rng: np.random.Generator) -> np.ndarray:
    """Resample `n_needed` returns as contiguous blocks, with replacement.

    Blocks rather than individual observations: drawing single days
    would destroy the serial correlation and volatility clustering that
    make a price path realistic, producing implausibly smooth synthetic
    histories.

    Raises ConfigurationError if block_size exceeds the available
    history, since not even one full block could be formed.
    """
    if len(returns) < block_size:
        raise ConfigurationError(
            f"block_size ({block_size}) exceeds available return observations ({len(returns)}) -- "
            "cannot form even one full block."
        )
    max_start = len(returns) - block_size
    n_blocks = -(-n_needed // block_size)  # ceil division
    starts = rng.integers(0, max_start + 1, size=n_blocks)
    blocks = [returns[s : s + block_size] for s in starts]
    return np.concatenate(blocks)[:n_needed]


def generate_synthetic_path(historical_data: pd.DataFrame, block_size: int, rng: np.random.Generator) -> pd.DataFrame:
    """One synthetic OHLCV path, same length and index as
    historical_data, built by block-bootstrapping historical_data's
    own close-to-close returns. Directly testable in isolation (not
    only through the full run() pipeline) so seed-determinism and
    the volatility-sensitivity acceptance criteria can be checked
    against actual price arrays, not just end-to-end summary output."""
    closes = historical_data["close"].to_numpy()
    n_bars = len(closes)
    returns = np.diff(closes) / closes[:-1]

    resampled_returns = _block_bootstrap_returns(returns, block_size, n_bars - 1, rng)

    synthetic_closes = np.empty(n_bars)
    synthetic_closes[0] = closes[0]
    synthetic_closes[1:] = closes[0] * np.cumprod(1 + resampled_returns)

    prev_close = np.concatenate(([closes[0]], synthetic_closes[:-1]))
    highs = np.maximum(prev_close, synthetic_closes) * 1.0015
    lows = np.minimum(prev_close, synthetic_closes) * 0.9985

    return pd.DataFrame(
        {
            "open": prev_close,
            "high": highs,
            "low": lows,
            "close": synthetic_closes,
            "volume": historical_data["volume"].to_numpy() if "volume" in historical_data.columns else 1_000_000,
        },
        index=historical_data.index,
    )


class MonteCarloRunner:
    """Runs a chosen parameter set across many resampled price paths.

    Answers "how else might this have gone" rather than "how did this
    go" -- a single backtest is one sample from a distribution, and this
    estimates the rest of that distribution.
    """

    def run(
        self,
        controller_factory,
        n_paths: int,
        block_size: int,
        step: float,
        target: float,
        strategy_class,
        strategy_params: dict,
        historical_data: pd.DataFrame,
        seed: Optional[int] = None,
        initial_cash: float = 100_000.0,
    ) -> pd.DataFrame:
        """Simulate n_paths synthetic histories; return percentile outcomes.

        Each path gets an independent child seed derived from `seed`, so
        results are reproducible without any two paths sharing a random
        stream. Returns 5th/25th/50th/75th/95th percentiles of CAGR,
        Max Drawdown %, and Final Equity.
        """
        validate_positive_int(n_paths, "n_paths")
        validate_positive_int(block_size, "block_size")

        seed_sequence = np.random.SeedSequence(seed)
        child_seeds = seed_sequence.spawn(n_paths)  # independent, deterministic per path

        cagrs, drawdowns, final_equities = [], [], []
        for child_seed in child_seeds:
            rng = np.random.default_rng(child_seed)
            path = generate_synthetic_path(historical_data, block_size, rng)

            controller = controller_factory(path)
            result = controller.run_sweep(
                grid_steps=[step],
                profit_targets=[target],
                strategy_class=strategy_class,
                strategy_params_grid=[strategy_params],
                initial_cash=initial_cash,
            ).iloc[0]

            final_equity = result["Final Equity"]
            years = (path.index[-1] - path.index[0]).days / 365.25
            cagr = (final_equity / initial_cash) ** (1.0 / years) - 1.0 if years > 0 else float("nan")

            cagrs.append(cagr)
            drawdowns.append(result["Max Drawdown %"])
            final_equities.append(final_equity)

        summary = pd.DataFrame(
            {
                "CAGR": np.percentile(cagrs, PERCENTILES),
                "Max Drawdown %": np.percentile(drawdowns, PERCENTILES),
                "Final Equity": np.percentile(final_equities, PERCENTILES),
            },
            index=pd.Index(PERCENTILES, name="percentile"),
        )
        return summary

    def generate_paths(
        self, historical_data: pd.DataFrame, n_paths: int, block_size: int, seed: Optional[int] = None
    ) -> list:
        """Path generation alone, without running any simulation --
        exposed directly for the seed-determinism acceptance criterion
        ("two runs produce identical resampled paths"), comparable as
        arrays without needing to run a full backtest sweep to check it."""
        validate_positive_int(n_paths, "n_paths")
        validate_positive_int(block_size, "block_size")
        seed_sequence = np.random.SeedSequence(seed)
        child_seeds = seed_sequence.spawn(n_paths)
        return [generate_synthetic_path(historical_data, block_size, np.random.default_rng(cs)) for cs in child_seeds]
