"""
The two engines that turn a training frame into daily return quantiles.

  chronos     Amazon Chronos-2, zero-shot, exactly as the pre-market forecast
              generator runs it: daily log returns (%) as the target, the
              frame's other columns as past covariates, the calendar columns
              also as known future covariates, nine quantiles (10%..90%) per
              session through the model's native horizon. It is an OPTIONAL
              dependency like the TFT (research/ml/tft_model.py): torch and
              chronos-forecasting come from requirements-dl.txt and are
              imported only when a forecast asks for this engine, so the
              server, the Pi image and the test suite import this module
              without them.
  bootstrap   The historical baseline the generator's walk-forward compares
              Chronos-2 against: every session's quantiles are the empirical
              quantiles of the fund's last five years of daily returns. No
              model, no torch -- what a host without requirements-dl.txt can
              still produce, and labelled as such in the report's `model`.

Neither is calibrated: Chronos-2 is zero-shot and has not been fine-tuned on
these funds. The report says so (snapshot notes; kelly_fraction_cap 0).
"""

from __future__ import annotations

import importlib.util
import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from research.forecast_generator.scenarios import QUANTILE_LEVELS

ENGINES = ("chronos", "bootstrap")
MODEL_ID = os.getenv("VAI_CHRONOS_MODEL", "amazon/chronos-2")
DEVICE = os.getenv("VAI_CHRONOS_DEVICE", "cpu")
CONTEXT_LENGTH = min(8192, int(os.getenv("VAI_CHRONOS_CONTEXT_LENGTH", "8192")))
NATIVE_HORIZON_DEFAULT = 64
# The generator's CHRONOS_DIRECT_HORIZON: Chronos-2 forecasts at most this many
# sessions directly, whatever its native horizon (chronos-forecasting 2.3
# reports 1,024), and scenarios.extend_daily_quantiles carries it to 252.
DIRECT_HORIZON = max(1, int(os.getenv("VAI_CHRONOS_DIRECT_HORIZON", "64")))
BOOTSTRAP_WINDOW = 1260

_MODEL: Any = None
_MODEL_LOCK = threading.Lock()


@dataclass(frozen=True)
class Quantiles:
    """Daily quantiles (steps x 9, percent log returns) and where they came from."""

    values: np.ndarray
    engine: str
    model: str
    direct_steps: int
    native_horizon: int


def chronos_available() -> tuple[bool, str]:
    """(whether the Chronos-2 engine can run here, why not)."""
    missing = [name for name in ("torch", "chronos") if importlib.util.find_spec(name) is None]
    if missing:
        return False, (
            f"{' and '.join(missing)} not installed: pip install -r requirements-dl.txt "
            "(torch, chronos-forecasting)"
        )
    return True, f"{MODEL_ID} on {DEVICE}" + (" (loaded)" if _MODEL is not None else "")


def _pipeline() -> Any:
    """The Chronos-2 pipeline, loaded once. The first load downloads the
    public weights from Hugging Face."""
    global _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            from chronos import Chronos2Pipeline

            _MODEL = Chronos2Pipeline.from_pretrained(MODEL_ID, device_map=DEVICE)
        return _MODEL


def chronos_quantiles(
    target: np.ndarray,
    past_covariates: Mapping[str, np.ndarray],
    future_covariates: Mapping[str, np.ndarray],
    steps: int,
    pipeline: Any | None = None,
) -> Quantiles:
    """Chronos-2's daily quantiles for the next `steps` sessions, at most
    DIRECT_HORIZON and its native horizon (scenarios.extend_daily_quantiles
    carries them further)."""
    model = pipeline if pipeline is not None else _pipeline()
    native = int(getattr(model, "model_prediction_length", NATIVE_HORIZON_DEFAULT))
    direct = max(1, min(steps, native, DIRECT_HORIZON))
    inputs = {
        "target": np.asarray(target, dtype=np.float32),
        "past_covariates": {k: np.asarray(v, dtype=np.float32) for k, v in past_covariates.items()},
        "future_covariates": {
            k: np.asarray(v, dtype=np.float32)[:direct] for k, v in future_covariates.items()
        },
    }
    quantiles, _mean = model.predict_quantiles(
        inputs=[inputs],
        prediction_length=direct,
        quantile_levels=QUANTILE_LEVELS.tolist(),
        context_length=min(CONTEXT_LENGTH, len(target)),
        limit_prediction_length=False,
    )
    first = quantiles[0]
    values = first.detach().cpu().numpy() if hasattr(first, "detach") else np.asarray(first)
    values = np.asarray(values, dtype=np.float64)
    # One target series: (1, steps, 9) -> (steps, 9).
    if values.ndim == 3:
        values = values[0]
    return Quantiles(
        values=values, engine="chronos", model=MODEL_ID, direct_steps=direct, native_horizon=native
    )


def bootstrap_quantiles(history_returns_pct: np.ndarray, steps: int) -> Quantiles:
    """The baseline: the last BOOTSTRAP_WINDOW sessions' empirical quantiles,
    the same for every step."""
    returns = np.asarray(history_returns_pct, dtype=np.float64)
    returns = returns[np.isfinite(returns)][-BOOTSTRAP_WINDOW:]
    if len(returns) < 60:
        raise ValueError("At least 60 daily returns are required for the historical baseline.")
    row = np.maximum.accumulate(np.quantile(returns, QUANTILE_LEVELS))
    return Quantiles(
        values=np.tile(row, (steps, 1)),
        engine="bootstrap",
        model="historical-bootstrap",
        direct_steps=steps,
        native_horizon=steps,
    )


__all__ = [
    "ENGINES",
    "MODEL_ID",
    "Quantiles",
    "bootstrap_quantiles",
    "chronos_available",
    "chronos_quantiles",
]
