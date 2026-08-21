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
"""

from __future__ import annotations

import math
from collections import deque

from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.size_calculators import SizingStrategy
from src.sizing_indicators import RollingMax, bars_from_days, clamp


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

        # After this call the window covers bars [i-H+1 .. i], which is
        # precisely the scoring window of the trial opened at bar i-H.
        window_max = self._window_max.update(price)
        self._pending.append(price)

        # A trial started H bars ago is now fully observed. Only now --
        # never earlier -- may it touch the posteriors.
        if len(self._pending) > self._horizon_bars:
            entry_price = self._pending.popleft()
            success = window_max >= entry_price * (1.0 + self.target_return)
            self._fast.update(success)
            self._slow.update(success)

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
        return clamp(ceiling * multiplier, 0.0, ceiling)

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
