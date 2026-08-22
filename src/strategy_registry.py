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

from src.bayesian_sizing_calculators import BayesianDualScaleSizing
from src.exceptions import ConfigurationError
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.size_calculators import (
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
