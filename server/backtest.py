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
import json
import math
import os
import re
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

import pandas as pd
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, model_validator

from server import contract, history
from server.jobs import (
    TERMINAL,
    JobQueue,
    QueueError,
    QueueStore,
    RunControl,
    RunStopped,
    UnknownRun,
)
from src.core.config import BacktestConfig, expand_strategy_params
from src.core.exceptions import ConfigurationError
from src.optimization.optimization_controller import OptimizationController
from src.optimization.search_strategies import BayesianSearch, GridSearch, SearchStrategy
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
# space larger than anyone wants to run in full; RunRequest.bayes.trials
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


class BayesSearch(BaseModel):
    """Sample the combination space with Optuna's TPE instead of enumerating it."""

    # REQUIRED in spirit, Optional in the schema: a legacy request with
    # search_strategy="bayesian" and no n_trials arrives as trials=None,
    # and build_config refuses it with a message naming the choice rather
    # than a bare 422. No default budget is offered on purpose --
    # to_run_sweep_kwargs's plain-string dispatch would default an unset
    # budget to the FULL combination count, which defeats the reason to
    # choose Optuna over grid (cli.py search makes the identical choice).
    # Bounded well under MAX_SWEEP_COMBINATIONS's spirit: this queue is a
    # single-worker FIFO and one submission should not monopolize it.
    trials: int | None = Field(default=None, ge=2, le=500)
    # None -> a fresh exploration order each submission.
    seed: int | None = None


class RunRequest(BaseModel):
    """The shape of a submitted run. Semantics are BacktestConfig's.

    Field names are the condensed contract's (web/src/types/backtest.ts
    RunReq). The OLD names (sizing_model, strategy_params, fill_model,
    enforce_no_loss, profit_targets, n_jobs, search_strategy, n_trials,
    search_seed, search_direction) are still accepted and translated by
    server/contract.request -- a queued sweep in output/queue/state.json
    and any script written against them keep working.
    """

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
    targets: list[float] = Field(..., min_length=1, max_length=12)
    model: str = "fixed"
    params: dict[str, Any] = Field(default_factory=dict)
    fill: str = "close"
    no_loss: bool = True
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
    jobs: int | None = Field(default=None, ge=1, le=64)

    # HOW THE COMBINATION SPACE IS EXPLORED, not how big it is -- that is
    # still every enabled per-field "Sweep" checkbox (lib/sweepStrategies.ts
    # on the frontend, expand_strategy_params on the engine). Absent
    # (default) enumerates every combination exhaustively. Present samples
    # `trials` of them via Optuna's TPE sampler
    # (src/optimization/search_strategies.BayesianSearch) -- the same
    # engine `cli.py search` drives from a YAML config.
    bayes: BayesSearch | None = None
    # The objective Optuna optimizes toward AND the column the final
    # summary is sorted by -- one value serves both, so the ranked
    # output always agrees with what was actually searched for. Also
    # used to sort a plain grid sweep's summary. Restricted to columns
    # _simulate_single's own metrics dict actually carries (see
    # optimization_controller.py) -- "Sharpe Ratio" is NOT one of these;
    # it is computed later, only for display, and is not a valid target.
    rank_by: str = "Capital Velocity Index"
    minimize: bool = False

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_names(cls, data: Any) -> Any:
        return contract.request(data) if isinstance(data, dict) else data

    @property
    def is_bayesian(self) -> bool:
        return self.bayes is not None

    def wire(self) -> dict[str, Any]:
        """The request as persisted and echoed on a job's `req`."""
        return self.model_dump(exclude_none=True)


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
        "history_path": "data/XBI_1Min_sip_all_rth_2016-01-01_2026-09-11.csv",
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
    # UNVALIDATED PLACEHOLDER, AND CURRENTLY INFEASIBLE TO FIX. No
    # model exists at data/ml/models/URSP_regime_*; selecting this id
    # fails at ensure_model_available() with a clear ConfigurationError
    # naming that, per src/ml/regime_scaled_sizing.py's own lazy-load
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
    """The grid-step trigger methods a strategy supports, as the wire's Trigger.

    ``methods`` (display order; entry 0 is the default, a single entry is
    locked) lists what ``_grid_trigger_level`` actually does. ``control``
    names the strategy_param whose PRESENCE selects ``local_reference``.
    ``window.param`` is the strategy_param that IS the rolling-high window;
    ``window.seed`` is written to it the first time ``local_reference`` is
    picked (absent when it seeds itself, as hf's committed ``lookback_days``
    does). Absent keys mean none.
    """
    spec = _GRID_TRIGGER.get(strategy_id, _GRID_TRIGGER_LAST_BUY)
    out: dict[str, Any] = {"methods": list(spec["methods"])}
    if spec["controlled_by"] is not None:
        out["control"] = spec["controlled_by"]
    if spec["window_param"] is not None:
        window: dict[str, Any] = {"param": spec["window_param"]}
        if spec["window_default"] is not None:
            window["seed"] = spec["window_default"]
        out["window"] = window
    return out


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
    if request.params:
        return dict(request.params)
    return dict(STRATEGY_DEFAULTS.get(request.model, {}))


def build_config(request: RunRequest) -> BacktestConfig:
    """Validate a request the way the engine itself would.

    Raises ConfigurationError, which the caller turns into a 400. A bad
    strategy_id fails here with the list of real ones rather than as a
    KeyError somewhere inside a worker thread.
    """
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": request.model,
                "strategy_params": resolve_params(request),
            },
            "grid": {
                "steps": request.grid_steps,
                "profit_targets": request.targets,
            },
            "execution": {
                "fill_model": request.fill,
                "enforce_no_loss": request.no_loss,
            },
            "search": {
                "strategy": "bayesian" if request.bayes else "grid",
                "rank_by": request.rank_by,
                "direction": "minimize" if request.minimize else "maximize",
                "seed": request.bayes.seed if request.bayes else None,
            },
            # NO `live` SECTION, EVER. This process has no credentials and
            # no broker; accepting live settings from a browser would be
            # accepting them from anyone who can reach this port. The
            # capability test asserts this module names no broker.
        }
    )
    config.validate()
    strategy_class = resolve_strategy(config.strategy.strategy_id)  # fails loudly on a typo

    if request.bayes is not None and request.bayes.trials is None:
        raise ConfigurationError(
            "a bayesian search requires bayes.trials -- the whole reason to choose "
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
    is_bayesian = request.is_bayesian
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


def _combination_key(grid_step: Any, profit_target: Any, params: dict[str, Any]) -> str:
    """One configuration's identity, stable across a JSON round trip.

    Used to recognise a configuration already finished before a pause or
    restart. json with sorted keys rather than a tuple of the dict's
    items because the checkpointed side has been through json once and
    the live side has not -- serialising both the same way is what makes
    0.15 from a request and 0.15 read back from disk compare equal.
    """
    return json.dumps(
        [float(grid_step), float(profit_target), params], sort_keys=True, default=_native
    )


def _rank_key(row: dict[str, Any], rank_by: str, tie_break_by: str | None) -> tuple:
    """run_sweep's ordering -- descending, missing or NaN last -- as a sort key.

    Needed because a resumed run's rows no longer all come out of one
    run_sweep call, so the ranking has to be applied here, over rows that
    finished in different processes. Sorted with Python's stable sort, so
    among exact ties the configuration that finished FIRST ranks first --
    which _BestOnlySink below relies on to agree about which row is best.
    """

    def part(column: str | None) -> tuple[int, float]:
        if column is None:
            return (0, 0.0)
        try:
            value = float(row.get(column))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return (1, 0.0)
        return (1, 0.0) if math.isnan(value) else (0, -value)

    return (*part(rank_by), *part(tie_break_by))


class _ResumableSearch(SearchStrategy):
    """Wraps the real search: skips finished configurations, honours stops.

    The stop hook lives in suggest() because that is the one seam
    run_sweep already has that is consulted before EVERY new
    configuration, in both its sequential and parallel branches, and
    whose None already means "no more work" -- so a pause ends the sweep
    through the engine's own clean exit rather than an exception thrown
    through a process pool. progress_callback could not do this: run_sweep
    deliberately swallows anything it raises.
    """

    def __init__(
        self, inner: SearchStrategy, skip: set[str], should_stop: Callable[[], bool]
    ) -> None:
        self._inner = inner
        self._skip = skip
        self._should_stop = should_stop
        self.stopped = False

    def suggest(self) -> dict | None:
        # Checked BEFORE asking the inner search: BayesianSearch.suggest
        # opens an Optuna trial, and one opened and never run would be a
        # dangling trial in a study that is about to be abandoned anyway.
        if self._should_stop():
            self.stopped = True
            return None
        while True:
            suggestion = self._inner.suggest()
            if suggestion is None or not self._skip:
                return suggestion
            key = _combination_key(
                suggestion["grid_step"], suggestion["profit_target"], suggestion["strategy_params"]
            )
            if key not in self._skip:
                return suggestion

    def report(self, params: dict, result) -> None:
        self._inner.report(params, result)


class _BestOnlySink:
    """A run_sweep result sink: checkpoints every row, keeps ONE full result.

    THIS REPLACES return_full_results=True, AND THE REASON IS A CRASH.
    The report needs every configuration's metrics row but only the BEST
    configuration's full SimulationResult (its trade log and equity
    curve). run_backtest used to ask run_sweep to retain every result
    anyway, and on a full-history intrabar RSP run each one is ~35 MB --
    so a 1,536-configuration sweep needed ~54 GB. On 2026-09-13 the
    server process reached 31.4 GB on this 15 GB machine, Windows logged
    low-virtual-memory warnings for twenty minutes, and it bugchecked.
    run_sweep's own docstring had already recorded the same failure on a
    1,260-configuration run.

    Holding only the running best bounds a run at about two results
    however large it is. result_sink is the right seam because run_sweep
    hands it each (row, SimulationResult) in the parent process as the
    configuration lands; it is contractually forbidden from retaining the
    results, which this honours for every one but the current best.
    """

    def __init__(
        self,
        first_index: int,
        rank_by: str,
        tie_break_by: str | None,
        on_row: Callable[[dict[str, Any]], None] | None,
    ) -> None:
        self.rows: list[dict[str, Any]] = []
        self._first_index = first_index
        self._rank_by = rank_by
        self._tie_break_by = tie_break_by
        self._on_row = on_row
        self.best_index: int | None = None
        self.best_result = None
        self._best_key: tuple | None = None

    def record(self, row: dict[str, Any], sim_result, elapsed_ms: int) -> None:
        index = self._first_index + len(self.rows)
        self.rows.append(row)
        if self._on_row is not None:
            self._on_row(row)
        if sim_result is None:
            return
        key = _rank_key(row, self._rank_by, self._tie_break_by)
        # Strictly better only: an exact tie keeps the earlier row, the
        # same one the stable sort in run_backtest will put first.
        if self._best_key is None or key < self._best_key:
            self._best_key = key
            self.best_index = index
            self.best_result = sim_result


def run_backtest(
    request: dict[str, Any],
    report: Callable[[float, str], None],
    control: RunControl | None = None,
) -> dict[str, Any]:
    """Execute one submitted run. Called on the worker thread.

    `report` is the job queue's progress callback. Progress is per
    (ticker x configuration), which is as fine as the engine's own
    reporting allows -- run_sweep returns when it returns.

    `control`, when the queue passes one, makes the run resumable and
    stoppable: configurations it reports as already finished are skipped,
    every newly finished one is checkpointed through it, and once it says
    stop, no new configuration starts and RunStopped is raised after the
    ones in flight land. None -- a direct call from a script -- runs to
    completion exactly as before.
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
    bayesian = config.search.strategy == "bayesian"
    # What one ticker will actually evaluate. For a Bayesian run that is
    # the trial budget, not the size of the space -- measuring progress
    # against the space left a 200-trial search over 11,520 combinations
    # topping out at 1.7%.
    trials = parsed.bayes.trials if parsed.bayes else None
    per_ticker = trials if bayesian and trials else combinations
    total_units = max(1, per_ticker * len(available))
    finished_units = 0
    should_stop = control.should_stop if control is not None else (lambda: False)
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
        # False, deliberately -- see _BestOnlySink for the crash this was.
        kwargs["return_full_results"] = False
        kwargs["symbol"] = ticker
        rank_by = kwargs["rank_by"]
        tie_break_by = kwargs.get("tie_break_by")
        param_keys = sorted({key for params in kwargs["strategy_params_grid"] for key in params})

        # kwargs["search_strategy"] is still the bare string "bayesian"
        # at this point -- to_run_sweep_kwargs has no n_trials field to
        # put on it (BacktestConfig/SearchConfig has none; it is a
        # REQUEST-only concept, the web equivalent of cli.py search's
        # own --trials flag, not a YAML config field). Passed as a
        # string, _resolve_search_strategy would default the budget to
        # the FULL combination count -- see BayesianSearch's own
        # docstring on exactly this trap. Replaced here, per ticker,
        # with a real pre-configured instance carrying parsed.bayes.trials;
        # everything else it needs (grid_steps/profit_targets/
        # strategy_params_grid/rank_by/direction/seed) is already in
        # kwargs from to_run_sweep_kwargs, read back rather than
        # recomputed. One fresh BayesianSearch per ticker, matching how
        # a plain grid sweep already runs the identical combination
        # space once per ticker in this same loop.
        prior = control.completed_rows(ticker) if control is not None else []
        inner: SearchStrategy
        skip: set[str] = set()
        if kwargs["search_strategy"] == "bayesian":
            inner = BayesianSearch(
                kwargs["grid_steps"],
                kwargs["profit_targets"],
                kwargs["strategy_params_grid"],
                rank_by=rank_by,
                direction=kwargs["search_direction"],
                n_trials=trials,
                seed=kwargs["search_seed"],
            )
            expected = inner.n_trials
            if prior:
                # Replayed, not skipped: TPE legitimately proposes the same
                # configuration twice, so "already done" is a count against
                # the budget plus a history for the sampler, not a set.
                inner.seed_completed(
                    [
                        (
                            {
                                "grid_step": row.get("Grid Step"),
                                "profit_target": row.get("Profit Target"),
                                "strategy_params": {key: row.get(key) for key in param_keys},
                            },
                            None if "error" in row else row.get(rank_by),
                        )
                        for row in prior
                    ]
                )
        else:
            inner = GridSearch(
                kwargs["grid_steps"], kwargs["profit_targets"], kwargs["strategy_params_grid"]
            )
            expected = combinations
            if prior:
                # Only rows that belong to THIS grid, once each. A checkpoint
                # cannot outlive a change to its request today, but a row
                # counted twice would end the run one configuration short.
                in_grid = {
                    _combination_key(step, target, params)
                    for step in kwargs["grid_steps"]
                    for target in kwargs["profit_targets"]
                    for params in kwargs["strategy_params_grid"]
                }
                kept = []
                for row in prior:
                    key = _combination_key(
                        row.get("Grid Step"),
                        row.get("Profit Target"),
                        {k: row.get(k) for k in param_keys},
                    )
                    if key in in_grid and key not in skip:
                        skip.add(key)
                        kept.append(row)
                prior = kept

        remaining = max(0, expected - len(prior))
        jobs = choose_jobs(len(frame), max(1, remaining), parsed.jobs)
        kwargs["n_jobs"] = jobs
        controller = OptimizationController(historical_data=frame)
        search = _ResumableSearch(inner, skip, should_stop)
        sink = _BestOnlySink(
            first_index=len(prior),
            rank_by=rank_by,
            tie_break_by=tie_break_by,
            on_row=(
                (lambda row, _t=ticker: control.record_row(_t, row))
                if control is not None
                else None
            ),
        )
        if prior:
            report(
                (finished_units + len(prior)) / total_units,
                f"{ticker}: resuming -- {len(prior)}/{expected} configurations already done",
            )

        def on_combination(
            done: int,
            of: int,
            _base: int = finished_units,
            _t: str = ticker,
            _prior: int = len(prior),
            _expected: int = expected,
        ) -> None:
            # Bound as defaults so the closure reports THIS ticker's
            # offset even if it were ever called after the loop moved
            # on -- the same late-binding hazard the engine's own fill
            # closures bind against. `of` is run_sweep's view of the whole
            # space; _expected is what this ticker will really evaluate.
            finished = min(_prior + done, _expected)
            report((_base + finished) / total_units, f"{_t}: {finished}/{_expected} configurations")

        if remaining > 0:
            kwargs["search_strategy"] = search
            kwargs["result_sink"] = sink
            kwargs["progress_callback"] = on_combination
            try:
                controller.run_sweep(**kwargs)
            except ConfigurationError:
                # The one ConfigurationError that is not a real error: the
                # stop landed before a single new configuration ran, so
                # run_sweep had no rows to rank by. Anything else is real.
                if not search.stopped:
                    raise

        rows = prior + sink.rows
        if search.stopped and len(rows) < expected:
            raise RunStopped(f"{ticker}: stopped at {len(rows)}/{expected} configurations")

        # run_sweep's own rank_by / tie_break_by checks, applied to the
        # combined rows since the ranking now happens here.
        for column in (rank_by, tie_break_by):
            if column is not None and not any(column in row for row in rows):
                available_columns = sorted({key for row in rows for key in row})
                raise ConfigurationError(
                    f"rank_by column {column!r} not found in results. "
                    f"Available columns: {available_columns}"
                )
        order = sorted(range(len(rows)), key=lambda i: _rank_key(rows[i], rank_by, tie_break_by))
        summary = pd.DataFrame([rows[i] for i in order])

        # The best configuration by the engine's own default ranking -- the
        # row the UI is not re-ranking by a metric of its own invention.
        best = rows[order[0]]
        if sink.best_index == order[0] and sink.best_result is not None:
            result = sink.best_result
        else:
            # The best finished in an earlier attempt, so its full result
            # was never in THIS process. The engine is deterministic, so one
            # more configuration reproduces it exactly -- far cheaper than
            # checkpointing a ~35 MB trade log for every new leader.
            report(
                (finished_units + expected) / total_units,
                f"{ticker}: rebuilding the best configuration's trade log",
            )
            single = dict(kwargs)
            single.update(
                grid_steps=[best.get("Grid Step")],
                profit_targets=[best.get("Profit Target")],
                strategy_params_grid=[{key: best.get(key) for key in param_keys}],
                search_strategy=None,
                result_sink=None,
                progress_callback=None,
                return_full_results=True,
                n_jobs=1,
            )
            _, full = controller.run_sweep(**single)
            result = full[0]
        sink.best_result = None
        funds[ticker] = {
            # EVERY configuration, ranked -- metrics only. cells[0] IS the
            # configuration `fills` and `equity` below come from: its row
            # carries every figure result.metrics does (result_row spreads
            # them in), so it doubles as the fund's headline metrics
            # rather than those being sent twice. Carrying each cell's
            # fills as well would multiply the payload by the size of the
            # grid to draw a heatmap that needs one number per cell.
            "cells": [
                {
                    "grid": float(row["Grid Step"]),
                    "target": float(row["Profit Target"]),
                    # The resolved strategy-param combo THIS cell ran
                    # with -- distinct per cell once a strategy param is
                    # swept, so the sweep matrix/history can tell one
                    # combo's row from another's rather than showing the
                    # same (wrong) run-level value on every row.
                    "params": {key: _native(row[key]) for key in strategy_param_keys if key in row},
                    "m": fund_metrics(dict(row)),
                }
                for _, row in summary.iterrows()
            ],
            "fills": executions(result.trade_blotter),
            "equity": equity_series(result.equity_curve),
            "bars": {
                "start": pd.Timestamp(frame.index[0]).isoformat(),
                "end": pd.Timestamp(frame.index[-1]).isoformat(),
                "count": len(frame),
            },
        }
        # This ticker's combinations are done; the next one's callback
        # counts from here rather than restarting at zero.
        finished_units += per_ticker

    report(1.0, "assembling report")
    # A Report: RunMeta fields flat, then the funds.
    return {
        "id": "",  # filled in by the route from the job's own id
        # Descriptive only; None when the run was submitted unnamed or
        # with nothing but whitespace.
        "name": (parsed.name or "").strip() or None,
        "model": config.strategy.strategy_id,
        "fill": config.execution.fill_model,
        "no_loss": config.execution.enforce_no_loss,
        # The RESOLVED strategy parameters -- what the engine was actually
        # constructed with, after defaults were filled in and target_return
        # was aligned to the grid. A list where that argument was swept.
        # All values are plain numbers/strings/bools; nothing here needs a
        # custom encoder.
        "params": dict(config.strategy.strategy_params),
        "grid": config.grid.steps[0] if config.grid.steps else None,
        "target": config.grid.profit_targets[0] if config.grid.profit_targets else None,
        # What the run ACTUALLY used, not what was asked for, so a reader
        # can tell a slow sweep from a serial one.
        "jobs": jobs,
        "start": min((f["bars"]["start"] for f in funds.values()), default=None),
        "end": max((f["bars"]["end"] for f in funds.values()), default=None),
        "interval": "1Min",
        "funds": funds,
    }


def _archive(job) -> None:
    """Write a completed run to the history directory.

    Stamped with its own id first: run_backtest cannot know the id --
    the queue mints it after the request is built -- and a stored report
    whose id was the empty string would be unloadable by the very
    endpoint that serves it back.
    """
    history.save(job.run_id, _with_id(job.snapshot(), job.run_id))


# DURABLE: pending runs, their order and per-configuration checkpoints
# survive a restart under VAI_QUEUE_DIR. Restored by server/app.py's
# startup hook, never at import -- see JobQueue.restore.
queue = JobQueue(runner=run_backtest, on_complete=_archive, store=QueueStore())


@router.get("/funds")
def funds() -> dict[str, Any]:
    """What can actually be backtested on this machine: a Catalog.

    Reports presence rather than filtering it out: a UI that silently
    omits SPY is indistinguishable from one that has never heard of it,
    and the fix (`cli.py fetch-data`) is worth naming.

    `models` is keyed by strategy id and carries each model's constructor
    schema and grid-trigger methods. Served rather than hard-coded in the
    bundle so the two cannot drift -- the frontend carries no idea of its
    own about what a strategy's constructor looks like. What used to be a
    separate `sizing_details` (required names, committed defaults) is the
    params' own `required` / `suggested`.
    """
    return {
        "funds": [
            {"ticker": ticker, "path": path, "ok": Path(path).exists()}
            for ticker, path in sorted(KNOWN_DATA.items())
        ],
        "models": {
            name: {
                "params": _safe_describe(name, cls)["params"],
                "trigger": describe_grid_trigger(name),
            }
            for name, cls in sorted(STRATEGIES.items())
        },
    }


def bar_rows(frame: pd.DataFrame, times: Any) -> list[list[float]]:
    """OHLCV rows as [t, o, h, l, c, v] tuples -- about a third of the bytes
    of one keyed object per bar, on a payload of thousands of bars."""
    return [
        [t, float(o), float(h), float(lo), float(c), float(v)]
        for t, o, h, lo, c, v in zip(
            times,
            frame["open"],
            frame["high"],
            frame["low"],
            frame["close"],
            frame["volume"],
            strict=True,
        )
    ]


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
    not offer. Both answer with the same Bars shape.

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
        return {"bucket_s": 60, "rows": 0, "bars": []}

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
        "bucket_s": minutes * 60,
        "rows": source_rows,
        "bars": bar_rows(rolled, (int(ts.timestamp()) for ts in rolled.index)),
    }


@router.get("/history")
def history_rows() -> dict[str, Any]:
    """Every completed run: run-level fields once, then one row PER CELL.

    A run can hold several funds and each fund several configurations,
    so "rank the runs" is the wrong shape -- the thing worth comparing
    is a (run, fund, grid step, profit target, params) cell and its
    metrics. Flattening here means the client sorts an array rather than
    walking a tree to find comparable numbers.

    The run-level fields (name, model, fill, window, ...) are NOT
    repeated on every row: a 1,536-cell sweep would otherwise carry them
    1,536 times. `runs[row.run]` joins them back.

    Ranking itself is deliberately NOT done here. The metric is the
    reader's choice and changing it should be instant, not a round trip.
    """
    runs: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for run in history.load_all():
        report = run.get("report")
        if not isinstance(report, dict):
            continue
        run_id = run["id"]
        runs[run_id] = {
            **{key: value for key, value in report.items() if key not in ("id", "funds")},
            "saved_at": run.get("saved_at"),
        }
        for ticker, fund in (report.get("funds") or {}).items():
            count = (fund.get("bars") or {}).get("count")
            for index, cell in enumerate(fund.get("cells") or []):
                # rank: where the ENGINE ranked this cell; 0 is its own
                # pick, so a reader can see when their chosen metric
                # disagrees with it.
                rows.append({**cell, "run": run_id, "ticker": ticker, "rank": index, "bars": count})
    return {"runs": runs, "rows": rows}


@router.get("/runs")
def runs() -> dict[str, Any]:
    """Every run this server has seen, newest first, plus whether the queue
    is paused.

    Each snapshot carries its own `pos`; the order a client should show
    pending runs in is that, not submission order -- the two differ the
    moment anything has been moved.
    """
    return {"runs": [job.snapshot() for job in queue.all()], "paused": queue.paused}


@router.get("/runs/{run_id}")
def run(run_id: str) -> dict[str, Any]:
    """One run: the live queue's snapshot, else the archived copy.

    A completed run outlives the process that made it, so a restart must
    not turn a link someone saved into a 404.
    """
    job = queue.get(run_id)
    if job is not None:
        return _with_id(job.snapshot(), run_id)
    stored = history.load(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No run {run_id!r}.")
    return stored


@router.post("/runs", status_code=202)
def submit(request: RunRequest) -> dict[str, Any]:
    """Queue a run. Returns immediately with its snapshot.

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

    job = queue.submit(request.wire())
    return _with_id(job.snapshot(), job.run_id)


# ---------------------------------------------------------------------
# QUEUE CONTROLS
#
# One route per target: POST /runs/{id} with an `op`, and POST /queue.
# Every run action answers with the job's new snapshot, so a client can
# render the result of what it asked for without a second request.
#
# Pause and cancel on a RUNNING job are requests: the job keeps running
# until the configurations already handed to the process pool finish
# (up to about a minute on a full-history run), and its status reads
# "pausing" / "cancelling" meanwhile. That is the engine's clean exit
# rather than a killed worker, and it is why a paused run loses nothing
# -- see server/jobs.py's module docstring.
#
# 404 for an id this server has never queued; 409 for an action that does
# not apply to the job's current state (cancelling a completed run,
# moving a running one). Neither is a 400: the request is well-formed,
# the target is simply in the wrong state or absent.
# ---------------------------------------------------------------------


class RunOp(BaseModel):
    """What to do to one run.

    pause   queued: paused at once. running: after its in-flight batch.
    resume  paused: back in the queue at its place, from its checkpoint.
    cancel  queued/paused: at once. running: after its in-flight batch.
            Discards the checkpoint -- there is nothing to come back to.
    next    to the front of the pending order, resuming it if paused.
    move    to `pos` among pending runs (0 = next, larger = later, clamped).
    """

    op: Literal["pause", "resume", "cancel", "next", "move"]
    pos: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _move_needs_a_position(self) -> RunOp:
        if self.op == "move" and self.pos is None:
            raise ValueError("op 'move' requires pos")
        return self


@router.post("/runs/{run_id}")
def control_run(run_id: str, body: RunOp) -> dict[str, Any]:
    actions: dict[str, Callable[[], Any]] = {
        "pause": lambda: queue.pause(run_id),
        "resume": lambda: queue.resume(run_id),
        "cancel": lambda: queue.cancel(run_id),
        "next": lambda: queue.run_next(run_id),
        "move": lambda: queue.move(run_id, body.pos or 0),
    }
    try:
        job = actions[body.op]()
    except UnknownRun as exc:
        raise HTTPException(
            status_code=404, detail=f"No queued or running run {run_id!r}."
        ) from exc
    except QueueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _with_id(job.snapshot(), run_id)


class QueueState(BaseModel):
    paused: bool


@router.post("/queue")
def set_queue(body: QueueState) -> dict[str, Any]:
    """paused=true: stop starting runs; the running one pauses after its
    in-flight batch. paused=false: start again, resuming whatever the
    queue pause paused."""
    if body.paused:
        queue.pause_all()
    else:
        queue.resume_all()
    return {"paused": queue.paused}


class ValidateError(BaseModel):
    """One thing wrong with a would-be run, attached to a field when it
    can be, so the form can render it under the offending input."""

    field: str | None = None
    msg: str

    def wire(self) -> dict[str, Any]:
        return {"msg": self.msg} if self.field is None else {"field": self.field, "msg": self.msg}


def _validation(
    errors: list[ValidateError],
    resolved: dict[str, Any] | None = None,
    aligned: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A Validation. Valid exactly when `errors` is empty.

    resolved  the parameters the engine would actually build with --
              defaults filled in, target_return aligned
    aligned   the subset of `resolved` the server set or changed relative
              to what was submitted (today: target_return)
    """
    out: dict[str, Any] = {"errors": [error.wire() for error in errors]}
    if resolved is not None:
        out["resolved"] = resolved
    if aligned:
        out["aligned"] = aligned
    return out


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
                ValidateError(field=name if name in names else None, msg=message)
                for name in missing
            ]
    # The multi-target refusal names `target_return` in passing ("reaching
    # one target_return, so it cannot sweep ..."), but it is about the
    # profit-target GRID, not a constructor argument -- leave it
    # unattached so the form shows it as a banner, not under a locked
    # field the user cannot change to fix it.
    if "cannot sweep" in message and "profit target" in message:
        return [ValidateError(field=None, msg=message)]
    return [ValidateError(field=_error_field(message, names), msg=message)]


@router.post("/validate")
def validate(request: RunRequest) -> dict[str, Any]:
    """Dry-run the exact validation `submit` runs, without queuing.

    The form calls this while the operator types so a bad parameter is a
    red line under a field, not a 400 on click or a job that dies twenty
    seconds later. It goes through the SAME `build_config(request)` the
    submit path uses -- there is no second definition of "valid" to
    drift -- and `build_config` opens no store, imports no broker and
    touches neither the queue nor history (the capability test holds
    this module to that). Always HTTP 200: the errors are the payload,
    which is easier to consume from a debounced keystroke than a 400.

    DELIBERATELY ITS OWN ROUTE, not `POST /runs?dry_run=1`: a server that
    predated the flag would ignore it and QUEUE the run being validated.
    """
    submitted = dict(request.params)
    strategy_class = STRATEGIES.get(request.model)
    names = (
        [spec["name"] for spec in _safe_describe(request.model, strategy_class)["params"]]
        if strategy_class is not None
        else []
    )
    try:
        config = build_config(request)
    except ConfigurationError as exc:
        return _validation(_explode_error(str(exc), names))
    except Exception as exc:
        return _validation([ValidateError(field=None, msg=str(exc))])

    resolved = dict(config.strategy.strategy_params)
    aligned = {
        key: value
        for key, value in resolved.items()
        if key not in submitted or submitted[key] != value
    }
    return _validation([], resolved=resolved, aligned=aligned)


@router.websocket("/ws/{run_id}")
async def run_socket(socket: WebSocket, run_id: str) -> None:
    """Stream one run as Frame<Run>: its state on every change, then close.

    Blocks on the job queue's Condition rather than polling, so an
    update is delivered when it happens. Sends the current state first,
    because a client that connects after a fast run finished must not
    wait forever for an event that has already passed.
    """
    await socket.accept()
    job = queue.get(run_id)
    if job is None:
        await socket.send_json({"t": "err", "msg": f"No run {run_id!r}."})
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
                await socket.send_json({"t": "err", "msg": f"No run {run_id!r}."})
                return
            if current.revision == seen:
                await socket.send_json({"t": "hb"})
                continue
            seen = current.revision
            await socket.send_json({"t": "data", "d": _with_id(current.snapshot(), run_id)})
            if current.status in TERMINAL:
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
        report["id"] = run_id
    return snapshot


__all__ = [
    "RunOp",
    "RunRequest",
    "bar_rows",
    "build_config",
    "describe_grid_trigger",
    "describe_params",
    "queue",
    "router",
    "run_backtest",
]
