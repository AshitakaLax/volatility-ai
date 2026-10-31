"""
strategy_id -> sizing-strategy class.

src/config.py treats strategy_id as an opaque string precisely because
no registry existed; every caller that needed a class kept its own
mapping (cli.py had one, docs/Run_Instructions documented another). Two
hand-maintained copies of the same table is exactly the drift this
module removes.

Keeping it in src/ rather than in cli.py matters for one reason: the
backtest entrypoint, the live loop, and the sweep tooling must all
resolve a strategy_id the same way. A registry that lived in the CLI
would be unavailable to anything importing the library directly, and
the copy that grew to fill the gap would be free to disagree.
"""

from __future__ import annotations

from engine.core.exceptions import ConfigurationError
from research.composition.composed_strategy import ComposedStrategy
from research.ml.reachability_sizing import MLReachabilitySizing
from research.ml.regime_scaled_sizing import MLRegimeScaledSizing
from research.strategies.bayesian_sizing_calculators import BayesianDualScaleSizing
from research.strategies.catalog_exposure_sizing import CatalogExposureSizing
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from research.strategies.library_sizing import LibrarySizing, library_strategy_ids
from research.strategies.signal_gated_sizing import SignalGatedSizing
from research.strategies.size_calculators import (
    BellCurveProbabilitySizing,
    FixedPortfolioPercentage,
    RsiMomentumSizing,
    SizingStrategy,
)
from research.strategies.ultimate_rsp_sizing import UltimateRspSizing
from research.strategies.ultimate_sizing import UltimateSizing
from research.strategies.ultimate_ursp_sizing import UltimateUrspSizing

STRATEGIES: dict[str, type[SizingStrategy]] = {
    "fixed": FixedPortfolioPercentage,
    "bell_curve": BellCurveProbabilitySizing,
    "rsi": RsiMomentumSizing,
    "bayesian_dual_scale": BayesianDualScaleSizing,
    "hf_local_reference": HighFrequencyLocalReferenceSizing,
    # The champion plus entry-suppression gates (breakdown / shooting
    # star). Both gates default "off", which is the champion exactly --
    # pinned by research/tests/test_gated_local_reference_sizing.py.
    # UNMEASURED: registered so config/probe_entry_gate_*.yaml can run.
    "hf_entry_gated": GatedLocalReferenceSizing,
    # hf_entry_gated plus the ranked list's single-symbol signal gates
    # (research/strategies/signal_gates.py: RK14, RK55, RK64, RK79, RK112,
    # RK147, RK161, RK168, RK208, RK243, RK253, RK294, RK297). Every new
    # gate defaults "off", which is hf_entry_gated exactly -- pinned by
    # research/tests/test_signal_gated_sizing.py. A separate id so the
    # traded hf_entry_gated is untouched. UNMEASURED.
    "hf_signal_gated": SignalGatedSizing,
    # The Ultimate algorithm (docs/research/ultimate-algorithm.md): the
    # champion grid while a causal NATR regime says calm, capitulation-
    # close event lots while it says turbulent, and the calm lots sold an
    # hour into the first turbulent session. Measured in the research lab
    # on TQQQ only (2016-12 to 2026-08: 29.7% CAGR, 13.7% max DD against
    # the champion's 25.7% / 42.2%), but its deflated Sharpe is not
    # significant and its PBO is high -- see that document's caveats
    # before a `live:` config. The regime exit is a sale below cost, so
    # it needs execution.allow_signal_exit (server/backtest.py turns it
    # on for this id; config/ultimate_tqqq.yaml sets it), and the
    # regime needs ~250 sessions of history (UltimateSizing.warm_up).
    "ultimate": UltimateSizing,
    # Ultimate-RSP (docs/research/ultimate-rsp.md): not a grid. A daily
    # exposure target for RSP from two uncorrelated vote families --
    # PLUS_DM (upside volatility) and Chaikin ADOSC (money flow), each
    # below its own trailing median, averaged over their parameters --
    # reached once a session an hour after the open. Research-lab
    # result on RSP 2017-2026: 11.2% CAGR at an 11.9% max drawdown
    # against buy-and-hold's 12.0% at 39.1%; out of sample (2022-26)
    # the family's Calmar held at ~0.9 against buy-and-hold's 0.40.
    # Its exits are signal exits (server/backtest.py turns them on for
    # this id), and its target needs ~300 sessions of history
    # (UltimateRspSizing.warm_up). RSP only.
    "ultimate_rsp": UltimateRspSizing,
    # Ultimate-URSP (docs/research/ultimate-ursp.md): Ultimate-RSP's daily
    # exposure book with a graded bear gate (out once the fund is 55% below
    # its one-year high, linear from 25%) and a 20% rebalance band, for
    # URSP (2x daily S&P 500 Equal Weight). Measured on a simulated URSP
    # 2004-2026 (tools/simulate_ursp.py): 11.7% CAGR at a 28% max DD
    # against buy-and-hold URSP's 11.2% at 88.5%. Signal exits on (server);
    # ~300 sessions of history (warm_up). URSP only.
    "ultimate_ursp": UltimateUrspSizing,
    # The research catalog's single-fund long-or-cash signals (Kalman, l1 and
    # spectral trend, KAMA, Supertrend, MACD, PSAR, TSMOM, tail-risk budgets,
    # ...: catalog_exposure_sizing.SIGNALS) on Ultimate-RSP's exposure book,
    # one signal per run by `catalog_signal`. Unlike the rk* library ids
    # (gates on the grid) it holds the whole position in or out. UNMEASURED:
    # none has been swept. Signal exits on (server), like the book it reuses.
    "catalog_exposure": CatalogExposureSizing,
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
    # bar-only baseline (docs/ml_plan.md, "Ablation by block"); RSP and SPYD
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
    # see research/ml/regime_scaled_sizing.py's "UNMEASURED AS OF THIS
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
    # Any buy algorithm with any sell policy (research/composition/,
    # docs/research/buy-sell-composition.md): strategy_params are
    # {buy: {id, params}, sell: {id, params}}. composed(X, fixed_target) is X
    # exactly (research/tests/test_composition.py). A sell policy that may
    # sell below cost still needs execution.allow_signal_exit, which
    # live_algorithm.check_live_support requires of a live config.
    "composed": ComposedStrategy,
}

# The ranked list's single-symbol algorithms, one id each: rk<ledger
# number>_<signal> (e.g. rk44_supertrend), all LibrarySizing with that
# algorithm's `signal` as the committed default (param_schema.py), so each
# is picked from the strategy list by name. Derived from the signal library
# rather than listed, so a new signal cannot be left unregistered.
# UNMEASURED: none of these has been swept.
STRATEGIES.update(dict.fromkeys(library_strategy_ids(), LibrarySizing))

# Strategies whose design includes an exit below cost basis. The flag is
# half of a two-part gate -- a loss needs execution.allow_signal_exit AND
# the strategy's lots_to_liquidate -- so it changes nothing for a strategy
# without the hook. UltimateSizing's regime exit (sell the calm-mode lots
# during the first turbulent session, L6) is the step-down the whole
# design was measured with; without the flag those lots ride the downturn
# and the run is a different, unresearched strategy. UltimateRspSizing's
# only exit is one: it moves to a daily exposure target by selling whole
# lots -- and so are UltimateUrspSizing's and CatalogExposureSizing's.
#
# server/backtest.py turns the flag on for these ids (it never trades).
# A live deployment must set it in its own file:
# research/strategies/live_algorithm.py refuses to start one without it.
SIGNAL_EXIT_STRATEGIES: frozenset[str] = frozenset(
    {"ultimate", "ultimate_rsp", "ultimate_ursp", "catalog_exposure"}
)


def may_realize_loss(strategy_id: str, params: dict | None = None) -> bool:
    """Whether a run of this strategy is designed to sell below cost, so
    needs execution.allow_signal_exit: the Ultimate family by id, a
    composition by its sell policy (any variant of a sweep)."""
    if strategy_id in SIGNAL_EXIT_STRATEGIES:
        return True
    ask = getattr(STRATEGIES.get(strategy_id), "can_realize_loss_for", None)
    return bool(ask(params or {})) if callable(ask) else False


def regular_session_only(strategy_class: type, params: dict | None = None) -> bool:
    """Whether a run of `strategy_class` (with these params, for one whose
    answer depends on them -- a composition asks its buy and sell sides) is
    built on regular-session bars."""
    ask = getattr(strategy_class, "regular_session_only_for", None)
    if callable(ask):
        return bool(ask(params or {}))
    return bool(getattr(strategy_class, "regular_session_only", False))


def session_bars(strategy_class: type, bars, params: dict | None = None):
    """The bars a backtest of `strategy_class` should see: all of them, or
    only the regular session's for a strategy built on those
    (`regular_session_only`: the Ultimate family). From a fund kept with
    extended hours (SQQQ, SPY, IWM, EEM) a pre-market or after-hours bar
    would fold into the session's range and shift its minutes; live,
    live_algorithm.check_live_support refuses the same mix."""
    if bars.empty or not regular_session_only(strategy_class, params):
        return bars
    from engine.data.historical_data import filter_regular_trading_hours

    kept, _ = filter_regular_trading_hours(bars)
    return kept


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
