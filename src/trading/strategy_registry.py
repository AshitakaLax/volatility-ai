"""
strategy_id -> sizing-strategy class.

src/config.py treats strategy_id as an opaque string precisely because
no registry existed; every caller that needed a class kept its own
mapping (cli.py had one, Run_Instructions documented another). Two
hand-maintained copies of the same table is exactly the drift this
module removes.

Keeping it in src/ rather than in cli.py matters for one reason: the
backtest entrypoint, the live loop, and the sweep tooling must all
resolve a strategy_id the same way. A registry that lived in the CLI
would be unavailable to anything importing the library directly, and
the copy that grew to fill the gap would be free to disagree.
"""

from __future__ import annotations

from src.strategies.bayesian_sizing_calculators import BayesianDualScaleSizing
from src.core.exceptions import ConfigurationError
from src.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.ml.reachability_sizing import MLReachabilitySizing
from src.ml.regime_scaled_sizing import MLRegimeScaledSizing
from src.strategies.size_calculators import (
    BellCurveProbabilitySizing,
    FixedPortfolioPercentage,
    RsiMomentumSizing,
    SizingStrategy,
)

STRATEGIES: dict[str, type[SizingStrategy]] = {
    "fixed": FixedPortfolioPercentage,
    "bell_curve": BellCurveProbabilitySizing,
    "rsi": RsiMomentumSizing,
    "bayesian_dual_scale": BayesianDualScaleSizing,
    "hf_local_reference": HighFrequencyLocalReferenceSizing,
    # Three ids, one class: MLReachabilitySizing takes `ticker` as a
    # constructor kwarg, and each id's STRATEGY_DEFAULTS entry
    # (server/backtest.py) supplies a different one. The sizing-model
    # dropdown has no per-run field editor -- it always submits exactly
    # a strategy's committed defaults (see ParameterForm.tsx) -- so the
    # ticker has to be chosen by WHICH id is picked, not by a value
    # typed into a form. optimization_controller.py separately checks
    # the chosen id's .ticker against the fund actually being simulated
    # and refuses a mismatch, the same way it already does for
    # BayesianDualScaleSizing's target_return.
    #
    # Only COWZ showed a measured, fold-consistent lift over the
    # bar-only baseline (ml_plan.md, "Ablation by block"); RSP and SPYD
    # are offered to test against, not because they are proven --
    # server/backtest.py's /funds response and the UI both say so.
    "ml_reachability_rsp": MLReachabilitySizing,
    "ml_reachability_cowz": MLReachabilitySizing,
    "ml_reachability_spyd": MLReachabilitySizing,
    # Same one-id-per-ticker convention, same reason: MLRegimeScaledSizing
    # takes `ticker` as a constructor kwarg, the sizing-model dropdown
    # submits a strategy's committed defaults with no per-run field
    # editor, so WHICH id is picked is the only thing that can select
    # the model -- and .ticker is checked against the simulated symbol
    # in optimization_controller.py.
    #
    # UNMEASURED. Unlike the reachability ids above, none of these has
    # been through a sweep, a walk-forward, or a paired test against
    # hf_local_reference. They are registered so they can BE measured;
    # see src/ml/regime_scaled_sizing.py's "UNMEASURED AS OF THIS
    # COMMIT" note before putting one in a `live:` config.
    "ml_regime_tqqq": MLRegimeScaledSizing,
    "ml_regime_qqq": MLRegimeScaledSizing,
    "ml_regime_rsp": MLRegimeScaledSizing,
    "ml_regime_soxl": MLRegimeScaledSizing,
    "ml_regime_sqqq": MLRegimeScaledSizing,
    "ml_regime_spyd": MLRegimeScaledSizing,
    "ml_regime_xbi": MLRegimeScaledSizing,
    "ml_regime_cowz": MLRegimeScaledSizing,
    "ml_regime_ursp": MLRegimeScaledSizing,
}


def resolve_strategy(strategy_id: str) -> type[SizingStrategy]:
    """Look up a strategy class, or fail naming the valid options.

    Raises ConfigurationError rather than KeyError so a typo'd
    strategy_id surfaces through the same domain-exception path as
    every other configuration mistake, and so the message can list what
    IS available -- a bare KeyError names only what is missing.
    """
    try:
        return STRATEGIES[strategy_id]
    except KeyError:
        known = ", ".join(sorted(STRATEGIES))
        raise ConfigurationError(
            f"Unknown strategy_id {strategy_id!r}. Known strategies: {known}"
        ) from None
