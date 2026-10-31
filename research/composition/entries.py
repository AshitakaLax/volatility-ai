"""
Buy policies: when to buy and how much, as the `buy` half of a
ComposedStrategy.

A buy policy here is a STRATEGY used for its buying alone. The composed
strategy constructs the real strategy class with the given parameters and
calls only its buy side (record_tick, the grid trigger,
calculate_trade_value, next_lot_tag, warm-up); its sell hooks answer
nothing -- the sell policy does. That is what makes a pinned identity
possible: composed(X, its own sells) is X's own code, not a re-implementation
that could drift from it.

PARAMETERS THAT CONFIGURE SELLING are refused on the buy side unless left at
their constructor default: they would be silently ignored there, and the run
would not be what its parameters say. Set them on a sell policy instead
(trail_pct on `trailing`, a target decay on `age_decay`, Ultimate's regime
exit on `ultimate_exit`).

A BUYER THAT READS ITS LOTS. Ultimate limits its reversal buys by how many
reversal lots are open, which it learns in its own adjust_profit_target. Such
an entry is marked LOT_VIEW: the composed strategy still shows it the open
lots through its own wants_lot_retargeting / adjust_profit_target /
retain_lots, for its bookkeeping only -- any target it returns is discarded,
because targets are the sell policy's.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from engine.core.exceptions import ConfigurationError
from research.strategies.ultimate_sizing import TURBULENT, UltimateSizing

# Parameters that configure SELLING on every strategy that has them.
SELL_SIDE_PARAMS: frozenset[str] = frozenset({"trail_pct", "trail_min_profit_target"})


@dataclass(frozen=True)
class EntrySpec:
    """One buy policy: which class buys, and which of its parameters sell."""

    cls_path: str
    sell_params: frozenset[str] = SELL_SIDE_PARAMS
    lot_view: bool = False
    defaults_from: str | None = None  # a STRATEGY_DEFAULTS key to seed from

    def load(self) -> type:
        module, name = self.cls_path.rsplit(".", 1)
        return getattr(__import__(module, fromlist=[name]), name)


_HF = "research.strategies.high_frequency_sizing.HighFrequencyLocalReferenceSizing"

# Registered strategy ids whose buying stands alone, by the class to build.
# The library's rk* ids (LibrarySizing) are added by entry_ids().
_SPECS: dict[str, EntrySpec] = {
    "fixed": EntrySpec("research.strategies.size_calculators.FixedPortfolioPercentage"),
    "rsi": EntrySpec("research.strategies.size_calculators.RsiMomentumSizing"),
    "bell_curve": EntrySpec("research.strategies.size_calculators.BellCurveProbabilitySizing"),
    "hf_local_reference": EntrySpec(_HF),
    "hf_entry_gated": EntrySpec(
        "research.strategies.gated_local_reference_sizing.GatedLocalReferenceSizing"
    ),
    "hf_signal_gated": EntrySpec("research.strategies.signal_gated_sizing.SignalGatedSizing"),
    "bayesian_dual_scale": EntrySpec(
        "research.strategies.bayesian_sizing_calculators.BayesianDualScaleSizing"
    ),
    # The harvest sleeve's buying -- inventory decay and skew, the volatility
    # step, its session throttle and gates, the calm/turbulent sleeve -- with
    # its target decay and regime liquidation moved to sell policies.
    "harvest_sleeve": EntrySpec(
        "research.strategies.harvest_sleeve_sizing.HarvestSleeveSizing",
        sell_params=SELL_SIDE_PARAMS
        | {
            "target_decay_after_bars",
            "target_decay_span_bars",
            "target_floor",
            "target_decay_check_bars",
            "liquidate_minute",
            "liquidate_fraction",
        },
        defaults_from="hf_local_reference",
    ),
    # Ultimate's buying: the champion grid while calm, capitulation-close
    # reversal lots while turbulent (each tagged "reversal"). Its regime exit
    # and reversal target are `ultimate_exit`'s.
    "ultimate": EntrySpec(
        "research.composition.entries.UltimateEntry",
        sell_params=SELL_SIDE_PARAMS
        | {"liquidate_minute", "liquidate_reversal_on_calm", "reversal_target"},
        lot_view=True,
    ),
    # The exposure books' buying: whole lots up to a daily exposure target.
    # Their rebalancing sales are the *_rebalance sell policies.
    "ultimate_rsp": EntrySpec("research.strategies.ultimate_rsp_sizing.UltimateRspSizing"),
    "ultimate_ursp": EntrySpec("research.strategies.ultimate_ursp_sizing.UltimateUrspSizing"),
    "catalog_exposure": EntrySpec(
        "research.strategies.catalog_exposure_sizing.CatalogExposureSizing"
    ),
}

_ML_PREFIXES = ("ml_reachability_", "ml_regime_")


def _spec(entry_id: str) -> EntrySpec | None:
    from research.strategies.library_sizing import LibrarySizing
    from research.strategies.strategy_registry import STRATEGIES

    if entry_id in _SPECS:
        return _SPECS[entry_id]
    cls = STRATEGIES.get(entry_id)
    if cls is LibrarySizing or (cls is not None and entry_id.startswith(_ML_PREFIXES)):
        return EntrySpec(f"{cls.__module__}.{cls.__name__}")
    return None


def entry_ids() -> tuple[str, ...]:
    """Every buy policy, in a stable order: the named ones, then the library
    and ML ids."""
    from research.strategies.strategy_registry import STRATEGIES

    rest = sorted(i for i in STRATEGIES if i not in _SPECS and _spec(i) is not None)
    return (*_SPECS, *rest)


def entry_class(entry_id: str) -> type:
    spec = _spec(entry_id)
    if spec is None:
        from research.strategies.strategy_registry import STRATEGIES

        if entry_id in STRATEGIES:
            raise ConfigurationError(f"{entry_id} cannot be a buy policy.")
        raise ConfigurationError(f"Unknown buy policy {entry_id!r}.")
    return spec.load()


def sees_lots(entry_id: str) -> bool:
    spec = _spec(entry_id)
    return bool(spec and spec.lot_view)


def sell_params(entry_id: str) -> frozenset[str]:
    spec = _spec(entry_id)
    return spec.sell_params if spec else SELL_SIDE_PARAMS


def entry_defaults(entry_id: str) -> dict[str, Any]:
    """The committed defaults of the strategy, less anything that sells."""
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    spec = _spec(entry_id)
    key = spec.defaults_from if spec and spec.defaults_from else entry_id
    selling = sell_params(entry_id)
    return {k: v for k, v in STRATEGY_DEFAULTS.get(key, {}).items() if k not in selling}


def build_entry(entry_id: str, params: dict) -> Any:
    """The strategy behind a buy policy, constructed for its buying."""
    cls = entry_class(entry_id)
    signature = inspect.signature(cls.__init__).parameters
    selling = sorted(
        k
        for k, v in params.items()
        if k in sell_params(entry_id)
        and k in signature
        and v != signature[k].default
        and not (v is None and signature[k].default is inspect.Parameter.empty)
    )
    if selling:
        raise ConfigurationError(
            f"{', '.join(selling)} configure selling, not buying: set them on the sell policy "
            "(e.g. `trailing`, `age_decay`, `ultimate_exit`), not on the buy policy."
        )
    try:
        return cls(**params)
    except TypeError as exc:
        raise ConfigurationError(f"buy policy {entry_id} refused these parameters: {exc}") from exc


class UltimateEntry(UltimateSizing):
    """Ultimate, buying: tags each lot bought in turbulent mode "reversal"
    (Lot.entry_tag), so the sell side -- `ultimate_exit` or any other -- can
    tell reversal lots from grid lots without inferring it from a target
    value. A turbulent-mode buy is exactly the lot UltimateSizing itself
    classes as a reversal lot the bar after: then _mode_prev is that buy's
    mode, and a flip to turbulent cannot follow a turbulent bar."""

    def next_lot_tag(self) -> str | None:
        return "reversal" if self.mode == TURBULENT else None

    def resume(self, open_lots) -> None:
        lots = list(open_lots)
        super().resume(lots)
        self._reversal_ids |= {lot.order_id for lot in lots if lot.entry_tag == "reversal"}
