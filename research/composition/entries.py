"""
Buy policies: when to buy and how much, as the `buy` half of a
ComposedStrategy.

A buy policy here is a REGISTERED STRATEGY used for its buying alone. The
composed strategy constructs the real strategy class with the given
parameters and calls only its buy side (record_tick, the grid trigger,
calculate_trade_value, next_lot_tag, warm-up); its sell hooks are never
called -- the sell policy answers those. That is what makes a pinned
identity possible: composed(X, fixed_target) is X's own code buying, not a
re-implementation that could drift from it.

Parameters that configure SELLING (trail_pct and its floor) are refused on
the buy side: they would be silently ignored there, and the run would not be
what its parameters say. Set them on a sell policy (`trailing`) instead.

Which strategies can be a buy policy is a deliberate list, not "all of
them": one whose buys and sells are entangled must first be split (Phase 4
of docs/research/buy-sell-composition.md -- Bayesian/ML's target_return
cross-checks, Ultimate's reversal lots, the exposure books).
"""

from __future__ import annotations

from typing import Any

from engine.core.exceptions import ConfigurationError

# Parameters that configure the strategy's SELLING, so mean nothing on the
# buy side of a composition (see the module docstring).
SELL_SIDE_PARAMS: frozenset[str] = frozenset({"trail_pct", "trail_min_profit_target"})

# Registered strategy ids whose buying stands alone. The library's rk* ids
# (LibrarySizing: hf_entry_gated plus one gate/sizer/level component, none of
# which sells) are added by entry_ids().
_STANDALONE: tuple[str, ...] = (
    "fixed",
    "rsi",
    "bell_curve",
    "hf_local_reference",
    "hf_entry_gated",
    "hf_signal_gated",
)


def entry_ids() -> tuple[str, ...]:
    """Every registered strategy id usable as a buy policy, in a stable order."""
    from research.strategies.library_sizing import LibrarySizing
    from research.strategies.strategy_registry import STRATEGIES

    library = sorted(i for i, c in STRATEGIES.items() if c is LibrarySizing)
    return (*_STANDALONE, *library)


def entry_class(entry_id: str) -> type:
    from research.strategies.strategy_registry import STRATEGIES

    if entry_id not in entry_ids():
        if entry_id in STRATEGIES:
            raise ConfigurationError(
                f"{entry_id} cannot be a buy policy yet: its buying and selling are not "
                "separated (docs/research/buy-sell-composition.md, Phase 4)."
            )
        raise ConfigurationError(f"Unknown buy policy {entry_id!r}.")
    return STRATEGIES[entry_id]


def entry_defaults(entry_id: str) -> dict[str, Any]:
    """The committed defaults of the strategy, less anything that sells."""
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    return {
        k: v for k, v in STRATEGY_DEFAULTS.get(entry_id, {}).items() if k not in SELL_SIDE_PARAMS
    }


def build_entry(entry_id: str, params: dict) -> Any:
    """The strategy behind a buy policy, constructed for its buying."""
    cls = entry_class(entry_id)
    selling = sorted(k for k, v in params.items() if k in SELL_SIDE_PARAMS and v is not None)
    if selling:
        raise ConfigurationError(
            f"{', '.join(selling)} configure selling, not buying: set them on the sell policy "
            "(e.g. `trailing`), not on the buy policy."
        )
    try:
        return cls(**params)
    except TypeError as exc:
        raise ConfigurationError(f"buy policy {entry_id} refused these parameters: {exc}") from exc
