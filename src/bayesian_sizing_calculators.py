"""
BayesianDualScaleSizing -- position sizing from a conjugate posterior.

--------------------------------------------------------------------
ON THE NAME, because it has meant two different things in this repo.

CHANGELOG.md records the original reading: "macro" in this strategy's
name refers to "a long-window Bayesian posterior -- a lookback-length
distinction", NOT to macroeconomic data. So "dual scale" means TWO
TIMESCALES, and that is what this implements: two posteriors over the
same latent quantity, differing only in how fast they forget.

A later technical design document proposed something different under
the same name -- a multiplicative ensemble of an exponential drawdown
term with a Gaussian or RSI multiplier -- and stated plainly in its
own Section 4 that those formulas involve "no explicit prior
distribution, likelihood, posterior update, or Bayesian parameter
estimation". That ensemble's mathematics is implemented, and is
genuinely useful, but it lives in src/size_calculators.py as
BellCurveProbabilitySizing and RsiMomentumSizing, where the names do
not claim inference that is not happening.

This module does the inference. There is no canonical published
"Bayesian Dual-Scale Sizing" algorithm; what follows is standard
conjugate Beta-Bernoulli machinery with exponential forgetting,
applied to this repository's actual decision. It is a reasoned design,
not a recovered specification.
--------------------------------------------------------------------
THE INFERENCE PROBLEM

Given the evidence so far, what is the probability that a lot bought
now reaches its profit target within the horizon? Allocate in
proportion to a CONSERVATIVE estimate of that probability.

Latent parameter: p, the success probability.
Prior:            Beta(alpha0, beta0).
Likelihood:       each resolved trial is one Bernoulli observation.
Posterior:        Beta(alpha, beta), conjugate and closed-form.

--------------------------------------------------------------------
THE LOOKAHEAD TRAP, which is the single most important property here.

A trial started at bar t cannot be scored until bar t+H, because
whether price reached the target within the horizon is not knowable
before then. If a resolved trial were credited to the posterior at the
bar it STARTED, every sizing decision would be reading its own future
and the backtest would be worthless in a way that flatters it.

So trials sit in a pending queue and update the posterior only on the
bar they resolve. At bar t the posterior contains strictly those
trials that finished at or before t. tests/unit/ pins this directly:
appending future bars must not change the posterior visible at t.
--------------------------------------------------------------------
WHY UNCERTAINTY SIZING, RATHER THAN A POINT ESTIMATE

Sizing uses a lower confidence bound on p, not the posterior mean.
That single choice does most of the safety work:

  - A cold strategy has a wide posterior, so its lower bound is near
    zero and it allocates near nothing. Warm-up needs no flag, no
    special case, and no arbitrary fallback multiplier -- it falls out
    of the arithmetic.
  - Evidence narrows the posterior, which raises the lower bound
    toward the mean. Confidence, not just optimism, is what unlocks
    size.
  - A regime that stops working widens and lowers the fast posterior,
    shrinking allocations before the mean alone would react.

scipy is deliberately NOT a dependency of this project, so the bound
is computed from the Beta's closed-form mean and variance rather than
an exact quantile function. mean - k*sd is slightly conservative
against the true Beta quantile for small alpha/beta, which is the
correct direction to be wrong in.
--------------------------------------------------------------------
WHAT THIS DOES NOT DO

It does not sell, harvest, or reason about existing lots. Sizing
governs new exposure only; src/no_loss_guard.py owns the exit
invariant and src/risk_manager.py owns portfolio exposure. A strategy
that is confident is still clamped by both.
--------------------------------------------------------------------
THE OPTIONAL RETRIGGER, AND WHY IT WAS ADDED

Like every SizingStrategy that does not override the trigger, this one
originally relied on the DEFAULT _check_grid_trigger (src/size_
calculators.py): a buy fires only when price falls `step` below
`last_buy_price`, a scalar that only moves on a real fill. Measured
directly on this repo's 10.63-year TQQQ SIP dataset: over that whole
window this strategy (like FixedPortfolioPercentage, BellCurve, and
RSI) fired exactly 54 trades, because TQQQ mostly trended up and the
stale reference was rarely revisited. That is not a sizing problem --
the posterior never got evaluated against more than 54 opportunities
to size.

lookback_days, when set, fixes this the same way
HighFrequencyLocalReferenceSizing did: _grid_trigger_level measures the
pullback from max(last_buy_price, rolling_high) instead of
last_buy_price alone, so a buy can retrigger on any local dip. It
defaults to None (off), which reproduces the exact original monotonic
behavior -- every existing config keeps its measured results unchanged
unless it opts in.

This is purely an entry-timing change. It shares no state with
record_tick's posterior machinery -- the rolling high is updated
unconditionally every bar, same as the pending-trial queue, but the
two are independent: retriggering more often changes how often
calculate_trade_value is called, never what the posteriors believe or
when a trial resolves. The lookahead trap above is untouched.

One consequence, not a defect: sizing here is still equity*max_trade_
pct*posterior_multiplier, not HighFrequencyLocalReferenceSizing's fixed
dollar-per-lot. Frequent retriggering can exhaust cash after a handful
of buys during one decline, same as it would for any equity-fraction
strategy -- max_trade_pct will typically need to be swept smaller
alongside enabling lookback_days.
--------------------------------------------------------------------
THE OPTIONAL VOL SCALE

Every HF sweep to date picked a negative vol_scale_exponent (size DOWN
into realized volatility) as its single most consistent finding --
this strategy had no way to do that at all: reference_probability
governs how confident the posterior must be, not how large a position
is once confident. This adds the same ratio-of-rolling-windows scaler
HighFrequencyLocalReferenceSizing uses, as an independent multiplier on
top of the posterior, so the two ideas compose rather than compete: the
posterior decides WHETHER to size up, this decides how much smaller a
position should be given current turbulence, regardless of how
confident the posterior is.

Deliberately NOT shared code with HighFrequencyLocalReferenceSizing's
_vol_scale -- that method is exercised directly by the currently-
running live deployment, and refactoring it to share an implementation
with a change landing here would risk the live strategy over a
convenience save. The formula is copied, not imported: same ratio,
same clamp, same warm-up-returns-1.0 behavior, same synthetic-bar
guard (see record_tick) -- verified equal in
tests/unit/test_bayesian_sizing_calculators.py.

Defaults: vol_scale_exponent=0.0, an exact no-op -- existing configs
and search_bayesian_deep.yaml's already-recorded results are unaffected.
--------------------------------------------------------------------
THE OPTIONAL TRAILING TARGET

This strategy had NO exit management at all until now: it "does not
sell, harvest, or reason about existing lots" (see above) -- true of
its SIZING, but it means every lot it opens sits at a single fixed
target forever, exactly the failure mode
HighFrequencyLocalReferenceSizing's own trailing target
(src/trailing_target.py) was built to fix there. It applies with equal
force here, arguably more: this strategy's whole model is "estimate
P(reach target within horizon)" -- when the posterior is honestly
uncertain about a wide target, it still opens a (smaller) position, and
if the estimate does not pan out that lot then has no reachable exit
at all.

trail_pct=None (the default) reproduces the exact original fixed-
target behavior. Set it to compose src.trailing_target.TrailingTargetPolicy
the same way HighFrequencyLocalReferenceSizing does -- see that
strategy's adjust_profit_target for the identical pattern. Deliberately
independent of target_return: target_return still governs what the
POSTERIOR is estimating (unaffected by trailing), while trail_pct
governs what a lot's real exit price can fall to once it has shown a
genuine gain. See src/trailing_target.py's own docstring for why
trailing only engages once there is a real gain to trail (a fix
already required once, this session, before it could be trusted here).
--------------------------------------------------------------------
THE TARGET_RETURN / PROFIT_TARGET CROSS-CHECK

target_return (below) was, until now, purely on the honor system: the
posterior estimates P(reach target_return within horizon), but the
sweep's real exit price is grid.profit_targets/live.profit_target --
a SEPARATE value this class never sees. Nothing anywhere checked they
agreed. A sweep varying profit_targets with target_return left fixed
in strategy_params would silently run every combination but one with a
posterior confidently answering a different question than the one
being traded, and every resulting metric would look completely
ordinary -- exactly the "silent modelling error" this class's own
target_return docstring already named without anything enforcing it.

optimization_controller._run_one_combination and the live construction
path now read this instance's target_return via getattr immediately
after construction and raise ConfigurationError on a mismatch, before
any simulation work runs. allow_target_return_mismatch=True is the
escape hatch for a genuinely deliberate divergence -- the docstring
below still calls that legitimate; it just no longer looks identical
to the accident this exists to catch.
--------------------------------------------------------------------
THE COST BUFFER, AND WHY THE POSTERIOR WAS OPTIMISTIC WITHOUT IT

record_tick's success test was a RAW PRICE TOUCH: did the window's high
ever reach entry_price * (1 + target_return). But a real exit goes
through src/no_loss_guard.py, which can reject a sell outright (net
proceeds must clear cost basis after slippage/commission), and even
when it does not reject, the net realized return is always somewhat
below the raw touch price. So the posterior was being fit to an EASIER
question than the one that matters -- "did price touch X" instead of
"could this lot actually have been sold for a profit" -- which means
_conservative_probability() systematically OVERESTIMATED the true,
cost-adjusted success rate. The gap is worst for tight targets, where
slippage is a larger fraction of the move, and this project already
measured a version of that exact interaction: src/no_loss_guard.py's
own docstring notes thin profit targets can stop clearing the guard at
all once realistic costs are modeled.

cost_buffer_pct closes this: the success test becomes window_max >=
entry_price * (1 + target_return + cost_buffer_pct), so a trial only
counts as a win if it cleared the target WITH ROOM for costs, not
merely touched it. Defaults to 0.0 -- an exact no-op, reproducing the
original (optimistic) behavior -- because this project's strategies
are deliberately cost-agnostic (this class "does not sell, harvest, or
reason about existing lots"; costs are owned entirely by
src/cost_models.py and src/no_loss_guard.py). This is therefore a
BUFFER the operator calibrates from the same cost model config they are
already running (e.g. roughly 2x a dynamic-slippage model's base_bps
for a round trip), not a live query into the actual TransactionCostModel
object -- wiring that object into a sizing strategy would be a larger
change, coupling a class that currently knows nothing about costs to
one that owns them, for a benefit a simple buffer already captures.
"""

from __future__ import annotations

import math
from collections import deque

from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.size_calculators import SizingStrategy
from src.sizing_indicators import RollingMax, RollingMean, RollingStdev, bars_from_days, clamp
from src.synthetic_bars import is_synthetic_bar
from src.trailing_target import TrailingTargetPolicy


class DecayedBetaPosterior:
    """A Beta posterior that forgets old evidence exponentially.

    On each observation the accumulated evidence decays toward the
    prior before the new trial is added:

        alpha <- alpha0 + d*(alpha - alpha0) + x
        beta  <- beta0  + d*(beta  - beta0)  + (1 - x)

    with d = 0.5 ** (1 / half_life_trials). This is standard
    discounted conjugate updating. Two consequences worth naming:

    - Effective sample size saturates near 1/(1-d) instead of growing
      without bound, so the posterior stays responsive forever rather
      than freezing once it has seen enough.
    - With d = 1 (infinite half-life) it reduces exactly to ordinary
      Bayesian updating, which is what the slow scale approximates.
    """

    def __init__(self, alpha0: float = 1.0, beta0: float = 1.0, half_life_trials: float = 100.0):
        if alpha0 <= 0 or beta0 <= 0:
            raise ConfigurationError(
                f"Beta prior parameters must be positive, got alpha0={alpha0}, beta0={beta0}"
            )
        if half_life_trials <= 0:
            raise ConfigurationError(f"half_life_trials must be positive, got {half_life_trials}")
        self.alpha0 = alpha0
        self.beta0 = beta0
        self.half_life_trials = half_life_trials
        self._decay = 0.5 ** (1.0 / half_life_trials)
        self.alpha = alpha0
        self.beta = beta0

    def update(self, success: bool) -> None:
        """Fold in one resolved Bernoulli trial."""
        d = self._decay
        self.alpha = self.alpha0 + d * (self.alpha - self.alpha0) + (1.0 if success else 0.0)
        self.beta = self.beta0 + d * (self.beta - self.beta0) + (0.0 if success else 1.0)

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        n = self.alpha + self.beta
        return (self.alpha * self.beta) / (n * n * (n + 1.0))

    @property
    def effective_sample_size(self) -> float:
        """Evidence accumulated beyond the prior. Saturates near
        1/(1-decay); useful for diagnosing whether the strategy is
        sizing off real data or still mostly off its prior."""
        return (self.alpha + self.beta) - (self.alpha0 + self.beta0)

    def lower_bound(self, k: float) -> float:
        """Conservative estimate of p: mean - k standard deviations.

        Clamped to [0, 1] because the normal-style bound can fall
        outside the Beta's support when the posterior is very wide --
        which is precisely the cold-start case, where the honest answer
        is "zero confidence, allocate nothing".
        """
        return clamp(self.mean - k * math.sqrt(self.variance), 0.0, 1.0)


class BayesianDualScaleSizing(SizingStrategy):
    """Sizes by a conservative posterior probability of hitting target.

    Two posteriors track the same latent success probability at
    different memory lengths -- a fast one for the current regime and a
    slow one for the long-run base rate. Allocation uses the MINIMUM of
    their lower bounds, so both timescales must agree before the
    strategy sizes up. That mirrors the multiplicative safety property
    of the other strategies: each scale can only reduce exposure, and
    neither can override the other's caution.
    """

    def __init__(
        self,
        max_trade_pct: float,
        target_return: float,
        horizon_days: float,
        bars_per_day: int,
        fast_half_life_days: float = 5.0,
        slow_half_life_days: float = 120.0,
        confidence_k: float = 2.0,
        reference_probability: float = 0.5,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        lookback_days: float | None = None,
        vol_scale_exponent: float = 0.0,
        vol_fast_days: float = 0.5,
        vol_slow_days: float = 20.0,
        vol_scale_min: float = 0.5,
        vol_scale_max: float = 2.0,
        vol_measure: str = "stdev",
        trail_pct: float | None = None,
        trail_min_profit_target: float = 0.001,
        allow_target_return_mismatch: bool = False,
        cost_buffer_pct: float = 0.0,
    ) -> None:
        """Configure the model.

        target_return is a constructor parameter because the sizing
        contract never sees the sweep's profit_target -- record_tick
        and calculate_trade_value receive only a MarketContext. It
        should normally MIRROR grid.profit_targets: the posterior is
        estimating "will a lot bought now reach ITS target", so a
        mismatch means the strategy is confident about a different
        question than the one being traded. A deliberate mismatch is
        legitimate; an accidental one is a silent modelling error.

        lookback_days is None by default -- see the module docstring's
        "THE OPTIONAL RETRIGGER" section. Set it to enable the same
        local-pullback retrigger HighFrequencyLocalReferenceSizing uses.
        """
        if not 0.0 < max_trade_pct <= 1.0:
            raise ConfigurationError(f"max_trade_pct must be in (0, 1], got {max_trade_pct}")
        if target_return <= 0:
            raise ConfigurationError(f"target_return must be positive, got {target_return}")
        if confidence_k < 0:
            raise ConfigurationError(f"confidence_k must be >= 0, got {confidence_k}")
        if not 0.0 < reference_probability <= 1.0:
            raise ConfigurationError(
                f"reference_probability must be in (0, 1], got {reference_probability}"
            )
        if lookback_days is not None and lookback_days <= 0:
            raise ConfigurationError(f"lookback_days must be positive, got {lookback_days}")
        if vol_scale_min <= 0.0 or vol_scale_max < vol_scale_min:
            raise ConfigurationError(
                f"need 0 < vol_scale_min <= vol_scale_max, got {vol_scale_min} and {vol_scale_max}"
            )
        if vol_measure not in ("stdev", "range"):
            raise ConfigurationError(f"vol_measure must be 'stdev' or 'range', got {vol_measure!r}")
        if cost_buffer_pct < 0.0:
            raise ConfigurationError(f"cost_buffer_pct must be >= 0, got {cost_buffer_pct}")
        # trail_pct/trail_min_profit_target are validated by
        # TrailingTargetPolicy itself at construction, below -- not
        # duplicated here, so there is exactly one place those rules
        # live.

        self.max_trade_pct = max_trade_pct
        self.target_return = target_return
        self.horizon_days = horizon_days
        self.bars_per_day = bars_per_day
        self.fast_half_life_days = fast_half_life_days
        self.slow_half_life_days = slow_half_life_days
        self.confidence_k = confidence_k
        self.reference_probability = reference_probability
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.lookback_days = lookback_days
        self.vol_scale_exponent = vol_scale_exponent
        self.vol_fast_days = vol_fast_days
        self.vol_slow_days = vol_slow_days
        self.vol_scale_min = vol_scale_min
        self.vol_scale_max = vol_scale_max
        self.vol_measure = vol_measure
        self.trail_pct = trail_pct
        self.trail_min_profit_target = trail_min_profit_target
        # Read by optimization_controller._run_one_combination and
        # live_trading_loop's construction path, via getattr rather than
        # an isinstance check -- see "THE TARGET_RETURN / PROFIT_TARGET
        # CROSS-CHECK" module docstring section. False by default:
        # accidental drift, not deliberate divergence, is the default
        # assumption for a value with no enforcement until now.
        self.allow_target_return_mismatch = allow_target_return_mismatch
        self.cost_buffer_pct = cost_buffer_pct
        self._trailing = (
            TrailingTargetPolicy(trail_pct, min_profit_target=trail_min_profit_target)
            if trail_pct is not None
            else None
        )

        self._horizon_bars = bars_from_days(horizon_days, bars_per_day)
        # Half-lives are configured in DAYS but consumed in TRIALS, and
        # one trial resolves per bar, so the conversion is the same
        # days->bars mapping. Expressing them in days keeps them
        # meaningful across bar frequencies -- a "5" that means five
        # days on daily data and five minutes on minute data is the
        # exact failure this repo already hit with a 252-bar lookback.
        self._fast = DecayedBetaPosterior(
            prior_alpha, prior_beta, bars_from_days(fast_half_life_days, bars_per_day)
        )
        self._slow = DecayedBetaPosterior(
            prior_alpha, prior_beta, bars_from_days(slow_half_life_days, bars_per_day)
        )
        # Bounded by construction: at most horizon_bars entry prices.
        # Nothing here grows with the length of the backtest.
        self._pending: deque[float] = deque()
        # A trial opened at bar t is scored on max(price) over bars
        # t+1..t+H. At bar t+H that window is exactly "the last H
        # bars", so ONE sliding-window maximum resolves every trial --
        # no need to carry a running max per pending entry. That turns
        # record_tick from O(horizon) into amortized O(1), which is not
        # a micro-optimization: at horizon=652 bars over 408k bars of
        # minute data the per-entry version did ~266M comparisons and
        # took minutes per sweep combination.
        self._window_max = RollingMax(self._horizon_bars)
        self._bars_seen = 0
        # Independent of the horizon-scoring window above: this one
        # feeds only _grid_trigger_level's entry timing, never the
        # posteriors. None (the default) means the retrigger is off --
        # see the module docstring's "THE OPTIONAL RETRIGGER" section.
        self._rolling_high = (
            RollingMax(bars_from_days(lookback_days, bars_per_day))
            if lookback_days is not None
            else None
        )
        # Built only when enabled, matching HighFrequencyLocalReferenceSizing's
        # own reasoning: at exponent 0.0 this is an exact no-op, so
        # constructing the windows would add a per-bar update, for every
        # combination in a sweep, to compute a number raised to the
        # power zero.
        self._vol_enabled = vol_scale_exponent != 0.0
        self._prev_price: float | None = None
        if self._vol_enabled:
            fast_bars = max(2, bars_from_days(vol_fast_days, bars_per_day))
            slow_bars = max(2, bars_from_days(vol_slow_days, bars_per_day))
            make = RollingStdev if vol_measure == "stdev" else RollingMean
            self._fast_vol = make(fast_bars)
            self._slow_vol = make(slow_bars)

    def record_tick(self, context: MarketContext) -> None:
        """Open a trial for this bar and resolve any that have matured.

        Called on EVERY bar, not only triggered ones. The posterior is
        estimating a property of the market, so sampling it only on
        bars where the grid happened to fire would make the estimate a
        function of the grid step.
        """
        price = context.price
        if price <= 0 or not math.isfinite(price):
            return
        self._bars_seen += 1
        if self._rolling_high is not None:
            self._rolling_high.update(price)

        if self._vol_enabled:
            # Same structural synthetic-bar guard
            # HighFrequencyLocalReferenceSizing.record_tick uses, copied
            # rather than shared -- see that method's comment for the
            # exact reasoning and the measured false-positive rate. A
            # fabricated bar from resample_to_uniform_minutes is flat
            # (high==low==price) AND unchanged from the previous real
            # print; skip it so realized vol does not read low through
            # synthetic filler.
            synthetic = is_synthetic_bar(context.high, context.low, price, self._prev_price)
            if not synthetic:
                if self.vol_measure == "range":
                    self._fast_vol.update((context.high - context.low) / price)
                    self._slow_vol.update((context.high - context.low) / price)
                elif self._prev_price is not None and self._prev_price > 0:
                    log_return = math.log(price / self._prev_price)
                    self._fast_vol.update(log_return)
                    self._slow_vol.update(log_return)
            self._prev_price = price

        # After this call the window covers bars [i-H+1 .. i], which is
        # precisely the scoring window of the trial opened at bar i-H.
        window_max = self._window_max.update(price)
        self._pending.append(price)

        # A trial started H bars ago is now fully observed. Only now --
        # never earlier -- may it touch the posteriors.
        if len(self._pending) > self._horizon_bars:
            entry_price = self._pending.popleft()
            # + cost_buffer_pct (default 0.0, an exact no-op) -- see
            # module docstring's "THE COST BUFFER" section. A trial
            # only counts as a win if the touch cleared the target with
            # room for costs, not merely reached it, so the posterior
            # is not fit to an easier question than what a real exit
            # (gated by src/no_loss_guard.py) can actually collect.
            success = window_max >= entry_price * (1.0 + self.target_return + self.cost_buffer_pct)
            self._fast.update(success)
            self._slow.update(success)

    def wants_lot_retargeting(self) -> bool:
        """False when trailing is off, so decision_cycle can skip walking
        every open lot on every bar.

        Not a micro-optimisation: that walk profiled at 63% of total
        runtime, doing nothing, whenever trail_pct is unset -- which is
        the default and the champion configuration. See
        decision_cycle.adjust_open_lot_targets.

        Answering False promises that adjust_profit_target AND
        retain_lots are both inert, which is exactly what
        `self._trailing is None` means here.
        """
        return self._trailing is not None

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        """Trail this lot's exit target, when trail_pct is configured.

        Returns None (leave the target alone) when trailing is off,
        which is the default -- see the module docstring's "THE
        OPTIONAL TRAILING TARGET" section. Identical pattern to
        HighFrequencyLocalReferenceSizing.adjust_profit_target."""
        if self._trailing is None:
            return None
        return self._trailing.propose(lot, context.price)

    def retain_lots(self, open_order_ids) -> None:
        """Release peak state for lots that have closed. See
        decision_cycle.adjust_open_lot_targets."""
        if self._trailing is not None:
            self._trailing.retain_lots(open_order_ids)

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """last_buy_price OR the local rolling high, whichever is
        higher, is the reference a pullback is measured from -- only
        when lookback_days is set. See the module docstring's "THE
        OPTIONAL RETRIGGER" section, and
        HighFrequencyLocalReferenceSizing._grid_trigger_level, which
        this mirrors exactly."""
        if self._rolling_high is None:
            return super()._grid_trigger_level(context, last_buy_price, step)
        rolling_high = self._rolling_high.value
        reference = last_buy_price if rolling_high is None else max(last_buy_price, rolling_high)
        return reference * (1.0 - step)

    _VOL_EPSILON = 1e-9

    def _vol_scale(self) -> float:
        """Size multiplier from short-horizon realized vol relative to
        its own longer-horizon baseline -- see the module docstring's
        "THE OPTIONAL VOL SCALE" section for why this exists and why it
        is a copy of HighFrequencyLocalReferenceSizing's formula rather
        than a shared one.

        Returns 1.0 until both windows have enough observations and
        whenever disabled, so the unscaled strategy's behavior is
        reproduced exactly in both cases.
        """
        if not self._vol_enabled:
            return 1.0
        fast = self._fast_vol.value
        slow = self._slow_vol.value
        if fast is None or slow is None or slow <= self._VOL_EPSILON:
            return 1.0
        ratio = fast / slow
        return clamp(ratio**self.vol_scale_exponent, self.vol_scale_min, self.vol_scale_max)

    def _conservative_probability(self) -> float:
        """Lower bound on p that BOTH timescales support."""
        return min(
            self._fast.lower_bound(self.confidence_k),
            self._slow.lower_bound(self.confidence_k),
        )

    def calculate_trade_value(self, context: MarketContext) -> float:
        """Allocate in proportion to the conservative posterior.

        reference_probability is the success rate at which the strategy
        commits its full ceiling; below that it scales down linearly.
        It is NOT a threshold -- there is no cliff, so a posterior
        drifting across it changes size smoothly rather than switching
        the strategy on and off.

        IT MUST BE CALIBRATED TO THE TARGET AND HORIZON, and getting
        this wrong is the quiet failure mode of the whole strategy. If
        the achievable success rate sits well above the reference, the
        ratio pins at 1.0 forever and this degenerates into
        FixedPortfolioPercentage wearing a posterior -- it will look
        like it is working, and every Bayesian parameter will stop
        affecting results.

        Measured on this repo's 5-year TQQQ minute data, a 0.5% target
        over a half-day horizon succeeds about 82% of the time, so the
        default of 0.5 saturated 99.7% of bars. Calibrate by running
        diagnostics() over representative data and reading
        slow_mean -- the reference belongs near or above it, not below.
        """
        if context.equity <= 0 or context.price <= 0:
            return 0.0
        ceiling = context.equity * self.max_trade_pct
        multiplier = clamp(self._conservative_probability() / self.reference_probability, 0.0, 1.0)
        if not math.isfinite(multiplier):
            return 0.0
        # vol_scale multiplies ON TOP of the posterior-derived value,
        # rather than being folded into ceiling -- see module docstring:
        # the posterior decides whether to size up, this decides how
        # much smaller given current turbulence, independently. No
        # further clamp needed: _vol_scale() is already bounded to
        # [vol_scale_min, vol_scale_max] and the base value to
        # [0, ceiling], matching HighFrequencyLocalReferenceSizing's own
        # calculate_trade_value, which does not reclamp after its
        # multiplier chain either.
        return clamp(ceiling * multiplier, 0.0, ceiling) * self._vol_scale()

    def diagnostics(self, context: MarketContext | None = None) -> dict:
        """Why the strategy sized the way it did.

        Deliberately not part of the SizingStrategy contract -- nothing
        in the decision cycle calls it, and it must never be treated as
        authoritative state. It exists so that a live trade can be
        traced to the posterior that produced it, which is otherwise
        impossible to reconstruct after the fact.
        """
        return {
            "bars_seen": self._bars_seen,
            "pending_trials": len(self._pending),
            "horizon_bars": self._horizon_bars,
            "fast_mean": self._fast.mean,
            "fast_lower_bound": self._fast.lower_bound(self.confidence_k),
            "fast_effective_n": self._fast.effective_sample_size,
            "slow_mean": self._slow.mean,
            "slow_lower_bound": self._slow.lower_bound(self.confidence_k),
            "slow_effective_n": self._slow.effective_sample_size,
            "conservative_probability": self._conservative_probability(),
            # The calibration check. True means the posterior is pinned
            # at the ceiling, so the Bayesian machinery is not currently
            # influencing size at all -- see reference_probability in
            # __init__ for why that is the strategy's quiet failure
            # mode rather than a success.
            "saturated": self._conservative_probability() >= self.reference_probability,
            "proposed_trade_value": (
                self.calculate_trade_value(context) if context is not None else None
            ),
        }
