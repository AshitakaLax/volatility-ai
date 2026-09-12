"""Grid sizing and grid SPACING driven by a daily regime model.

Two things change, and the split between them is the design:

    the regime score decides WHEN to buy   (it widens the grid step)
    the volatility forecast decides HOW MUCH (it shrinks the lot)

--------------------------------------------------------------------
THIS IS THE FIRST STRATEGY IN THIS PROJECT TO MOVE THE TRIGGER

Everything in src/ml/ before it was explicitly forbidden from doing so.
src/ml/reachability_sizing.py's own docstring is emphatic: "This
changes ONE thing: how much a confirmed grid buy is worth. It does not
decide WHETHER to buy (the grid trigger is untouched)". This class
does move it, so the reasoning has to be better than that one's, and
the safety argument has to be made rather than inherited.

WHY IT IS DEFENSIBLE HERE. Widening the step in a crash is not a
directional bet, it is a spacing decision, and its two outcomes are
asymmetric in the safe direction:

  * Model right, market falls hard: lots are spaced 3-5% apart instead
    of 1%, so the same cash reaches far deeper, average cost basis is
    lower, and fewer lots strand above the eventual recovery. Under
    enforce_no_loss a stranded high-basis lot is not a paper loss that
    mean-reverts on its own schedule -- it is inventory that CANNOT be
    sold, ever, until price returns above it. That failure mode is
    already documented as real in this codebase (see
    reachability_sizing.py, "THE STRANDING RISK", and
    tools/simulate_full_length.py on 4 of 5 strategies stranding for a
    decade), and wider spacing in the fall is a direct attack on it.
  * Model wrong, the dip was ordinary: some buys are skipped that
    would have harvested. That is FOREGONE PROFIT, not a realized
    loss, and it is the same asymmetry every other model-driven
    strategy here already accepts by letting confidence shrink size
    toward zero but never grow it.

WHY THE PROJECT'S OWN "FASTER IS WORSE" FINDING DOES NOT VETO IT.
tools/probe_regime_signals.py measured every attempt to beat SMA200's
latency with a quicker signal making 2022 WORSE, not better -- EMA20
-65.0%, SMA50 -51.5%, RSI(14) -65.7% against SMA200's -19.8% -- and
concluded "latency was the wrong diagnosis". That finding is real and
it is about a BINARY IN-OR-OUT shell: fully long when bull, fully cash
when bear, where one false bear signal forfeits an entire trend and a
leveraged fund decays through every whipsaw. The cost of being wrong
there is unbounded upside forgone. Here a false crash reading skips a
few rungs of a dip ladder and the book stays invested throughout. The
mechanism that made fast signals lose money in that shell is not
present in this one -- but it is close enough that the hysteresis
below is not optional.

--------------------------------------------------------------------
HYSTERESIS, AND WHY THE RESPONSE IS BINARY RATHER THAN GRADED

A score that oscillates around one threshold would oscillate the grid
level with it, and a trigger level that moves non-monotonically
bar-to-bar is path-dependent noise: the same price path buys or does
not buy depending on which side of the line the model happened to land
on that minute. Two separate thresholds (enter high, exit low) make the
crash state STICKY, so leaving it requires a genuine move rather than a
rounding difference.

The widening itself is a step function, not a curve, and that is a
statement about the evidence rather than a simplification. This
project's own measured model quality is weak -- held-out AUCs of
0.57-0.60 for the reachability line, and ml_plan.md is explicit that
"absolute AUCs of 0.52-0.63 are weak in any case, and none of this has
yet been connected to money". reachability_sizing.py declined a
cleverer calibration curve on exactly that basis. A model that
weak supports "widen or do not"; it does not support a smooth mapping
from score to step width, which would be inventing precision the
evidence has not earned.

--------------------------------------------------------------------
NOTHING HERE CAN SELL

adjust_profit_target and lots_to_liquidate are NOT overridden, so they
keep SizingStrategy's defaults (None for every lot, empty for every
bar). This class cannot move an exit, cannot close a position, and
cannot realize a loss -- the no-loss guard is not even reached by
anything it does. Every effect it has runs through two methods that
only ever propose a BUY: _grid_trigger_level and calculate_trade_value.

That is deliberate and worth keeping. A regime model good enough to
size entries is not thereby good enough to liquidate a book, and
src/trading/decision_cycle.collect_liquidations already gates signal
exits behind a separate config flag for that reason.

--------------------------------------------------------------------
UNMEASURED AS OF THIS COMMIT

No sweep, walk-forward or paired test has been run on this strategy.
Every number above is either a measurement of something ELSE in this
repo (cited where used) or an argument about mechanism. The bar
ml_plan.md sets is explicit -- "a model must beat hf_local_reference"
-- and this has not been held to it yet. Treat it as a hypothesis with
an implementation, not as a validated configuration, and do not put it
in a `live:` config before running tools/ the way every other strategy
here was.
"""

from __future__ import annotations

import math
from pathlib import Path

from src.core.exceptions import ConfigurationError
from src.ml.qlib_regime import NO_READING, RegimeInferenceSource, RegimeReading
from src.strategies.market_context import MarketContext
from src.strategies.size_calculators import _BaselineScaledStrategy
from src.strategies.sizing_indicators import clamp


class MLRegimeScaledSizing(_BaselineScaledStrategy):
    """max_trade_pct, scaled by regime/vol, on a grid that widens in a
    predicted crash."""

    def __init__(
        self,
        max_trade_pct: float,
        ticker: str,
        *,
        crash_step_multiplier: float = 4.0,
        regime_enter_threshold: float = 0.30,
        regime_exit_threshold: float = 0.20,
        regime_floor: float = 0.25,
        drawdown_response: float = 0.0,
        vol_reference: float | None = None,
        vol_floor: float = 0.35,
        model_dir: str = "data/ml/models",
        external_dir: str | None = None,
        min_sessions: int = 60,
        history_path: str | None = None,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        """Configure the regime response.

        crash_step_multiplier -- what the grid step is multiplied BY
            while latched into the crash state. 4.0 against a 1% step
            gives the 4% spacing the deep-dip work in
            tools/probe_downturn_tactics.py operated at. 1.0 disables
            widening entirely and leaves only the sizing response, which
            is the way to test the two halves separately rather than
            changing both at once.

        regime_enter_threshold / regime_exit_threshold -- the hysteresis
            band. enter > exit is required; equal thresholds would be a
            single line and reintroduce exactly the flapping the band
            exists to prevent.

            THESE ARE NOT "PROBABILITIES THAT SOUND HIGH". Read them off
            the model's own score_quantiles sidecar -- p90 to p95 is the
            usual starting point. A calibrated classifier trained on a
            ~15% base rate emits scores that cluster near 15%, so a
            threshold of 0.65 is not "strict", it is unreachable, and
            the strategy would trade as a plain grid while looking
            regime-aware. _check_threshold_is_reachable() refuses that
            at load time rather than letting it run silently, and the
            0.30 default here is a PLACEHOLDER to be re-derived per
            model, not a recommendation.

        regime_floor -- the smallest fraction of the ceiling a lot may
            be scaled to by the regime term. Also what is used before
            the model is warm, matching reachability_sizing.py's
            confidence_floor convention: an unwarmed model
            under-allocates rather than betting on a reading it does
            not have.

        drawdown_response -- SIGNED, and defaults to 0.0 (inert), the
            same opt-in convention inverse_scale_kappa uses.
              > 0 de-risks: full size when flat, shrinking as the book
                  draws down.
              < 0 escalates: full size only once the book HAS drawn
                  down. This is the direction this project's own
                  measurements favour -- tools/probe_regime_integrated.py
                  scales the bear leg's lot up with drawdown, and
                  tools/probe_downturn_tactics.py's escalating dip book
                  was positive in 14 of 14 episodes -- but it is
                  expressed as a SHRINK from the ceiling rather than a
                  growth past it, because no multiplier in this codebase
                  may exceed 1.0. Set max_trade_pct to the size you want
                  at the BOTTOM and this scales the shallow rungs down
                  from it.

        vol_reference -- the annualized forward vol at which the
            volatility term starts biting, e.g. 0.45. None disables the
            term. Above it the lot shrinks toward vol_floor. This is the
            forward-looking generalization of the one filter this
            project has actually measured working
            (tools/probe_vol_filtered_regime.py: 20-day realized vol
            under its trailing 250-day 75th percentile), which is why
            the vol term is graded where the step response is binary --
            the underlying evidence is stronger.
        """
        super().__init__(max_trade_pct, baseline_price, inverse_scale_kappa)

        if crash_step_multiplier < 1.0:
            raise ConfigurationError(
                f"crash_step_multiplier must be >= 1.0 (a crash widens the grid, it never "
                f"tightens it), got {crash_step_multiplier}"
            )
        if not 0.0 <= regime_exit_threshold < regime_enter_threshold <= 1.0:
            raise ConfigurationError(
                f"need 0 <= regime_exit_threshold ({regime_exit_threshold}) < "
                f"regime_enter_threshold ({regime_enter_threshold}) <= 1. Equal thresholds are "
                "a single line, which is what the hysteresis band exists to avoid."
            )
        if not 0.0 <= regime_floor <= 1.0:
            raise ConfigurationError(f"regime_floor must be in [0, 1], got {regime_floor}")
        if not 0.0 <= vol_floor <= 1.0:
            raise ConfigurationError(f"vol_floor must be in [0, 1], got {vol_floor}")
        if vol_reference is not None and vol_reference <= 0.0:
            raise ConfigurationError(
                f"vol_reference is an annualized volatility and must be positive, got "
                f"{vol_reference}. Pass None to disable the volatility term."
            )
        if not ticker:
            raise ConfigurationError("MLRegimeScaledSizing requires ticker (e.g. 'XBI')")

        # Read back by optimization_controller._simulate_single, which
        # refuses a run whose symbol disagrees -- the same guard
        # MLReachabilitySizing.ticker gets, for the same reason: a
        # per-instrument model pointed at another instrument's bars is
        # confidently answering the wrong question.
        self.ticker = ticker
        self.crash_step_multiplier = crash_step_multiplier
        self.regime_enter_threshold = regime_enter_threshold
        self.regime_exit_threshold = regime_exit_threshold
        self.regime_floor = regime_floor
        self.drawdown_response = drawdown_response
        self.vol_reference = vol_reference
        self.vol_floor = vol_floor

        # THE MODEL IS LOADED LAZILY, AND THAT IS A DEPARTURE FROM
        # MLReachabilitySizing, WHICH LOADS IN ITS CONSTRUCTOR.
        #
        # Constructing a sizing strategy is not only something a RUN
        # does. server/backtest.py's describe_params() and the /funds
        # response instantiate every registered strategy just to
        # introspect its signature and render a form; so does
        # tests/unit/test_backtest_param_schema.py. Requiring a trained
        # binary artifact -- which lives under gitignored data/ and is
        # absent on any fresh clone or CI runner -- in order to draw a
        # number field is the wrong coupling, and it is already a latent
        # failure for the reachability ids on a machine that has not run
        # tools/train_ml_model.py.
        #
        # This does NOT weaken "validate front-loaded". Every numeric
        # argument above is still checked here, at construction. What
        # moves is only the disk read, and the place a live deployment
        # should catch a missing artifact is tools/preflight.py, which
        # docs/DEPLOY_RASPBERRY_PI.md already requires to be all-`ok`
        # before trading -- call ensure_model_available() from there.
        self._source_kwargs = {
            "model_dir": Path(model_dir),
            "external_dir": external_dir,
            "min_sessions": min_sessions,
            # Bars from before the run, so the model is scored on the
            # run's FIRST session rather than 60 sessions in. See
            # RegimeInferenceSource.__init__ for the measurement that
            # made this necessary rather than nice.
            "history_path": history_path,
        }
        self._source: RegimeInferenceSource | None = None
        self._reading: RegimeReading = NO_READING
        # The latch. False = ordinary grid, True = widened. Persisted
        # across bars on purpose; that persistence IS the hysteresis.
        self._in_crash = False

    def ensure_model_available(self) -> RegimeInferenceSource:
        """Load the model now, raising ConfigurationError if it is absent.

        Called on the first record_tick, and callable directly by a
        startup check that wants the failure BEFORE a session begins
        rather than on its first bar -- which is what tools/preflight.py
        is for. Idempotent.
        """
        if self._source is None:
            source = RegimeInferenceSource(self.ticker, **self._source_kwargs)
            self._check_threshold_is_reachable(source)
            self._source = source
        return self._source

    def _check_threshold_is_reachable(self, source: RegimeInferenceSource) -> None:
        """Refuse a threshold this model's output never reaches.

        THE SILENT-INERTNESS FAILURE THIS EXISTS TO PREVENT. A
        calibrated classifier trained on a base rate of ~15% emits
        probabilities that cluster near 15%. Measured on the synthetic
        check in tools/train_qlib_regime.py's own run: p99 = 0.258, max
        = 0.258. An operator setting regime_enter_threshold = 0.65 --
        because 0.65 reads like "probably a crash" -- would get a
        strategy that loads a model, computes a score every session,
        latches never, and trades EXACTLY like the plain grid while
        appearing to be regime-aware.

        That is the worst available outcome: not a wrong answer, but a
        feature that is inert in a way no metric shows. So it is a
        startup error naming the actual distribution, not a warning.

        Only p99 is used as the bar rather than max, because max is one
        observation and a slightly higher threshold than the single
        highest historical score is a legitimate, if aggressive, choice.
        Above p99 it is not a choice, it is a misunderstanding.
        """
        quantiles = source.score_quantiles
        if not quantiles:
            # A model trained before quantiles were recorded. Unknown is
            # not unreachable -- do not block on missing evidence.
            return
        ceiling = quantiles.get("p99")
        if ceiling is None or self.regime_enter_threshold <= ceiling:
            return
        shown = ", ".join(
            f"{k}={quantiles[k]:.3f}" for k in ("p50", "p90", "p95", "p99", "max") if k in quantiles
        )
        raise ConfigurationError(
            f"MLRegimeScaledSizing({self.ticker}): regime_enter_threshold="
            f"{self.regime_enter_threshold} is above this model's 99th-percentile output "
            f"({ceiling:.3f}), so the crash latch would never engage and the strategy would "
            f"trade as a plain grid while appearing regime-aware. Measured output "
            f"distribution: {shown}. Pick a threshold from those quantiles (p90-p95 is the "
            f"usual starting point), not from what a probability 'should' look like -- a "
            f"calibrated model on a low base rate never emits a high number."
        )

    # ---------------------------------------------------------------
    # Phase 1 of the decision cycle
    # ---------------------------------------------------------------

    @staticmethod
    def _reading_from_context(context: MarketContext) -> RegimeReading | None:
        """A reading injected through MarketContext, or None.

        The context wins when it carries one. That ordering matters: a
        caller that has gone to the trouble of populating the field
        (a precomputed per-bar array, a test fixture, some future
        engine-side pass) has made an explicit statement about what this
        bar's regime is, and silently preferring this class's own
        inference would make that statement inert -- the hardest kind of
        bug to see, because both paths produce plausible numbers.

        Both fields default to -1.0, which is outside the valid range of
        each and cannot be confused with a real reading. See
        MarketContext's own note on why the sentinel is -1.0 and not
        0.0.
        """
        if context.qlib_regime_score < 0.0 and context.expected_volatility < 0.0:
            return None
        return RegimeReading(
            crash_probability=context.qlib_regime_score,
            expected_volatility=context.expected_volatility,
            as_of=context.timestamp.date(),
            warm=True,
        )

    def record_tick(self, context: MarketContext) -> None:
        """Fires every bar. Advances the session clock, refreshes the
        reading, and updates the latch.

        The latch is updated HERE rather than inside
        _grid_trigger_level, and that is not a stylistic choice.
        _grid_trigger_level is called once per bar in the close-only
        path but is also called by the intrabar fill model
        (src/optimization/intraday_validation.py) to price a resting
        limit order; a method that mutated state would then produce a
        different grid depending on which fill model was running. Every
        state change in this class happens in record_tick, which
        src/trading/decision_cycle.py guarantees fires exactly once per
        bar in all three paths.
        """
        self._capture_baseline(context.price)

        injected = self._reading_from_context(context)
        if injected is not None and self._source is None:
            # Fully-injected mode: every reading arrives through
            # MarketContext, so no model is needed and none is loaded.
            # This is what makes the strategy testable, and replayable
            # against a precomputed per-bar series, without artifacts on
            # disk. The moment ONE bar arrives without an injected
            # reading, the branch below loads the model as usual.
            self._reading = injected
        else:
            source = self.ensure_model_available()
            # Drive the source even when a reading was injected, so its
            # session clock and rolling features stay warm. A caller may
            # inject on some bars and not others, and a source that had
            # stopped observing would be cold exactly when needed again.
            observed = source.observe(context.timestamp, context.high, context.low, context.close)
            self._reading = injected if injected is not None else observed

        self._update_latch(self._reading)

    def _update_latch(self, reading: RegimeReading) -> None:
        """Two thresholds, one sticky state."""
        score = reading.crash_probability
        if score < 0.0:
            # No reading. Hold whatever the latch already said rather
            # than resetting it: a model that goes briefly unavailable
            # mid-crash must not quietly re-tighten the grid.
            return
        if self._in_crash:
            if score <= self.regime_exit_threshold:
                self._in_crash = False
        elif score >= self.regime_enter_threshold:
            self._in_crash = True

    # ---------------------------------------------------------------
    # Phase 3: WHEN to buy
    # ---------------------------------------------------------------

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """The base level, with the step widened while latched.

        OVERRIDING THIS RATHER THAN _check_grid_trigger IS DELIBERATE
        AND IS THE WHOLE POINT. SizingStrategy's own docstring says so:
        the intrabar fill model needs the trigger as a VALUE, not a
        boolean, because it compares the level against the bar's LOW to
        decide whether a resting limit order was touched and then fills
        AT that level. A subclass that overrode only _check_grid_trigger
        would widen the grid in close-only backtests and in live, and
        leave the intrabar path silently filling at the UNWIDENED level
        -- two fill models disagreeing about where this strategy's
        orders sit, which is the exact bug the base class split these
        two methods to prevent. _check_grid_trigger is not overridden
        here at all; it routes through this method already.
        """
        return last_buy_price * (1.0 - step * self.step_multiplier)

    @property
    def step_multiplier(self) -> float:
        """1.0 normally, crash_step_multiplier while latched.

        A property rather than a private method because it is the single
        most useful thing to assert in a test and to print in a
        diagnostic, and because a caller reading it cannot accidentally
        change the latch by asking.
        """
        return self.crash_step_multiplier if self._in_crash else 1.0

    # ---------------------------------------------------------------
    # Phase 4: HOW MUCH to buy
    # ---------------------------------------------------------------

    def _regime_multiplier(self) -> float:
        """Linear from 1.0 at score 0 down to regime_floor at score 1."""
        score = self._reading.crash_probability
        if score < 0.0:
            # Unwarmed or unavailable: the conservative end, matching
            # reachability_sizing.py's confidence_floor behavior.
            return self.regime_floor
        return self.regime_floor + (1.0 - clamp(score, 0.0, 1.0)) * (1.0 - self.regime_floor)

    def _volatility_multiplier(self) -> float:
        """Shrink toward vol_floor as the forecast exceeds vol_reference."""
        if self.vol_reference is None:
            return 1.0
        forecast = self._reading.expected_volatility
        if forecast < 0.0:
            return 1.0
        if forecast <= self.vol_reference:
            return 1.0
        # Reciprocal rather than linear so the term decays smoothly and
        # never reaches zero on its own -- a forecast twice the
        # reference halves the lot, four times quarters it, and the
        # floor catches the tail.
        return clamp(self.vol_reference / forecast, self.vol_floor, 1.0)

    def _drawdown_multiplier(self, drawdown: float) -> float:
        """Signed response to the BOOK's drawdown. See __init__."""
        k = self.drawdown_response
        if k == 0.0:
            return 1.0
        dd = clamp(drawdown, 0.0, 1.0)
        if k > 0.0:
            return math.exp(-k * dd)
        # Escalating. Full size at a total drawdown, scaled down from
        # the ceiling everywhere shallower -- expressed as a shrink so
        # the "no multiplier exceeds 1.0" invariant in
        # _BaselineScaledStrategy.calculate_trade_value still holds.
        return math.exp(-abs(k) * (1.0 - dd))

    def _model_multiplier(self, context: MarketContext) -> float:
        """All three terms, multiplied.

        Multiplicative for the reason _BaselineScaledStrategy states:
        each factor can only REDUCE exposure, so no term can compensate
        for another's caution. A crash reading and a high vol forecast
        stack rather than averaging out.
        """
        combined = (
            self._regime_multiplier()
            * self._volatility_multiplier()
            * self._drawdown_multiplier(context.drawdown)
        )
        return clamp(combined, 0.0, 1.0)

    # ---------------------------------------------------------------

    def diagnostics(self) -> dict[str, float | bool | str | None]:
        """Current model state, for logging and the UI.

        Deliberately outside the SizingStrategy contract (the same way
        other strategies here treat it) so nothing in the decision cycle
        depends on it existing.
        """
        return {
            "ticker": self.ticker,
            "crash_probability": self._reading.crash_probability,
            "expected_volatility": self._reading.expected_volatility,
            "reading_as_of": str(self._reading.as_of) if self._reading.as_of else None,
            "in_crash": self._in_crash,
            "step_multiplier": self.step_multiplier,
            "regime_multiplier": self._regime_multiplier(),
            "volatility_multiplier": self._volatility_multiplier(),
        }


__all__ = ["MLRegimeScaledSizing"]
