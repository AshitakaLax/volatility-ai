"""Submit and read backtest runs. The bidirectional half of the API.

--------------------------------------------------------------------
THIS ONE ACCEPTS INPUT, AND THAT IS THE POINT

Live state is read-only (server/live.py) because a UI bug there could
touch a real position. A backtest touches nothing: it is a simulation
over a CSV, in a process with no broker and no credentials. So the UI
may submit parameters here, which is what makes the backtesting view an
instrument rather than a report.

The line between the two is drawn by capability, not by convention:
this module never opens a ledger store and never imports a broker, and
tests/unit/test_server_capability.py fails if either changes.

--------------------------------------------------------------------
PARAMETERS ARE VALIDATED BY BacktestConfig, NOT BY A SECOND SCHEMA

Everything submitted is assembled into a dict and handed to
BacktestConfig.from_dict(...).validate() -- the same path cli.py and
every YAML file take. A parallel Pydantic schema of the same fields
would be a second definition of what a valid configuration is, free to
drift from the one the engine enforces, and the disagreement would show
up as a run that validates here and fails there.

Pydantic is used only for the SHAPE of the request body (types, bounds,
list lengths), which is a transport concern.

--------------------------------------------------------------------
THE SERIALISERS ARE THE EXPORTER'S

executions(), fund_metrics() and equity_series() are imported from
tools/export_ui_data.py rather than reimplemented. A static export and a
live API that disagreed about what a BacktestExecution looks like would
be a bug the UI discovers at runtime, on a field it happens to read.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import os
import re
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

import pandas as pd
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from server import history
from server.jobs import JobQueue
from src.core.config import BacktestConfig, expand_strategy_params
from src.core.exceptions import ConfigurationError
from src.optimization.optimization_controller import OptimizationController
from src.optimization.search_strategies import BayesianSearch
from src.trading.strategy_registry import STRATEGIES, resolve_strategy
from tools.export_ui_data import KNOWN_DATA, equity_series, executions, fund_metrics

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# How long a websocket waits for a job to change before sending a
# heartbeat. Short enough that a browser tab does not decide the
# connection is dead, long enough that a 23-second run is not producing
# dozens of pointless frames.
HEARTBEAT_SECONDS = 10.0

# PARALLELISM IS SAFE HERE BECAUSE THIS IS NOT THE TRADING MACHINE.
#
# An earlier version of this server pinned every sweep to one core, on
# the reasoning that saturating a box which might also be running the
# live loop would starve the thing that actually matters. That premise
# is wrong for this deployment: the loop runs on separate hardware, so
# the only process competing for these cores is this API.
#
# One core is still left free -- not caution about the trading loop, but
# so the event loop keeps serving the read-only live socket and the
# run's own progress frames while a sweep saturates everything else.
#
# VAI_MAX_JOBS OVERRIDES BOTH, AND THE RASPBERRY PI SETS IT TO 1.
# The paragraph above is true of the development box and FALSE of the
# Pi, which runs the trading loop and this server on the same four
# cores. The premise is a property of the HOST, so it is a setting
# rather than a constant -- and the compose file that puts this next to
# a live loop is the thing that has to say so.
_CONFIGURED = os.environ.get("VAI_MAX_JOBS")
_CORES = os.cpu_count() or 2
if _CONFIGURED and _CONFIGURED.isdigit() and int(_CONFIGURED) >= 1:
    MAX_JOBS = int(_CONFIGURED)
    DEFAULT_JOBS = MAX_JOBS
else:
    DEFAULT_JOBS = max(1, _CORES - 1)
    MAX_JOBS = max(1, _CORES)

# BUT A POOL IS NOT FREE, AND BELOW A CERTAIN SIZE IT IS A LOSS.
#
# Windows spawns rather than forks, so every worker is a fresh
# interpreter that re-imports pandas and this module tree, and each task
# pickles the whole price frame across. Measured on this machine (12
# cores, 11 workers):
#
#     13,260 bars x 12 configs   4.2s serial   ->  0.69x   SLOWER
#    100,000 bars x  6 configs   8.2s serial   ->  1.35x
#    300,000 bars x  6 configs  19.8s serial   ->  2.25x
#
# The overhead is roughly fixed, so the pool pays for itself once the
# serial run would take longer than it. The threshold below sits just
# under the break-even in bar-configurations -- the product is a decent
# proxy for the work, since the engine is a per-bar loop.
#
# The small case is the interactive one: a single configuration over a
# recent window, run to look at a chart. Making THAT slower to speed up
# a sweep nobody is watching would be the wrong trade.
PARALLEL_THRESHOLD_BAR_CONFIGS = 500_000


def choose_jobs(bars: int, combinations: int, requested: int | None) -> int:
    """How many workers this run should use.

    An explicit request is honoured (capped), because someone who has
    measured their own machine knows more than this heuristic does.
    """
    ceiling = max(1, min(MAX_JOBS, combinations))
    if requested is not None:
        return max(1, min(requested, ceiling))
    if bars * combinations < PARALLEL_THRESHOLD_BAR_CONFIGS:
        return 1
    return max(1, min(DEFAULT_JOBS, ceiling))


# HOW MANY (grid step x profit target x strategy-params) COMBINATIONS ONE
# SUBMISSION MAY REQUEST.
#
# grid_steps/profit_targets were already capped at 12 each (144 combinations,
# max) by RunRequest's own Field bounds. A swept strategy_params entry is a
# third axis, multiplying that further -- and unlike the other two, its size
# is not bounded by a RunRequest Field, since strategy_params is a free-form
# dict. Left unbounded, one submission could ask this box (or the
# Pi, which sets VAI_MAX_JOBS=1) to run an arbitrarily long sweep.
#
# 2000 sits comfortably above today's implicit 144-combination ceiling while
# keeping worst case bounded -- per the combinations x bars timings recorded
# above choose_jobs(), that is on the order of tens of minutes, not hours.
# A product/ops knob, not an architectural constant, hence the override.
_CONFIGURED_MAX_SWEEP = os.environ.get("VAI_MAX_SWEEP_COMBINATIONS")
MAX_SWEEP_COMBINATIONS = (
    int(_CONFIGURED_MAX_SWEEP)
    if _CONFIGURED_MAX_SWEEP and _CONFIGURED_MAX_SWEEP.isdigit()
    else 2000
)

# THE BAYESIAN CEILING IS MUCH HIGHER, DELIBERATELY -- the entire reason
# to submit search_strategy="bayesian" instead of "grid" is to search a
# space larger than anyone wants to run in full; RunRequest.n_trials
# (<= 500) is what actually bounds the ENGINE's work in that mode, the
# same way config/search_cowz1_bayesian_dual_scale.yaml's own combination
# count (well past a million) was never the CLI search path's limiting
# factor. This ceiling exists for a narrower reason: build_config's own
# combination-construction and expand_strategy_params still run
# synchronously in the request handler, before any job is queued, and
# an unbounded strategy_params_grid would make THAT expensive/slow to
# reject even though nothing has been searched yet. 100x the grid
# ceiling is generous headroom for real sweeps while still bounding a
# single request's own bookkeeping cost.
MAX_SWEEP_COMBINATIONS_BAYESIAN = MAX_SWEEP_COMBINATIONS * 100


class RunRequest(BaseModel):
    """The shape of a submitted run. Semantics are BacktestConfig's."""

    # A DESCRIPTIVE LABEL, never read by the engine. It is carried onto
    # the job snapshot and the archived report so a sweep can be found
    # later by what it was for rather than only by its 12-hex id. Not
    # part of BacktestConfig -- it is a UI/history concern, so it stops
    # here and is never handed to from_dict().
    name: str | None = Field(
        default=None, max_length=120, description="Optional label for the run."
    )
    tickers: list[str] = Field(..., min_length=1, max_length=8)
    grid_steps: list[float] = Field(..., min_length=1, max_length=12)
    profit_targets: list[float] = Field(..., min_length=1, max_length=12)
    sizing_model: str = "fixed"
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    fill_model: str = "close"
    enforce_no_loss: bool = True
    # A DATE WINDOW, applied before the engine sees anything. `limit` is
    # the backstop that remains: these files are a million rows and a
    # sweep over all of them is minutes per configuration.
    #
    # The two compose in that order -- window first, then cap the tail --
    # so "the last 20k bars of 2022" means what it says.
    start: str | None = Field(default=None, description="ISO date, inclusive.")
    end: str | None = Field(default=None, description="ISO date, inclusive of the whole day.")
    limit: int | None = Field(default=200_000, ge=500, le=2_000_000)
    # None means "decide for me" -- DEFAULT_JOBS. Explicit 1 forces the
    # sequential path, which is worth keeping reachable: a single
    # configuration gains nothing from a process pool and pays the cost
    # of pickling the frame to a worker.
    n_jobs: int | None = Field(default=None, ge=1, le=64)

    # HOW THE COMBINATION SPACE IS EXPLORED, not how big it is -- that is
    # still every enabled per-field "Sweep" checkbox (lib/sweepStrategies.ts
    # on the frontend, expand_strategy_params on the engine). "grid"
    # (default) enumerates every combination exhaustively, exactly
    # today's behavior for every existing caller. "bayesian" samples
    # n_trials of them via Optuna's TPE sampler
    # (src/optimization/search_strategies.BayesianSearch) -- the same
    # engine `cli.py search` already drives, now reachable from a
    # submitted run instead of only a YAML config file.
    search_strategy: Literal["grid", "bayesian"] = "grid"
    # REQUIRED for "bayesian" (see build_config), meaningless for "grid".
    # No default budget is offered on purpose: to_run_sweep_kwargs's
    # plain-string dispatch would default an unset budget to the FULL
    # combination count, which defeats the reason to choose Optuna over
    # grid in the first place (cli.py search's own cmd_search makes the
    # identical choice, for the identical reason). Bounded well under
    # MAX_SWEEP_COMBINATIONS's spirit: this queue is a single-worker
    # FIFO, and one submission should not be able to monopolize it for
    # hours.
    n_trials: int | None = Field(default=None, ge=2, le=500)
    # The objective Optuna optimizes toward AND the column the final
    # summary is sorted by -- one value serves both, so the ranked
    # output always agrees with what was actually searched for. Also
    # used to sort a plain "grid" sweep's summary, unchanged from
    # before. Restricted to columns _simulate_single's own metrics dict
    # actually carries (see optimization_controller.py) -- "Sharpe
    # Ratio" is NOT one of these; it is computed later, only for display,
    # and is not a valid target here.
    rank_by: str = "Capital Velocity Index"
    search_direction: Literal["maximize", "minimize"] = "maximize"
    # Ignored for "grid" (nothing stochastic to seed). None -> a fresh
    # exploration order each submission.
    search_seed: int | None = None


def window(
    frame: pd.DataFrame, start: str | None, end: str | None, limit: int | None
) -> pd.DataFrame:
    """Apply the date window, then the bar cap. In that order.

    The end bound covers the WHOLE day: a picker gives "2026-03-27", and
    someone selecting one day means that day, not the instant midnight
    begins it. Slicing on the bare timestamp would return nothing.

    CAPPING FIRST WOULD BE A REAL BUG. It would take the tail of the
    FILE and then filter it, so any window that is not recent comes back
    empty -- indistinguishable, on screen, from "the strategy made no
    trades in that period".
    """
    if start:
        frame = frame[frame.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        frame = frame[frame.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
    if limit:
        frame = frame.tail(limit)
    return frame


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
    "ml_regime_xbi": {
        "max_trade_pct": 0.05,
        "ticker": "XBI",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.30,
        "regime_exit_threshold": 0.20,
        "regime_floor": 0.25,
        "vol_reference": 0.45,
    },
    # TQQQ: -25% over 20 sessions, 24tr/5te episodes, held-out AUC 0.7255.
    # Thresholds are p90/p50 of THIS model's own output (range
    # 0.073-0.285); vol_reference is the fwdvol head's p75.
    "ml_regime_tqqq": {
        "max_trade_pct": 0.05,
        "ticker": "TQQQ",
        "history_path": "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv",
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
        "history_path": "data/QQQ_1Min_sip_all_rth_2016-01-01_2026-09-05.csv",
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
        "history_path": "data/RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv",
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
    # src/ml/regime_scaled_sizing.py's "UNMEASURED" note; this sweep is
    # the measurement, and the answer is still "not yet."
    "ml_regime_soxl": {
        "max_trade_pct": 0.05,
        "ticker": "SOXL",
        "history_path": "data/SOXL_1Min_sip_all_rth_2016-01-01_2026-09-03.csv",
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
        "history_path": "data/SQQQ_1Min_sip_all_ext_2016-01-01_2026-09-01.csv",
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
        "history_path": "data/SPYD_1Min_sip_all_rth_2016-01-01_2026-09-06.csv",
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
        "history_path": "data/COWZ_1Min_sip_all_rth_2016-01-01_2026-09-06.csv",
        "crash_step_multiplier": 4.0,
        "regime_enter_threshold": 0.1090,
        "regime_exit_threshold": 0.1063,
        "regime_floor": 0.25,
        "vol_reference": 0.181,
    },
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
_PARAM_ENUMS: dict[str, list[str]] = {"vol_measure": ["stdev", "range"]}

# Filesystem wiring the engine supplies. Never shown, never sent -- the
# constructor's own default is used.
_HIDDEN_PARAMS: frozenset[str] = frozenset({"model_dir", "external_dir"})

# Shown but locked: the engine captures these at run time (the first
# bar), so a value typed into a form would only be right for a
# walk-forward replay.
_DERIVED_PARAMS: frozenset[str] = frozenset({"baseline_price"})


# -- Grid-step TRIGGER method, per strategy ----------------------------
#
# `strategy._grid_trigger_level(context, last_buy_price, step)` is the
# only seam for WHEN a grid buy fires. The base SizingStrategy returns
# `last_buy_price * (1 - step)` ("last_buy" -- a fresh low below the
# last fill). HighFrequencyLocalReferenceSizing overrides it
# UNCONDITIONALLY to `max(last_buy_price, rolling_high) * (1 - step)`
# ("local_reference" -- retriggers on any local pullback).
# BayesianDualScaleSizing overrides it too but falls back to the base
# unless its OPTIONAL `lookback_days` is set -- the one strategy with a
# real per-run choice, toggled by that param's presence.
#
# This is PRESENTATION over those existing overrides -- there is no
# base-class grid-reference argument and this must not add one.
# `window_param` is keyed here, never inferred from a name, because
# bell_curve also takes a required `lookback_days` that is a Gaussian
# SIZING window, not a trigger window. tests/unit/test_backtest_grid_trigger.py
# ties this table to the actual override.
_GRID_TRIGGER_LAST_BUY: dict[str, Any] = {
    "methods": ["last_buy"],
    "default": "last_buy",
    "controlled_by": None,
    "window_param": None,
    "window_default": None,
}
_GRID_TRIGGER: dict[str, dict[str, Any]] = {
    "hf_local_reference": {
        "methods": ["local_reference"],
        "default": "local_reference",
        "controlled_by": None,
        "window_param": "lookback_days",
        "window_default": None,
    },
    "bayesian_dual_scale": {
        "methods": ["last_buy", "local_reference"],
        "default": "last_buy",
        "controlled_by": "lookback_days",
        "window_param": "lookback_days",
        "window_default": 0.03,
    },
}
# MLRegimeScaledSizing's level is last_buy's formula with the STEP
# scaled by a model-driven latch, so it is neither of the two methods
# above: not plain last_buy (the multiplier is not 1), and not
# local_reference (the reference is still the last fill, not a rolling
# high). It gets its own locked method rather than being described as
# last_buy, because tests/unit/test_backtest_grid_trigger.py's anti-rot
# check ties this table to whether the class actually overrides
# _grid_trigger_level -- and describing a widened grid as an unwidened
# one is exactly the drift that check exists to catch.
#
# Locked (single-entry list), with no window_param: the widening is not
# an operator choice, it is what the strategy IS, and there is no
# rolling window to configure.
# Derived from the registry rather than listed, so registering a new
# ml_regime_* id cannot forget its trigger descriptor -- which is
# exactly what happened when six funds were added at once and
# tests/unit/test_backtest_grid_trigger.py's anti-rot check caught it.
for _regime_id in (_i for _i in STRATEGIES if _i.startswith("ml_regime_")):
    _GRID_TRIGGER[_regime_id] = {
        "methods": ["regime_widened"],
        "default": "regime_widened",
        "controlled_by": None,
        "window_param": None,
        "window_default": None,
    }


def describe_grid_trigger(strategy_id: str) -> dict[str, Any]:
    """The grid-step trigger methods a strategy supports, for the form.

    ``methods`` (display order; entry 0 is the default) lists what
    ``_grid_trigger_level`` actually does. ``controlled_by`` names the
    strategy_param whose PRESENCE selects ``local_reference`` (None when
    the method is locked). ``window_param`` is the strategy_param that
    IS the rolling-high window; ``window_default`` seeds it the first
    time ``local_reference`` is picked (None when it seeds itself, as
    hf's committed ``lookback_days`` does).
    """
    spec = _GRID_TRIGGER.get(strategy_id, _GRID_TRIGGER_LAST_BUY)
    return {**spec, "methods": list(spec["methods"])}


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
            # What the field is seeded to and what "reset" restores: the
            # project's committed value when there is one, else the bare
            # constructor default.
            "suggested": committed[parameter.name] if has_suggested else default,
            "has_suggested": has_suggested,
            "enum": _PARAM_ENUMS.get(parameter.name),
            # "primary" is exactly "required or in a committed config" --
            # the same line every tuned parameter in this project's sweeps
            # falls on. Everything else is "advanced".
            "group": "primary" if (parameter.name in required or has_suggested) else "advanced",
            "editable": True,
            "locked_reason": None,
            "mirrors": None,
            "step": None
            if parameter.name in _PARAM_ENUMS
            else {"int": "1", "float": "any"}.get(wire_type),
        }
        _apply_locks(spec, strategy_id, required, committed)
        # SWEEPABLE, for the "enable sweep" checkbox: an argument the
        # operator actually owns, whose values expand_strategy_params
        # (src/core/config.py) can turn into a real sweep axis. Computed
        # AFTER _apply_locks so a param it locked (editable=False) or
        # mirrored (target_return -> profit_target) is correctly
        # excluded -- an engine-owned or grid-mirrored value cannot also
        # be independently swept.
        #
        # TWO SWEEPABLE SHAPES, DISTINGUISHED BY `enum`, NOT BY A THIRD
        # FIELD. A numeric (int/float) param sweeps as a RANGE -- the
        # frontend's min/max/count/strategy generator
        # (web/src/lib/sweepStrategies.ts). A `str` param with `enum` set
        # sweeps as OPTIONS -- a checklist of which of its own named
        # values to include, submitted as that literal subset (e.g.
        # `vol_measure: ["stdev", "range"]`). expand_strategy_params
        # already treats any list-valued strategy_param as an axis
        # regardless of element type, so this widens what the FORM
        # offers, not what the engine accepts -- a config file could
        # already do this by hand.
        #
        # The two are mutually exclusive rather than a lookup on a
        # combined condition: `_wire_type` resolves an `_PARAM_ENUMS`
        # entry to `"str"`, never `"int"`/`"float"` (see the `step`
        # assignment above, which already special-cases enum names for
        # the identical reason), so `spec["enum"]` and
        # `spec["type"] in ("int", "float")` cannot both hold for one
        # spec -- no ambiguity for a caller branching on `enum` alone.
        spec["sweepable"] = (
            spec["editable"]
            and spec["mirrors"] is None
            and (spec["type"] in ("int", "float") or spec["enum"] is not None)
        )
        out.append(spec)
    return out


def _safe_describe(strategy_id: str, strategy_class: type) -> dict[str, Any]:
    """describe_params, but one broken strategy never 500s /funds."""
    try:
        return {"params": describe_params(strategy_id, strategy_class)}
    except Exception:
        return {"params": []}


def resolve_params(request: RunRequest) -> dict[str, Any]:
    """The parameters a run will actually use.

    An EMPTY strategy_params falls back to the model's defaults rather
    than erroring. Every model but `fixed` has required constructor
    arguments, so a bare `{"sizing_model": "rsi"}` would otherwise be a
    400 for a request that is perfectly clear about what it wants -- and
    the UI, a script, and a curl all end up carrying the same table.

    Anything the caller DID provide is used as given, including a
    partial set: someone overriding one parameter has said something
    deliberate, and silently merging defaults underneath would run a
    configuration they did not ask for.
    """
    if request.strategy_params:
        return dict(request.strategy_params)
    return dict(STRATEGY_DEFAULTS.get(request.sizing_model, {}))


def build_config(request: RunRequest) -> BacktestConfig:
    """Validate a request the way the engine itself would.

    Raises ConfigurationError, which the caller turns into a 400. A bad
    strategy_id fails here with the list of real ones rather than as a
    KeyError somewhere inside a worker thread.
    """
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": request.sizing_model,
                "strategy_params": resolve_params(request),
            },
            "grid": {
                "steps": request.grid_steps,
                "profit_targets": request.profit_targets,
            },
            "execution": {
                "fill_model": request.fill_model,
                "enforce_no_loss": request.enforce_no_loss,
            },
            "search": {
                "strategy": request.search_strategy,
                "rank_by": request.rank_by,
                "direction": request.search_direction,
                "seed": request.search_seed,
            },
            # NO `live` SECTION, EVER. This process has no credentials and
            # no broker; accepting live settings from a browser would be
            # accepting them from anyone who can reach this port. The
            # capability test asserts this module names no broker.
        }
    )
    config.validate()
    strategy_class = resolve_strategy(config.strategy.strategy_id)  # fails loudly on a typo

    if request.search_strategy == "bayesian" and request.n_trials is None:
        raise ConfigurationError(
            "search_strategy='bayesian' requires n_trials -- the whole reason to choose "
            "Optuna over an exhaustive grid is to search a space larger than you want to run "
            "in full. Pick a trial budget (2-500)."
        )

    # CONSTRUCT IT HERE, where the caller is still waiting. Left to the
    # worker, a missing argument surfaces as every combination erroring
    # and then a confusing "rank_by column not found" -- twenty seconds
    # later, naming a column rather than the argument that was missing.
    params = dict(config.strategy.strategy_params)

    # A SWEPT target_return WOULD BE SILENTLY DISCARDED BELOW, not run:
    # the mirror-alignment block just past this force-aligns target_return
    # to the grid's single profit target, so a list here would have its
    # sweep attempt overwritten with no error. describe_params() already
    # marks target_return non-sweepable (mirrors="profit_target") so the
    # form never offers this checkbox -- this is defense-in-depth for a
    # caller reaching the API directly.
    if isinstance(params.get("target_return"), list):
        raise ConfigurationError(
            f"{config.strategy.strategy_id!r} estimates the probability of reaching one "
            "target_return, so it cannot be swept independently -- the server aligns it to "
            "the grid's profit target automatically."
        )

    # TARGET_RETURN MUST MIRROR THE GRID, and the engine refuses when it
    # does not -- BayesianDualScaleSizing estimates P(reaching
    # target_return within horizon), so a mismatch has it confidently
    # answering a different question than the one being traded.
    #
    # That guard is right, and it means no single default can span a
    # sweep of several profit targets. Rather than let the dropdown
    # submit a run that dies per-combination twenty seconds later, the
    # value is ALIGNED here when the caller did not choose one, and
    # refused outright when the grid has more than one target for it to
    # mirror.
    if "target_return" in required_parameters(strategy_class) or "target_return" in params:
        targets = config.grid.profit_targets
        if len(targets) > 1:
            raise ConfigurationError(
                f"{config.strategy.strategy_id!r} estimates the probability of reaching one "
                f"target_return, so it cannot sweep {len(targets)} profit targets at once. "
                "Run one profit target per submission, or choose another sizing model."
            )
        if targets:
            params["target_return"] = targets[0]

    # A LIST-VALUED strategy_param IS A SWEEP AXIS, expanded here the same
    # way the CLI/config-file path already does (BacktestConfig.to_run_sweep_kwargs
    # -> expand_strategy_params). Scalars-only pass through as the single
    # combination they always were, so nothing about this changes behavior
    # for a request that never sweeps a strategy param.
    strategy_params_grid = expand_strategy_params(params)

    total_combinations = (
        len(config.grid.steps) * len(config.grid.profit_targets) * len(strategy_params_grid)
    )
    # Bayesian mode is bounded by n_trials, already validated above --
    # the combination-space ceiling here exists for a different reason
    # (see MAX_SWEEP_COMBINATIONS_BAYESIAN's own comment) and is
    # correspondingly looser.
    is_bayesian = request.search_strategy == "bayesian"
    combination_ceiling = MAX_SWEEP_COMBINATIONS_BAYESIAN if is_bayesian else MAX_SWEEP_COMBINATIONS
    if total_combinations > combination_ceiling:
        raise ConfigurationError(
            f"This sweep would run {total_combinations} combinations "
            f"({len(config.grid.steps)} grid steps x {len(config.grid.profit_targets)} profit "
            f"targets x {len(strategy_params_grid)} strategy-parameter combinations), which "
            f"exceeds the {combination_ceiling} limit for one submission. Narrow a swept "
            "range, or split this into more than one run."
        )

    try:
        # Every combination is constructed here, not just the first --
        # a bad value anywhere in a swept strategy param must fail this
        # request now, not twenty combinations into a worker thread.
        # `instance` stays the first: enough for the ticker check below,
        # since `ticker` is locked (never sweepable) and so is identical
        # across every combination.
        #
        # BAYESIAN MODE ONLY VALIDATES THE FIRST COMBINATION. Optuna will
        # construct at most n_trials (<= 500) of the space it actually
        # samples, at engine run time, where a per-combination failure is
        # already isolated and reported per-row -- validating every
        # combination of a space that can run to MAX_SWEEP_COMBINATIONS_BAYESIAN
        # here, synchronously, before the job even queues, would defeat
        # the point of choosing Optuna to avoid touching the whole space.
        instance = strategy_class(**strategy_params_grid[0])
        if not is_bayesian:
            for combo in strategy_params_grid[1:]:
                strategy_class(**combo)
    except TypeError as exc:
        missing = [name for name in required_parameters(strategy_class) if name not in params]
        detail = f"{config.strategy.strategy_id!r} cannot be built from the parameters given: {exc}"
        if missing:
            suggested = STRATEGY_DEFAULTS.get(config.strategy.strategy_id, {})
            detail += f". Missing: {missing}."
            if suggested:
                detail += f" Try: {suggested}"
        raise ConfigurationError(detail) from exc

    # THE SAME "catch it here" REASONING, for a per-instrument model
    # (MLReachabilitySizing) rather than a missing argument. Without
    # this, submitting ml_reachability_cowz against RSP fails deep
    # inside the sweep -- optimization_controller.py's own mismatch
    # guard fires, but per-combination error isolation there turns it
    # into an ordinary "combination failed" row, and with every
    # combination failing the same way, the caller sees "rank_by
    # column 'Capital Velocity Index' not found" rather than the
    # actual reason. getattr, not isinstance, so this generalizes to
    # any future per-instrument model declaring the same convention.
    declared_ticker = getattr(instance, "ticker", None)
    if declared_ticker is not None and declared_ticker not in request.tickers:
        raise ConfigurationError(
            f"{config.strategy.strategy_id!r} was trained on {declared_ticker}, which is not "
            f"among the tickers being simulated ({', '.join(request.tickers)}). Pick the sizing "
            f"model that matches the fund (e.g. ml_reachability_cowz for COWZ), or add "
            f"{declared_ticker} to the funds being run."
        )

    # Rebuilt so the alignment above is what the ENGINE sees, not just
    # what was validated. A check that passed on one set of parameters
    # and ran another would be worse than no check.
    if params != dict(config.strategy.strategy_params):
        config = BacktestConfig.from_dict(
            {
                "strategy": {"strategy_id": config.strategy.strategy_id, "strategy_params": params},
                "grid": {
                    "steps": list(config.grid.steps),
                    "profit_targets": list(config.grid.profit_targets),
                },
                "execution": {
                    "fill_model": config.execution.fill_model,
                    "enforce_no_loss": config.execution.enforce_no_loss,
                },
                # Carried through explicitly -- from_dict defaults an
                # absent "search" key to plain grid, which would
                # silently downgrade a bayesian request the instant
                # target_return alignment (above) triggers this rebuild.
                "search": {
                    "strategy": config.search.strategy,
                    "rank_by": config.search.rank_by,
                    "direction": config.search.direction,
                    "seed": config.search.seed,
                },
            }
        )
        config.validate()
    return config


def _native(value: Any) -> Any:
    """A pandas/numpy scalar as a plain Python one.

    summary.iterrows() (below) yields numpy scalars -- np.float64,
    np.int64, ... -- for any column pulled straight through pandas, and
    history.save() calls bare json.dumps with no custom encoder. An
    uncoerced value here would raise TypeError at archive time, well
    after the run itself succeeded. grid_step/profit_target already
    avoid this with an explicit float(...); this generalizes it to a
    strategy param of unknown type (int, float, bool, str).
    """
    return value.item() if hasattr(value, "item") else value


def run_backtest(request: dict[str, Any], report: Callable[[float, str], None]) -> dict[str, Any]:
    """Execute one submitted run. Called on the worker thread.

    `report` is the job queue's progress callback. Progress is per
    (ticker x configuration), which is as fine as the engine's own
    reporting allows -- run_sweep returns when it returns.
    """
    parsed = RunRequest(**request)
    config = build_config(parsed)
    strategy_class = resolve_strategy(config.strategy.strategy_id)

    available = [t for t in parsed.tickers if t in KNOWN_DATA and Path(KNOWN_DATA[t]).exists()]
    if not available:
        raise ValueError(
            f"None of {parsed.tickers} has a data file. Known: {sorted(KNOWN_DATA)}. "
            "Download one with `python cli.py fetch-data --symbol <T> ...`."
        )

    funds: dict[str, Any] = {}
    jobs = 1
    # PROGRESS IS PER COMBINATION, NOT PER TICKER. A single-instrument
    # run has one ticker, so a per-ticker bar sits at 0% for the whole
    # run and then jumps to 100% -- which tells a watcher nothing except
    # that the page has not crashed. The engine now reports each
    # combination as it finishes, so the fraction below is real work
    # done across every ticker in the request.
    strategy_params_grid = expand_strategy_params(config.strategy.strategy_params)
    combinations = (
        len(config.grid.steps) * len(config.grid.profit_targets) * len(strategy_params_grid)
    )
    total_units = max(1, combinations * len(available))
    finished_units = 0
    # Which summary columns are strategy params, not "Grid Step"/"Profit
    # Target"/"Strategy"/a metric -- optimization_controller.py's
    # result_row spreads the resolved combo's own keys straight into the
    # row, so this is exactly the set to pull back out per cell.
    strategy_param_keys = set(config.strategy.strategy_params)

    for ticker in available:
        report(finished_units / total_units, f"running {ticker}")
        frame = pd.read_csv(KNOWN_DATA[ticker], parse_dates=["timestamp"]).set_index("timestamp")
        frame = window(frame, parsed.start, parsed.end, parsed.limit)
        if frame.empty:
            raise ValueError(
                f"{ticker} has no bars between {parsed.start} and {parsed.end}. "
                "Widen the window, or check what the file covers."
            )

        kwargs = config.to_run_sweep_kwargs(strategy_class)
        kwargs["return_full_results"] = True
        kwargs["symbol"] = ticker
        jobs = choose_jobs(len(frame), combinations, parsed.n_jobs)
        kwargs["n_jobs"] = jobs

        # kwargs["search_strategy"] is still the bare string "bayesian"
        # at this point -- to_run_sweep_kwargs has no n_trials field to
        # put on it (BacktestConfig/SearchConfig has none; it is a
        # REQUEST-only concept, the web equivalent of cli.py search's
        # own --trials flag, not a YAML config field). Passed as a
        # string, _resolve_search_strategy would default the budget to
        # the FULL combination count -- see BayesianSearch's own
        # docstring on exactly this trap. Replaced here, per ticker,
        # with a real pre-configured instance carrying parsed.n_trials;
        # everything else it needs (grid_steps/profit_targets/
        # strategy_params_grid/rank_by/direction/seed) is already in
        # kwargs from to_run_sweep_kwargs, read back rather than
        # recomputed. One fresh BayesianSearch per ticker, matching how
        # a plain grid sweep already runs the identical combination
        # space once per ticker in this same loop.
        if kwargs["search_strategy"] == "bayesian":
            kwargs["search_strategy"] = BayesianSearch(
                kwargs["grid_steps"],
                kwargs["profit_targets"],
                kwargs["strategy_params_grid"],
                rank_by=kwargs["rank_by"],
                direction=kwargs["search_direction"],
                n_trials=parsed.n_trials,
                seed=kwargs["search_seed"],
            )

        def on_combination(
            done: int, of: int, _base: int = finished_units, _t: str = ticker
        ) -> None:
            # Bound as defaults so the closure reports THIS ticker's
            # offset even if it were ever called after the loop moved
            # on -- the same late-binding hazard the engine's own fill
            # closures bind against.
            report((_base + done) / total_units, f"{_t}: {done}/{of} configurations")

        kwargs["progress_callback"] = on_combination
        summary, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)

        # The best configuration by the engine's own default ranking.
        # run_sweep sorted summary and full_results together, so index 0
        # is that row and the UI is not re-ranking by a metric of its own
        # invention.
        result = full[0]
        funds[ticker] = {
            "metrics": fund_metrics(result.metrics, ticker),
            "executions": executions(result.trade_blotter, ticker),
            "equity_curve": equity_series(result.equity_curve),
            # EVERY configuration, for the sweep matrix -- metrics only.
            # Carrying each one's executions as well would multiply the
            # payload by the size of the grid to draw a heatmap that
            # needs one number per cell.
            "configurations": [
                {
                    "grid_step": float(row["Grid Step"]),
                    "profit_target": float(row["Profit Target"]),
                    # The resolved strategy-param combo THIS cell ran
                    # with -- distinct per cell once a strategy param is
                    # swept, so the sweep matrix/history can tell one
                    # combo's row from another's rather than showing the
                    # same (wrong) run-level value on every row.
                    "strategy_params": {
                        key: _native(row[key]) for key in strategy_param_keys if key in row
                    },
                    "metrics": fund_metrics(dict(row), ticker),
                }
                for _, row in summary.iterrows()
            ],
            "bars": {
                "start": pd.Timestamp(frame.index[0]).isoformat(),
                "end": pd.Timestamp(frame.index[-1]).isoformat(),
                "count": len(frame),
            },
        }
        # This ticker's combinations are done; the next one's callback
        # counts from here rather than restarting at zero.
        finished_units += combinations

    report(1.0, "assembling report")
    return {
        "run_id": "",  # filled in by the route from the job's own id
        "parameters": {
            # Descriptive only; None when the run was submitted unnamed
            # or with nothing but whitespace.
            "name": (parsed.name or "").strip() or None,
            "grid_step_pct": config.grid.steps[0] if config.grid.steps else None,
            "profit_target_pct": (
                config.grid.profit_targets[0] if config.grid.profit_targets else None
            ),
            "sizing_model": config.strategy.strategy_id,
            # The RESOLVED strategy parameters -- what the engine was
            # actually constructed with, after defaults were filled in
            # and target_return was aligned to the grid. Carried so the
            # history view can filter on an input argument rather than
            # only on the swept grid step and profit target. All values
            # are plain numbers/strings/bools; nothing here needs a
            # custom encoder.
            "strategy_params": dict(config.strategy.strategy_params),
            "fill_model": config.execution.fill_model,
            "enforce_no_loss": config.execution.enforce_no_loss,
            # What the run ACTUALLY used, not what was asked for, so a
            # reader can tell a slow sweep from a serial one.
            "n_jobs": jobs,
        },
        "timeframe": {
            "start": min((f["bars"]["start"] for f in funds.values()), default=None),
            "end": max((f["bars"]["end"] for f in funds.values()), default=None),
            "interval": "1Min",
        },
        "funds": funds,
    }


def _archive(job) -> None:
    """Write a completed run to the history directory.

    Stamped with its own id first: run_backtest cannot know the id --
    the queue mints it after the request is built -- and a stored report
    whose run_id was the empty string would be unloadable by the very
    endpoint that serves it back.
    """
    history.save(job.run_id, _with_id(job.snapshot(), job.run_id))


queue = JobQueue(runner=run_backtest, on_complete=_archive)


@router.get("/funds")
def funds() -> dict[str, Any]:
    """What can actually be backtested on this machine.

    Reports presence rather than filtering it out: a UI that silently
    omits SPY is indistinguishable from one that has never heard of it,
    and the fix (`cli.py fetch-data`) is worth naming.
    """
    return {
        "funds": [
            {"ticker": ticker, "path": path, "available": Path(path).exists()}
            for ticker, path in sorted(KNOWN_DATA.items())
        ],
        "sizing_models": sorted(STRATEGIES),
        # What each model NEEDS and a working starting point for it.
        # Served rather than hard-coded in the bundle so the two cannot
        # drift -- the frontend should not carry its own idea of what a
        # strategy's constructor looks like.
        "sizing_details": {
            name: {
                "required": required_parameters(cls),
                "defaults": STRATEGY_DEFAULTS.get(name, {}),
            }
            for name, cls in sorted(STRATEGIES.items())
        },
        # The dynamic-form schema: every constructor argument of every
        # model, typed and seeded, so the form can swap its fields when
        # the model changes. `sizing_details` above is left exactly as it
        # was for its existing consumers; this is a strict addition.
        "sizing_params": {
            name: _safe_describe(name, cls) for name, cls in sorted(STRATEGIES.items())
        },
        # Which grid-step trigger method(s) each model supports, so the
        # form can offer the choice only where the engine has one. A
        # sibling key -- `sizing_params` and its broken-strategy guard
        # are untouched -- and a plain dict lookup, no try/except.
        "grid_trigger": {name: describe_grid_trigger(name) for name in sorted(STRATEGIES)},
    }


@router.get("/bars")
def bars(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    max_points: int = 3000,
) -> dict[str, Any]:
    """OHLC for a window, downsampled SERVER-SIDE.

    Distinct from /api/live/bars, which serves the tail of a file for a
    running deployment. This one takes a date range, which is what a
    historical chart needs and what the live endpoint deliberately does
    not offer.

    THE DOWNSAMPLE IS OHLC, NOT SAMPLING. Buckets are sized so the
    result lands near max_points, and each keeps first open, max high,
    min low, last close. Taking every Nth row instead would drop the
    extremes -- and under the engine's "intrabar" fill model a level
    TOUCHED during a bar is a fill, so the wicks are exactly where the
    executions are. A chart that dropped them would show markers hanging
    off a candle that never reached them.

    A ten-year minute file is a million rows and roughly 60 MB. Sending
    it whole would stall this process serialising it and the browser
    parsing it, to draw a few thousand pixels.
    """
    path = KNOWN_DATA.get(ticker)
    if path is None or not Path(path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"No data file for {ticker!r}. Known: {sorted(KNOWN_DATA)}.",
        )

    frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    frame = window(frame, start, end, None)
    if frame.empty:
        return {"ticker": ticker, "bars": [], "bucket_seconds": 60, "source_rows": 0}

    source_rows = len(frame)
    # Round the bucket up to a whole number of minutes so the result is
    # a recognisable timeframe rather than an arbitrary 137-second bar.
    minutes = max(1, -(-source_rows // max_points))
    rule = f"{minutes}min"
    rolled = frame.resample(rule).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    # Gaps -- nights, weekends, holidays -- resample into empty rows.
    # Dropping them keeps the axis continuous across sessions, which is
    # what every trading chart does.
    rolled = rolled.dropna(subset=["close"])

    return {
        "ticker": ticker,
        "bucket_seconds": minutes * 60,
        "source_rows": source_rows,
        "bars": [
            {
                "time": int(timestamp.timestamp()),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
            for timestamp, row in rolled.iterrows()
        ],
    }


@router.get("/history")
def history_rows() -> dict[str, Any]:
    """Every completed run, flattened to one row PER CONFIGURATION.

    A run can hold several funds and each fund several configurations,
    so "rank the runs" is the wrong shape -- the thing worth comparing
    is a (run, fund, grid step, profit target) tuple and its metrics.
    Flattening here means the client sorts an array rather than walking
    a tree to find comparable numbers.

    Ranking itself is deliberately NOT done here. The metric is the
    reader's choice and changing it should be instant, not a round trip.
    """
    rows: list[dict[str, Any]] = []
    for run in history.load_all():
        report = run.get("report") or {}
        parameters = report.get("parameters") or {}
        timeframe = report.get("timeframe") or {}
        for ticker, fund in (report.get("funds") or {}).items():
            configurations = fund.get("configurations") or []
            if not configurations:
                # A report from before configurations were carried still
                # has its headline metrics. Synthesised as a single cell
                # so old runs stay comparable rather than disappearing.
                configurations = [
                    {
                        "grid_step": parameters.get("grid_step_pct"),
                        "profit_target": parameters.get("profit_target_pct"),
                        "metrics": fund.get("metrics") or {},
                    }
                ]
            for index, cell in enumerate(configurations):
                rows.append(
                    {
                        "run_id": run.get("run_id"),
                        # Repeated on every configuration row of a run --
                        # the table is flattened one row per cell, and a
                        # reader scanning it should see the label on each.
                        "name": parameters.get("name"),
                        "saved_at": run.get("saved_at"),
                        "ticker": ticker,
                        "grid_step": cell.get("grid_step"),
                        "profit_target": cell.get("profit_target"),
                        "sizing_model": parameters.get("sizing_model"),
                        # The resolved input arguments, so the client can
                        # filter on one. Prefer the CELL's own combo --
                        # once a strategy param is swept, cells of the
                        # same run can differ; falling back to the run-
                        # level value keeps a pre-sweep report (which
                        # never carried a per-cell value) unchanged, and
                        # {} covers a run archived before either existed.
                        "strategy_params": cell.get("strategy_params")
                        or parameters.get("strategy_params")
                        or {},
                        "fill_model": parameters.get("fill_model"),
                        # The engine ranked these; index 0 is its own
                        # pick, and saying so lets a reader see when
                        # their chosen metric disagrees with it.
                        "engine_rank": index,
                        "start": timeframe.get("start"),
                        "end": timeframe.get("end"),
                        "bars": (fund.get("bars") or {}).get("count"),
                        "metrics": cell.get("metrics") or {},
                    }
                )
    return {"rows": rows, "runs": len({row["run_id"] for row in rows})}


@router.get("/history/{run_id}")
def history_run(run_id: str) -> dict[str, Any]:
    """One persisted run in full, for loading back into the view."""
    run = history.load(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No stored run {run_id!r}.")
    return run


@router.get("/runs")
def runs() -> dict[str, Any]:
    """Every run this server has seen, newest first."""
    return {"runs": [job.snapshot() for job in queue.all()]}


@router.get("/runs/{run_id}")
def run(run_id: str) -> dict[str, Any]:
    job = queue.get(run_id)
    if job is not None:
        return _with_id(job.snapshot(), run_id)
    # Not in memory. A completed run outlives the process that made it,
    # so a restart must not turn a link someone saved into a 404.
    stored = history.load(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No run {run_id!r}.")
    return stored


@router.post("/runs", status_code=202)
def submit(request: RunRequest) -> dict[str, Any]:
    """Queue a run. Returns immediately with an id.

    202, not 200: nothing has been computed yet. Validation happens HERE
    rather than on the worker so a malformed request fails as a 400 the
    caller can act on, instead of as a job that fails 20 seconds later.
    """
    try:
        build_config(request)
    except ConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid run request: {exc}") from exc

    job = queue.submit(request.model_dump())
    return _with_id(job.snapshot(), job.run_id)


class ValidateError(BaseModel):
    """One thing wrong with a would-be run, attached to a field when it
    can be, so the form can render it under the offending input."""

    field: str | None = None
    message: str


class ValidateResponse(BaseModel):
    ok: bool
    # The parameters the engine would actually build with -- defaults
    # filled in, target_return aligned. None when the request is invalid.
    resolved_strategy_params: dict[str, Any] | None = None
    # The subset of resolved_strategy_params the server set or changed
    # relative to what was submitted (today: target_return).
    aligned: dict[str, Any] = Field(default_factory=dict)
    errors: list[ValidateError] = Field(default_factory=list)


# `build_config`'s missing-argument message names them as `Missing: [...]`.
_MISSING_RE = re.compile(r"Missing: \[([^\]]*)\]")


def _error_field(message: str, names: list[str]) -> str | None:
    """The parameter a validation message is about, if exactly one is
    named. Leading token first (the engine's messages start with the id
    or the offending key), then a whole-word scan."""
    head = message.strip().split(" ", 1)[0].strip("'\"")
    if head in names:
        return head
    hits = [n for n in names if re.search(rf"\b{re.escape(n)}\b", message)]
    return hits[0] if len(hits) == 1 else None


def _explode_error(message: str, names: list[str]) -> list[ValidateError]:
    """One ConfigurationError string -> field-attached errors. A
    `Missing: [a, b]` message becomes one error per missing name."""
    found = _MISSING_RE.search(message)
    if found:
        missing = [
            token.strip().strip("'\"") for token in found.group(1).split(",") if token.strip()
        ]
        if missing:
            return [
                ValidateError(field=name if name in names else None, message=message)
                for name in missing
            ]
    # The multi-target refusal names `target_return` in passing ("reaching
    # one target_return, so it cannot sweep ..."), but it is about the
    # profit-target GRID, not a constructor argument -- leave it
    # unattached so the form shows it as a banner, not under a locked
    # field the user cannot change to fix it.
    if "cannot sweep" in message and "profit target" in message:
        return [ValidateError(field=None, message=message)]
    return [ValidateError(field=_error_field(message, names), message=message)]


@router.post("/validate")
def validate(request: RunRequest) -> ValidateResponse:
    """Dry-run the exact validation `submit` runs, without queuing.

    The form calls this while the operator types so a bad parameter is a
    red line under a field, not a 400 on click or a job that dies twenty
    seconds later. It goes through the SAME `build_config(request)` the
    submit path uses -- there is no second definition of "valid" to
    drift -- and `build_config` opens no store, imports no broker and
    touches neither the queue nor history (the capability test holds
    this module to that). Always HTTP 200: the errors are the payload,
    which is easier to consume from a debounced keystroke than a 400.
    """
    submitted = dict(request.strategy_params)
    strategy_class = STRATEGIES.get(request.sizing_model)
    names = (
        [spec["name"] for spec in _safe_describe(request.sizing_model, strategy_class)["params"]]
        if strategy_class is not None
        else []
    )
    try:
        config = build_config(request)
    except ConfigurationError as exc:
        return ValidateResponse(ok=False, errors=_explode_error(str(exc), names))
    except Exception as exc:
        return ValidateResponse(ok=False, errors=[ValidateError(field=None, message=str(exc))])

    resolved = dict(config.strategy.strategy_params)
    aligned = {
        key: value
        for key, value in resolved.items()
        if key not in submitted or submitted[key] != value
    }
    return ValidateResponse(ok=True, resolved_strategy_params=resolved, aligned=aligned)


@router.websocket("/ws/{run_id}")
async def run_socket(socket: WebSocket, run_id: str) -> None:
    """Stream one run's progress, then its result.

    Blocks on the job queue's Condition rather than polling, so an
    update is delivered when it happens. Sends the current state first,
    because a client that connects after a fast run finished must not
    wait forever for an event that has already passed.
    """
    await socket.accept()
    job = queue.get(run_id)
    if job is None:
        await socket.send_json({"type": "error", "detail": f"No run {run_id!r}."})
        await socket.close()
        return

    try:
        seen = -1
        while True:
            # OFF THE EVENT LOOP. wait_for_change blocks on a
            # threading.Condition for up to HEARTBEAT_SECONDS, and
            # calling it directly from this coroutine would stall every
            # other request for that whole period -- including the
            # read-only live socket an operator may be watching a real
            # deployment through. asyncio.to_thread hands the block to a
            # worker and lets the loop keep serving.
            current = await asyncio.to_thread(
                queue.wait_for_change, run_id, seen, HEARTBEAT_SECONDS
            )
            if current is None:
                await socket.send_json({"type": "error", "detail": f"No run {run_id!r}."})
                return
            if current.revision == seen:
                await socket.send_json({"type": "heartbeat", "run_id": run_id})
                continue
            seen = current.revision
            await socket.send_json({"type": "run", "run": _with_id(current.snapshot(), run_id)})
            if current.status in {"complete", "failed"}:
                return
    except WebSocketDisconnect:
        return


def _with_id(snapshot: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Stamp the job's id onto its report.

    run_backtest cannot know it -- the id is minted by the queue when
    the job is created, after the request has been built. Filling it in
    here keeps the worker free of queue concepts.
    """
    report = snapshot.get("report")
    if isinstance(report, dict):
        report["run_id"] = run_id
    return snapshot


__all__ = [
    "RunRequest",
    "ValidateResponse",
    "build_config",
    "describe_grid_trigger",
    "describe_params",
    "queue",
    "router",
    "run_backtest",
]
