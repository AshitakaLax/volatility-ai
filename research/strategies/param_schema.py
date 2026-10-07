"""
Per-strategy parameters: the committed defaults, and a schema of every
constructor argument -- type, default, whether it is required, and which
ones the engine owns and an operator must not set.

Shared by the two places a person picks a strategy and its parameters:
the web UI's "Run a backtest" form (server/backtest.py, which re-exports
all of this under its old names) and the Fidelity Bridge extension's
algorithm editor for a live deployment (research/strategies/live_algorithm.py).
It lived in server/backtest.py until the second one needed it, and the
live trading process must not import the web stack.

Pure introspection over strategy classes: no I/O, no optional dependencies.
"""

from __future__ import annotations

import contextlib
import inspect
import sys
import types
from typing import Any, Union, get_args, get_origin, get_type_hints

# DEFAULTS FOR THE STRATEGIES THAT CANNOT BE CONSTRUCTED WITHOUT THEM.
#
# Only `fixed` has an all-optional constructor. Every other strategy has
# required arguments, and a UI that offered the dropdown without them
# submitted {} and produced a run that failed twenty seconds later with
# "rank_by column not found" -- which is what the caller sees when every
# combination errored and the summary has nothing but error rows. That
# is what happened.
#
# The values are lifted from this project's OWN committed configs, which
# are the parameter sets its sweeps actually selected, rather than
# invented here. Where a config sweeps a list, the single value below is
# one point from it: a starting position to run and adjust, not a claim
# about what is best.
STRATEGY_DEFAULTS: dict[str, dict[str, Any]] = {
    # config/production.yaml
    "fixed": {"allocation_pct": 0.05},
    # config/best_known_2026-08-24.yaml -- the champion parameter set.
    "hf_local_reference": {
        "bars_per_day": 387,
        "per_lot_pct": 0.0002,
        "lookback_days": 0.02,
        "vol_scale_exponent": -1.5,
        "vol_fast_days": 0.25,
        "vol_slow_days": 10.0,
        "vol_scale_min": 0.25,
        "vol_scale_max": 3.0,
        "volume_scale_exponent": -1.0,
    },
    # config/sweep_bell_curve_comparative.yaml, mid of each swept list.
    "bell_curve": {"max_trade_pct": 0.08, "lookback_days": 20, "bars_per_day": 387},
    # config/sweep_rsi_comparative.yaml
    "rsi": {"max_trade_pct": 0.08, "period": 14, "oversold_threshold": 30},
    # config/search_bayesian_deep.yaml
    "bayesian_dual_scale": {
        "max_trade_pct": 0.05,
        "target_return": 0.0075,
        "horizon_days": 1.0,
        "bars_per_day": 387,
    },
    # No committed config for these three -- there is no production
    # deployment of this strategy yet, only tools/train_ml_model.py's
    # own measured held-out AUC (RSP 0.60, COWZ 0.57, SPYD 0.57;
    # ml_plan.md, "Phase ML-0"). `ticker` is what makes these three
    # entries distinct rather than duplicates: MLReachabilitySizing
    # takes one shared class and a ticker kwarg, and the sizing-model
    # dropdown has no per-run field editor (it submits exactly a
    # strategy's committed defaults -- see ParameterForm.tsx), so
    # WHICH id is picked is what selects the ticker. Simulating a fund
    # that does not match costs a ConfigurationError naming the
    # mismatch, not a silent wrong answer (optimization_controller.py,
    # mirroring the existing target_return guard).
    "ml_reachability_rsp": {"max_trade_pct": 0.05, "ticker": "RSP", "confidence_floor": 0.25},
    "ml_reachability_cowz": {"max_trade_pct": 0.05, "ticker": "COWZ", "confidence_floor": 0.25},
    "ml_reachability_spyd": {"max_trade_pct": 0.05, "ticker": "SPYD", "confidence_floor": 0.25},
    # MLRegimeScaledSizing, one id per ticker for the identical reason.
    #
    # NO MEASURED NUMBER BACKS THESE DEFAULTS, unlike every other entry
    # in this table -- there is no committed config and no sweep result
    # to copy from, because the strategy has never been run. They are
    # STARTING POINTS chosen from adjacent measurements in this repo,
    # and each is stated so it can be argued with:
    #
    #   crash_step_multiplier 4.0  the 4% spacing
    #       tools/probe_downturn_tactics.py's escalating dip book used,
    #       against a 1% base step.
    #   regime_enter/exit 0.65/0.45  a wide band, because the models
    #       these read are weak (ml_plan.md: AUC 0.52-0.63) and a narrow
    #       band on a weak score is just flapping.
    #   vol_reference 0.45  roughly where an annualized 20-day realized
    #       vol sits near the 75th percentile that
    #       tools/probe_vol_filtered_regime.py measured its filter at.
    #       Instrument-specific -- XBI and COWZ do not share a vol
    #       regime, and this is the first parameter to re-derive per
    #       fund rather than inherit.
    #   drawdown_response 0.0  inert, following inverse_scale_kappa's
    #       opt-in convention. Turn it on deliberately, one direction at
    #       a time; see the strategy's own __init__ on the sign.
    # XBI: -8% over 10 sessions, 64tr/10te episodes, held-out AUC 0.7310
    # -- the THIRD fund to clear the moving-block-bootstrap significance
    # test (95% CI [0.575, 0.839], block-permutation p=0.031), and the
    # one with the most training episodes of any fund here.
    #
    # FETCHED AND TRAINED TO TEST A HYPOTHESIS, and it held. The other
    # seven funds cluster at ~20% annualized vol (3-10 deep-drawdown
    # episodes in a decade -- too few events to learn a crash from) or
    # ~65-100% (78-140 episodes, but leveraged, so decay strands lots
    # the no-loss guard can never sell -- SQQQ's sweep lost money on
    # every one of 80 trials with 9-28 stuck lots). XBI sits in the gap
    # at 32.8% vol with 61 episodes at -10%/20 sessions: enough events,
    # no leverage decay. Its drawdowns are also FDA/trial-driven rather
    # than pure market beta, so they are largely independent of the
    # 2018/2020/2022 events every other fund here shares.
    #
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.058-0.394 -- a 0.28-wide band, third widest here, so a threshold
    # sweep has room to differentiate rather than collapsing the way
    # COWZ's 0.008-wide range does); vol_reference is the fwdvol head's
    # p75. NOT yet swept -- ml_plan.md's bar (beat hf_local_reference)
    # is untested for this fund.
    "ml_regime_xbi": {
        "max_trade_pct": 0.05,
        "ticker": "XBI",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1874,
        "regime_exit_threshold": 0.1112,
        "regime_floor": 0.25,
        "vol_reference": 0.319,
    },
    # TQQQ: -25% over 20 sessions, 24tr/5te episodes, held-out AUC 0.7255.
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.073-0.285); vol_reference is the fwdvol head's p75.
    "ml_regime_tqqq": {
        "max_trade_pct": 0.05,
        "ticker": "TQQQ",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1757,
        "regime_exit_threshold": 0.0793,
        "regime_floor": 0.25,
        "vol_reference": 0.638,
    },
    # QQQ: -7% over 20 sessions, 52tr/14te episodes, held-out AUC 0.6748.
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.161-0.180); vol_reference is the fwdvol head's p75.
    "ml_regime_qqq": {
        "max_trade_pct": 0.05,
        "ticker": "QQQ",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1742,
        "regime_exit_threshold": 0.1610,
        "regime_floor": 0.25,
        "vol_reference": 0.218,
    },
    # RSP: -5% over 20 sessions, 46tr/10te episodes, held-out AUC 0.5369.
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.057-0.601); vol_reference is the fwdvol head's p75.
    "ml_regime_rsp": {
        "max_trade_pct": 0.05,
        "ticker": "RSP",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.4180,
        "regime_exit_threshold": 0.2286,
        "regime_floor": 0.25,
        "vol_reference": 0.172,
    },
    # SOXL: -30% over 20 sessions, 43tr/17te episodes, held-out AUC 0.7559
    # -- one of exactly two funds (with SQQQ, below) whose crash
    # classifier cleared a moving-block-bootstrap significance test
    # (95% CI [0.635, 0.859], p=0.001).
    #
    # THRESHOLDS ARE SWEEP-DERIVED, NOT HAND-PICKED, per
    # config/search_soxl_regime_bayesian.yaml -- an 80-trial Optuna TPE
    # search over this exact space, on the held-out 2024-01-01+ window
    # (261,248 bars), ranked by Return/Drawdown. The prior committed
    # values here (p90/p50 of the model's own quantiles: enter 0.331,
    # vol_reference 1.262) were the reasoned STARTING point the sweep
    # was built to test, not its answer -- the search never sampled that
    # exact combination and found a materially different one instead:
    # a markedly lower regime_enter_threshold (0.331 -> 0.20, latching
    # into the widened grid far more readily) paired with a lower
    # vol_reference (1.262 -> 0.9, damping size sooner as forecast vol
    # rises). Verified directly against the OLD defaults on the
    # identical window/engine: Sharpe 0.3715 vs 0.3503 (+6%), Sortino
    # 0.1679 vs 0.1504 (+12%), max drawdown 8.32% vs 12.22%, for lower
    # absolute return (4.52% vs 6.21%) and fewer trades (48 vs 54) --
    # the designed capital-preservation tradeoff, and both Sharpe and
    # Return/Drawdown rankings agree on this combination among the 80
    # trials, which is what makes it a real signal rather than a
    # rank_by artifact (see that config's own header on the failure
    # mode this guards against: near-zero-activity configs inflate
    # Return/Drawdown on almost no risk taken).
    #
    # STILL LOSES TO hf_local_reference ON THE SAME WINDOW (Sharpe 0.59
    # at this grid step) -- an improvement over this strategy's own
    # prior defaults, not a claim it beats the incumbent. See
    # research/ml/regime_scaled_sizing.py's "UNMEASURED" note; this sweep is
    # the measurement, and the answer is still "not yet."
    "ml_regime_soxl": {
        "max_trade_pct": 0.05,
        "ticker": "SOXL",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.20,
        "regime_exit_threshold": 0.166,
        "regime_floor": 0.25,
        "vol_reference": 0.9,
    },
    # SQQQ: -25% over 20 sessions, 41tr/8te episodes, held-out AUC
    # 0.8521 -- the stronger of the two significant funds (95% CI
    # [0.690, 0.987], p=0.001).
    #
    # THRESHOLDS UNCHANGED FROM THE MODEL'S OWN QUANTILES DELIBERATELY,
    # because the sweep that was supposed to improve on them
    # (config/search_sqqq_regime_bayesian.yaml, the same 80-trial
    # design as SOXL's, identical held-out window) found NO PROFITABLE
    # POINT ANYWHERE IN THIS SPACE. All 80 trials lost money -- Total
    # Return % ranged -29.57% to -7.42%, real trading activity throughout
    # (81-154 trades, not a near-zero-activity artifact), 9-28 open lots
    # stuck under the no-loss guard at the "best" (least-bad) trial. This
    # matches the paired simulation from the same session: ml_regime,
    # fixed, AND hf_local_reference were all negative on SQQQ post-cutoff.
    # SQQQ appears to have simply been a structural loser in this window
    # regardless of sizing strategy, not a hyperparameter problem --
    # replacing these with the "least-bad" sampled combination would
    # misrepresent a negative result as a tuned improvement, so they stay
    # at the quantile-derived starting point instead.
    "ml_regime_sqqq": {
        "max_trade_pct": 0.05,
        "ticker": "SQQQ",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1239,
        "regime_exit_threshold": 0.0935,
        "regime_floor": 0.25,
        "vol_reference": 0.689,
    },
    # SPYD: -5% over 20 sessions, 53tr/5te episodes, held-out AUC 0.3797.
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.200-0.268); vol_reference is the fwdvol head's p75.
    "ml_regime_spyd": {
        "max_trade_pct": 0.05,
        "ticker": "SPYD",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.2476,
        "regime_exit_threshold": 0.2248,
        "regime_floor": 0.25,
        "vol_reference": 0.182,
    },
    # COWZ IS THE ONE ENTRY HERE CALIBRATED AGAINST A REAL TRAINED
    # MODEL rather than guessed. data/ml/models/COWZ_regime_crash.json,
    # trained on 2016-12-19..2024-01-01 (1,768 sessions, 49 independent
    # episodes) at -5% over 20 sessions, held-out AUC 0.5987 over 7 test
    # episodes.
    #
    # The thresholds come straight off that model's score_quantiles and
    # could not have been guessed: its entire output range is
    # 0.106-0.114. enter = p90 (0.1090) latches the top decile;
    # exit = p50 (0.1063) releases at the median.
    #
    # THIS ENTRY HAS NOW BEEN WRONG TWICE, BOTH TIMES CAUGHT BY
    # _check_threshold_is_reachable RATHER THAN BY A BAD BACKTEST. First
    # a guessed 0.30 against a p99 of 0.218; then 0.211 left stale when
    # the label moved from -5% to -7% and the whole output range shifted
    # to 0.106-0.114. Retraining a model INVALIDATES these two
    # numbers -- they are properties of a specific artifact, not of the
    # fund.
    #
    # vol_reference 0.30 is still a guess -- the fwdvol head's own
    # output range should be read the same way before trusting it.
    "ml_regime_cowz": {
        "max_trade_pct": 0.05,
        "ticker": "COWZ",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1090,
        "regime_exit_threshold": 0.1063,
        "regime_floor": 0.25,
        "vol_reference": 0.181,
    },
    # UNVALIDATED PLACEHOLDER, AND CURRENTLY INFEASIBLE TO FIX. No
    # model exists at data/ml/models/URSP_regime_*; selecting this id
    # fails at ensure_model_available() with a clear ConfigurationError
    # naming that, per research/ml/regime_scaled_sizing.py's own lazy-load
    # design. Not just untrained: Alpaca's own history for URSP starts
    # 2025-08-27 (~260 sessions total, confirmed by fetching it), well
    # under the 250 TRAIN sessions alone every other fund's model
    # needed before any held-out test window -- there is currently not
    # enough history to train one, not merely a step skipped. Revisit
    # once the symbol has accumulated several more years.
    "ml_regime_ursp": {
        "max_trade_pct": 0.05,
        "ticker": "URSP",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.30,
        "regime_exit_threshold": 0.20,
        "regime_floor": 0.25,
        "vol_reference": 0.55,
    },
}
# hf_entry_gated: the champion's committed values with both gates off, so
# selecting it and changing nothing reproduces hf_local_reference. Derived
# from that entry rather than copied, so the two cannot drift apart.
STRATEGY_DEFAULTS["hf_entry_gated"] = dict(STRATEGY_DEFAULTS["hf_local_reference"])
# ultimate: the recommended configuration of docs/research/ultimate-algorithm.md
# (config/ultimate_tqqq.yaml) -- the champion's full committed set from
# config/best_known_2026-08-24.yaml, which unlike the hf_local_reference
# entry above includes the event / earnings boosts the research ran with,
# plus the regime, bear filter, delayed exit and capitulation-reversal
# values. The constructor defaults already equal the Ultimate values; they
# are listed so the form shows them as the strategy's primary fields.
STRATEGY_DEFAULTS["ultimate"] = {
    "bars_per_day": 387,
    "per_lot_pct": 0.0002,
    "lookback_days": 0.02,
    "event_day_boost_multiplier": 2.5,
    "earnings_day_boost_multiplier": 1.5,
    "vol_scale_exponent": -1.5,
    "vol_fast_days": 0.25,
    "vol_slow_days": 10.0,
    "vol_scale_min": 0.25,
    "vol_scale_max": 3.0,
    "vol_measure": "stdev",
    "volume_scale_exponent": -1.0,
    "natr_period": 10,
    "natr_lookback": 100,
    "regime_min_hold": 5,
    "bear_dd": 0.5,
    "bear_window": 250,
    "turbulent_mode": "reversal",
    "reversal_threshold": -0.09,
    "reversal_target": 0.06,
    "reversal_lot_pct": 0.2,
    "reversal_max_lots": 4,
    "liquidate_minute": 60,
}

# ultimate_rsp: the recommended configuration of docs/research/ultimate-rsp.md
# (config/ultimate_rsp.yaml), which is also the constructor's defaults --
# listed so the form shows them as the strategy's primary fields.
STRATEGY_DEFAULTS["ultimate_rsp"] = {
    "pd_periods": "14,21,42",
    "pd_lookbacks": "100,250",
    "ad_params": "3/10,5/20,10/40",
    "ad_lookbacks": "100,250",
    "pd_weight": 0.5,
    "execute_minute": 60,
    "rebalance_band": 0.05,
}

# ultimate_ursp: the recommended configuration of docs/research/ultimate-ursp.md
# (config/ultimate_ursp.yaml), also the constructor's defaults.
STRATEGY_DEFAULTS["ultimate_ursp"] = {
    **STRATEGY_DEFAULTS["ultimate_rsp"],
    "rebalance_band": 0.20,
    "bear_window": 250,
    "bear_dd_start": 0.25,
    "bear_dd_full": 0.55,
}


def required_parameters(strategy_class: type) -> list[str]:
    """Constructor arguments with no default, so a caller can be told."""
    signature = inspect.signature(strategy_class.__init__)
    return [
        parameter.name
        for parameter in signature.parameters.values()
        if parameter.name != "self"
        and parameter.default is inspect.Parameter.empty
        and parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
    ]


# -- Per-strategy parameter schema, for the dynamic form ----------------
#
# The "Run a backtest" form renders one input per sizing-model
# constructor argument and swaps the set when the model changes. That
# needs more than `required_parameters()` gives: a type to pick the
# widget, a default to seed it, whether it may be left blank, and which
# arguments the operator must NOT touch because the engine owns them.
#
# THREE THINGS inspect.signature CANNOT SEE, named here once:

# str arguments with a closed choice set -- the annotation is a bare
# `str`, and the allowed values only exist as a guard in the ctor body
# (`if vol_measure not in ("stdev", "range"): raise`). A unit test
# asserts every key here is a real parameter of some registered
# strategy, so this cannot rot silently.
_PARAM_ENUMS: dict[str, list[str]] = {
    "vol_measure": ["stdev", "range"],
    # research/strategies/entry_gates.py -- the tuples there are the
    # guard; these lists must match them (server/tests pin that).
    "breakdown_gate": ["off", "dual_thrust", "opening_range", "prior_low"],
    "breakdown_release": ["reclaim", "session"],
    "pattern_gate": ["off", "shooting_star"],
    "momentum_gate": ["off", "early_negative"],
    "bounce_gate": ["off", "w_bottom"],
    "rsi_gate": ["off", "head_shoulders"],
    "vol_target_estimator": [
        "yang_zhang",
        "close_to_close",
        "parkinson",
        "garman_klass",
        "rogers_satchell",
    ],
    # research/strategies/ultimate_sizing.TURBULENT_MODES (pinned there).
    "turbulent_mode": ["reversal", "cash"],
}

# Filesystem wiring the engine supplies. Never shown, never sent -- the
# constructor's own default is used. regime_by_date is UltimateSizing's
# research-lab injection of a precomputed {date: calm} map; a form has no
# way to type one, and without it the strategy computes the same regime
# from the bars (warmed with the history before the window -- see
# warm_up_history). exposure_by_date is UltimateRspSizing's equivalent.
_HIDDEN_PARAMS: frozenset[str] = frozenset(
    {"model_dir", "external_dir", "regime_by_date", "exposure_by_date"}
)

# Shown but locked: the engine captures these at run time (the first
# bar), so a value typed into a form would only be right for a
# walk-forward replay.
_DERIVED_PARAMS: frozenset[str] = frozenset({"baseline_price"})


def _wire_type(hint: object, has_default: bool, default: object) -> tuple[str, bool]:
    """(wire type, nullable) from a resolved annotation and its default.

    The strategy modules use ``from __future__ import annotations``, so a
    raw ``parameter.annotation`` is a string; callers resolve it with
    ``typing.get_type_hints`` first. ``bool`` is tested before ``int``
    because ``bool`` is a subclass of ``int`` and a checkbox is not a
    number field.

    ``nullable`` means the field may legitimately be left blank: either
    the annotation admits ``None``, or there is an explicit ``= None``
    default. A REQUIRED argument is never nullable -- a blank there must
    block the run, not be omitted.
    """
    nullable = has_default and default is None
    if get_origin(hint) in (Union, types.UnionType):  # PEP 604 "T | None"
        args = get_args(hint)
        real = [a for a in args if a is not type(None)]
        nullable = nullable or len(real) < len(args)
        hint = real[0] if real else str
    if hint is bool:
        return "bool", nullable
    if hint is int:
        return "int", nullable
    if hint is float:
        return "float", nullable
    if hint is str:
        return "str", nullable
    return "float", nullable  # tolerant: an exotic annotation renders as a number


def _apply_locks(
    spec: dict[str, Any], strategy_id: str, required: set[str], committed: dict
) -> None:
    """Mark the arguments the operator must not set directly.

    Each rule mirrors something ``build_config`` already enforces, so the
    form and the engine agree about what is editable.
    """
    name = spec["name"]
    if name in _DERIVED_PARAMS:
        spec["editable"] = False
        spec["locked_reason"] = (
            "captured from the first bar at run time; set only for walk-forward replay"
        )
    # `percentage` is FixedPortfolioPercentage's legacy alias of
    # `allocation_pct`, kept only for one internal caller; the form
    # offers the canonical name. Scoped to `fixed` so a future strategy
    # that legitimately takes a `percentage` is not caught by it.
    if name == "percentage" and strategy_id == "fixed":
        spec["editable"] = False
        spec["locked_reason"] = "deprecated alias of allocation_pct -- use allocation_pct"
    # `allocation_pct` is annotated `float | None`, but FixedPortfolioPercentage
    # raises without one (or the now-locked `percentage`), so for the form
    # it is required, not blankable -- a blank there blocks the run rather
    # than falling through to the server's committed-default substitution.
    if name == "allocation_pct" and strategy_id == "fixed":
        spec["required"] = True
        spec["nullable"] = False
    # build_config force-aligns target_return to the grid's single profit
    # target exactly when this branch is true (and refuses >1 target).
    if name == "target_return" and ("target_return" in required or "target_return" in committed):
        spec["editable"] = False
        spec["mirrors"] = "profit_target"
        spec["locked_reason"] = (
            "the posterior estimates P(reaching the run's profit target); the server sets "
            "this to the grid's profit target"
        )
    # ml_reachability_*: build_config refuses the run unless the declared
    # ticker is among the simulated funds, and the id picks the ticker.
    if name == "ticker" and strategy_id.startswith("ml_reachability"):
        spec["editable"] = False
        spec["locked_reason"] = f"{strategy_id} is trained on {committed.get('ticker')}"


def _resolve_hints(func: object) -> dict[str, object]:
    """Resolved type hints for a constructor, per parameter.

    The strategy modules use ``from __future__ import annotations``, so
    every annotation is a string. ``get_type_hints`` resolves them all in
    one call -- and fails the whole call if ONE name does not resolve (a
    ``TYPE_CHECKING``-only import, a moved symbol). A single bad
    annotation would then untype every field of that strategy: every
    ``bool`` would render as a number, every ``int`` would lose its step.
    So fall back to resolving each annotation on its own, and lose only
    the field that actually broke.
    """
    try:
        return dict(get_type_hints(func))
    except Exception:
        pass
    raw = getattr(func, "__annotations__", {}) or {}
    module = sys.modules.get(getattr(func, "__module__", ""), None)
    scope = getattr(module, "__dict__", {})
    resolved: dict[str, object] = {}
    for name, annotation in raw.items():
        if not isinstance(annotation, str):
            resolved[name] = annotation
            continue
        # A name that will not resolve just falls through -- _wire_type
        # renders that one field as a number rather than untyping the lot.
        with contextlib.suppress(Exception):
            resolved[name] = eval(annotation, scope)
    return resolved


def describe_params(strategy_id: str, strategy_class: type) -> list[dict[str, Any]]:
    """Every constructor argument of one strategy, in constructor order.

    Served by ``/funds`` so the frontend carries no idea of its own about
    what a strategy's constructor looks like -- the same reason
    ``sizing_details`` is served rather than hard-coded.
    """
    signature = inspect.signature(strategy_class.__init__)
    hints = _resolve_hints(strategy_class.__init__)
    committed = STRATEGY_DEFAULTS.get(strategy_id, {})
    required = set(required_parameters(strategy_class))

    out: list[dict[str, Any]] = []
    for parameter in signature.parameters.values():
        if parameter.name == "self" or parameter.kind in (
            parameter.VAR_POSITIONAL,
            parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.name in _HIDDEN_PARAMS:
            continue
        has_default = parameter.default is not inspect.Parameter.empty
        default = parameter.default if has_default else None
        wire_type, nullable = _wire_type(hints.get(parameter.name), has_default, default)
        has_suggested = parameter.name in committed
        spec: dict[str, Any] = {
            "name": parameter.name,
            "type": wire_type,
            "nullable": nullable,
            "required": parameter.name in required,
            "default": default,
            "enum": _PARAM_ENUMS.get(parameter.name),
            "editable": True,
            "locked_reason": None,
            "mirrors": None,
        }
        # What the field is seeded to and what "reset" restores: the
        # project's committed value. PRESENT ONLY WHEN THERE IS ONE -- its
        # presence is what used to be a separate has_suggested flag, and
        # an absent one means "seed with default".
        if has_suggested:
            spec["suggested"] = committed[parameter.name]
        _apply_locks(spec, strategy_id, required, committed)
        out.append(_wire_param(spec))
    return out


def _wire_param(spec: dict[str, Any]) -> dict[str, Any]:
    """An internal param spec as the wire's Param: false/None flags omitted.

    Four fields the form needs are NOT sent, because each is a fixed
    function of what is (web/src/lib/strategyParams.ts derives them):

      group      "advanced" exactly when neither required nor suggested --
                 the same line every tuned parameter in this project's
                 sweeps falls on
      step       "1" for int, "any" for float, else none
      editable   `locked` absent
      sweepable  not locked, not mirrored, and int/float (a RANGE sweep)
                 or enum-valued (an OPTIONS sweep). `_wire_type` resolves
                 an `_PARAM_ENUMS` entry to "str", never int/float, so the
                 two shapes cannot both hold for one spec.
    """
    out: dict[str, Any] = {"name": spec["name"], "type": spec["type"], "default": spec["default"]}
    if "suggested" in spec:
        out["suggested"] = spec["suggested"]
    if spec["required"]:
        out["required"] = True
    if spec["nullable"]:
        out["nullable"] = True
    if spec["enum"] is not None:
        out["enum"] = spec["enum"]
    if not spec["editable"]:
        out["locked"] = spec["locked_reason"] or "set by the engine"
    if spec["mirrors"] is not None:
        out["mirrors"] = spec["mirrors"]
    return out
