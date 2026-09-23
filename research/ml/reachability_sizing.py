"""Scale a grid buy by a model's confidence the target is reachable.

--------------------------------------------------------------------
WHAT THIS DOES, AND -- MORE IMPORTANTLY -- WHAT IT DOES NOT

This changes ONE thing: how much a confirmed grid buy is worth. It does
not decide WHETHER to buy (the grid trigger is untouched -- see "the
stranding risk" below), it cannot move a profit target
(adjust_profit_target is not overridden, so it stays at the base
class's default of None-for-every-lot), and it cannot sell anything
(lots_to_liquidate is not overridden either). Composed with
_BaselineScaledStrategy the same way RsiMomentumSizing and
BellCurveProbabilitySizing already are: confidence can only SHRINK a
position toward zero, never grow it past max_trade_pct. A model that is
wrong about a low-confidence bar costs foregone size, never oversizes a
mistake -- consistent with every other model-driven strategy in
src/size_calculators.py, and the right default for three funds whose
entire purpose (per the plan this was built against) is reducing risk,
not maximising a confident bet.

--------------------------------------------------------------------
THE STRANDING RISK IS NOT NEW, AND NOT ADDRESSED HERE

Grid re-triggering uses SizingStrategy's DEFAULT trigger
(last_buy_price * (1 - step)), which only ratchets down -- the same
formula `fixed`, `bell_curve`, `rsi` and `bayesian_dual_scale` all use,
and the same one this project measured stranding 4 of 5 strategies for
a decade on a persistently rising TQQQ/SOXL (see
tools/simulate_full_length.py's own docstring). hf_local_reference is
the one exception, via a rolling local reference this strategy does not
share. This strategy is exactly as exposed to that failure mode as the
other four defaults are, and is not claimed to be better. Pairing this
sizing model with a rolling-reference trigger is a real follow-up, not
done here.

--------------------------------------------------------------------
WHY predicted probability MAPS DIRECTLY TO THE MULTIPLIER

The measured evidence is not strong enough to justify a cleverer
calibration curve: the persisted model's held-out AUCs
(tools/train_ml_model.py's measured_test_auc, ~0.57-0.60) mean it is
weakly informative, not sharply discriminating. A linear map from
predicted probability to a [confidence_floor, 1.0] multiplier is the
simplest thing that uses the signal in the direction it was measured
(higher predicted P(reach target) -> closer to full size) without
inventing precision the evidence does not support.

--------------------------------------------------------------------
THIS IS SLOWER THAN EVERY OTHER STRATEGY IN THIS PROJECT, MEASURED

~600us per bar (~360 for the 36-feature vector, ~200 for the model
call), against roughly 23us/bar for this project's other strategies
(inferred from "one engine run is ~23 seconds" over ~1M bars elsewhere
in this codebase's own notes). A full-length run is minutes, not
seconds -- the UI's "everything (slow)" label was written for the
other strategies' definition of slow. Selecting the fastest
inference-time win available (predict(..., num_threads=1,
validate_features=False), worth ~25% of the model-call cost) was
judged worthwhile; rewriting IncrementalBarFeatures for raw throughput
was not, given the measured signal it feeds is itself weak -- see
ml_plan.md's own AUC numbers before spending more effort on speed than
the thing being sped up currently earns.

--------------------------------------------------------------------
ONE MODEL, ONE TICKER -- ENFORCED, NOT ASSUMED

Loaded lazily on the first record_tick (see ensure_model_available),
and `ticker` is a plain attribute a caller can read back. Analogous to
BayesianDualScaleSizing's target_return: optimization_controller.py
checks it against the symbol actually being simulated and refuses the
combination on a mismatch, for the identical reason that class's own
docstring gives -- a mismatch would have this confidently answering a
question about a different instrument's price action.

Lazy for the same reason MLRegimeScaledSizing is lazy:
constructing a sizing strategy is not only something a RUN does.
server/backtest.py's build_config() instantiates every submitted
strategy to validate it, and server/tests/test_server_api.py constructs
every registered strategy from STRATEGY_DEFAULTS just to prove the
dropdown's defaults work. Requiring trained binaries under gitignored
data/ml/models (plus the volatility-block files LiveFeatureSource
needs under data/external/) in order to construct -- or to draw a
number field -- is the wrong coupling, and it is a latent failure on
any fresh clone or CI runner that has not run
tools/train_ml_model.py / tools/fetch_market_inputs.py. What stays
front-loaded is every numeric argument check; what moves is only the
disk read. A live deployment catches a missing artifact via
tools/preflight.py before trading, and a run catches it on its first
bar rather than silently trading as a plain grid.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.ml.live_features import LiveFeatureSource
from research.strategies.size_calculators import _BaselineScaledStrategy
from research.strategies.sizing_indicators import clamp

_LABEL = "reached_t0.5_h390"


def _load_model(ticker: str, model_dir: Path) -> tuple[Any, dict]:
    try:
        import lightgbm as lgb
    except ImportError as exc:
        # This is the one class in src/ that needs it, and it is
        # deliberately absent from requirements.txt (see
        # requirements-ml.txt's own docstring: the live loop and the
        # Raspberry Pi that runs it must never NEED it to start).
        # Importing it lazily, here, means merely importing this module
        # -- which src/strategy_registry.py does unconditionally -- does
        # not require it; only actually USING this strategy does.
        # Checked BEFORE the artifact files exist so a machine without
        # requirements-ml.txt gets the actionable dependency error
        # rather than a missing-file error it cannot act on without the
        # dependency installed first.
        raise ConfigurationError(
            "MLReachabilitySizing needs lightgbm, which is not installed. Run: "
            "pip install -r requirements-ml.txt"
        ) from exc
    model_path = model_dir / f"{ticker}_{_LABEL}.txt"
    meta_path = model_dir / f"{ticker}_{_LABEL}.json"
    if not model_path.exists() or not meta_path.exists():
        raise ConfigurationError(
            f"MLReachabilitySizing: no trained model for {ticker!r} under {model_dir}. Run: "
            f"python tools/train_ml_model.py --tickers {ticker}"
        )

    booster = lgb.Booster(model_file=str(model_path))
    metadata = json.loads(meta_path.read_text())
    return booster, metadata


class MLReachabilitySizing(_BaselineScaledStrategy):
    """max_trade_pct, scaled down when the model is less confident the
    grid's profit target is reachable within the label's horizon."""

    def __init__(
        self,
        max_trade_pct: float,
        ticker: str,
        confidence_floor: float = 0.25,
        model_dir: str = "data/ml/models",
        external_dir: str | None = None,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        super().__init__(max_trade_pct, baseline_price, inverse_scale_kappa)
        if not 0.0 <= confidence_floor <= 1.0:
            raise ConfigurationError(f"confidence_floor must be in [0, 1], got {confidence_floor}")
        if not ticker:
            raise ConfigurationError("MLReachabilitySizing requires ticker (e.g. 'COWZ')")

        self.ticker = ticker
        self.confidence_floor = confidence_floor
        # Loaded lazily -- see ensure_model_available. Constructing must
        # not touch data/ml/models or data/external, so that validation
        # (server/backtest.py build_config), introspection
        # (describe_params via inspect.signature), and the defaults
        # construction test all work on a machine without trained
        # artifacts. The first record_tick loads, and tools/preflight.py
        # is where a live deployment fails fast before trading.
        self._model_dir = Path(model_dir)
        self._external_dir = external_dir
        self._booster: Any | None = None
        self.metadata: dict = {}
        self._feature_order: list[str] = []
        self._features: LiveFeatureSource | None = None
        self._last_probability: float | None = None

    def ensure_model_available(self) -> Any:
        """Load the model now, raising ConfigurationError if it is absent.

        Called on the first record_tick, and callable directly by a
        startup check that wants the failure BEFORE a session begins
        rather than on its first bar -- which is what tools/preflight.py
        is for. Idempotent.
        """
        if self._booster is None:
            booster, metadata = _load_model(self.ticker, self._model_dir)
            self._booster = booster
            self.metadata = metadata
            self._feature_order = list(metadata["feature_columns"])
            self._features = LiveFeatureSource(external_directory=self._external_dir)
        assert self._booster is not None and self._features is not None
        return self._booster

    def record_tick(self, context: MarketContext) -> None:
        self._capture_baseline(context.price)
        self.ensure_model_available()
        assert self._features is not None
        vector = self._features.record(context.timestamp, context.high, context.low, context.close)
        row = np.array([[vector[name] for name in self._feature_order]], dtype=np.float64)

        if np.isnan(row).all():
            # The very first bar of a run: nothing has been observed
            # yet, and a prediction made from zero information is not
            # one worth trusting over the conservative floor.
            self._last_probability = None
            return
        # LightGBM routes a missing feature down a learned default split
        # direction rather than needing it imputed -- a partial NaN row
        # (e.g. the volatility block not printed yet) is handled by the
        # model itself, not specially here.
        #
        # num_threads=1: this is ONE row. The thread-pool dispatch
        # LightGBM otherwise sets up per call is pure overhead here,
        # measured at ~25% of this call's cost with it left at its
        # training-time default of 4. validate_features=False skips
        # re-checking the column count against the model's own record
        # of it on every single bar -- this class already enforces that
        # by construction (self._feature_order comes from the same
        # metadata file the booster was saved next to).
        self._last_probability = float(
            self._booster.predict(row, num_threads=1, validate_features=False)[0]
        )

    def _model_multiplier(self, context: MarketContext) -> float:
        if self._last_probability is None:
            return self.confidence_floor
        return clamp(self._last_probability, self.confidence_floor, 1.0)


__all__ = ["MLReachabilitySizing"]
