"""
Sizing strategies for the grid-harvesting strategy.

SizingStrategy now implements the *target* form of the shared contract
from architecture_overview.md Section 5.2, as of Task 4.1:

    record_tick(context: MarketContext) -> None
    calculate_trade_value(context: MarketContext) -> float

Migrated from the interim (loose-parameter) form Phases 0-3 used --
see git history for that version. optimization_controller.py's
_simulate_single (Task 4.1) constructs one MarketContext per bar and
passes it to record_tick, _check_grid_trigger, and
calculate_trade_value uniformly.

FixedPortfolioPercentage, BellCurveProbabilitySizing and
RsiMomentumSizing live here (architecture_overview.md Section 6's
module layout). BayesianDualScaleSizing is in its own file,
src/bayesian_sizing_calculators.py, as that layout specifies.

The latter three had no documented sizing formula anywhere in the
original specification -- only names. The bell-curve and RSI formulas
implemented here come from a technical design document supplied
later; they are that document's mathematics, not a recovered original
spec, and should be read as one reasoned interpretation rather than a
canonical definition.

--------------------------------------------------------------------
WINDOW LENGTHS ARE IN TRADING DAYS, NOT BARS.

Both new strategies take lookback_days plus an explicit bars_per_day
rather than a raw bar count. A "252-bar" lookback is one trading year
on daily bars and roughly forty minutes on 1-minute bars; measured
against this repo's own 5-year TQQQ minute data, a 252-BAR "52-week
high" collapsed the Gaussian into a near-constant ~0.18 multiplier for
62% of bars. See src/sizing_indicators.py for the measurement and the
conversion helper.
--------------------------------------------------------------------
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.sizing_indicators import RollingMax, WilderRSI, bars_from_days, clamp


class SizingStrategy(ABC):
    """Target-form sizing-strategy contract (architecture_overview.md
    Section 5.2), as of Task 4.1."""

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """The price AT OR BELOW WHICH a buy triggers.

        Split out from _check_grid_trigger so the level is a value the
        caller can inspect, not just a boolean it can evaluate. The
        intrabar fill model needs exactly that: it compares the level
        against the bar's LOW (did a resting limit order get touched?)
        and fills AT the level, which is impossible to do from a
        boolean alone.

        Before this existed, src/intraday_validation.py recomputed
        `last_buy_price * (1 - grid_step)` inline -- which silently
        hardcoded the DEFAULT formula and would have been wrong for any
        strategy overriding the trigger (HighFrequencyLocalReferenceSizing
        measures its pullback from max(last_buy_price, rolling_high),
        not from last_buy_price). Overriding THIS method, rather than
        _check_grid_trigger, is what keeps the close-only and intrabar
        paths agreeing on one definition per strategy.
        """
        return last_buy_price * (1.0 - step)

    def _check_grid_trigger(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> bool:
        """Default: identical to the pre-Task-4.1 inline check
        (current_price <= last_buy_price * (1 - step)), now expressed
        against context.price and routed through _grid_trigger_level so
        there is one definition of the level per strategy.
        last_buy_price/step aren't part of MarketContext (they're
        grid/backtest state, not market state), so they stay as explicit
        parameters. Overridable per-strategy, though overriding
        _grid_trigger_level is usually the better seam -- see there."""
        return context.price <= self._grid_trigger_level(context, last_buy_price, step)

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        """The profit_target `lot` should now carry, or None to leave it.

        Default: None for every lot, so a strategy that does not
        override this keeps the original fixed-at-entry behavior
        exactly -- no existing strategy, config, or recorded sweep
        result changes because this hook exists.

        Called once per open lot per bar, BEFORE that bar's marketable
        check, by decision_cycle.adjust_open_lot_targets -- which is
        what keeps backtest and live applying it at the same point in
        the sequence rather than in two places that could drift.

        Overriding this cannot make a losing sell possible.
        src/no_loss_guard.py evaluates against buy_price and rejects
        independently of any target; see src/ledger.Lot.retarget.
        Compose src/trailing_target.TrailingTargetPolicy here rather
        than writing peak-tracking by hand.
        """
        return None

    @abstractmethod
    def record_tick(self, context: MarketContext) -> None:
        """Called once per bar in the target execution sequence
        (implementation_task_specs.md "Canonical execution sequence")."""
        ...

    @abstractmethod
    def calculate_trade_value(self, context: MarketContext) -> float:
        """Dollar value to buy at a confirmed grid trigger."""
        ...


class FixedPortfolioPercentage(SizingStrategy):
    """Allocates a fixed percentage of total equity to each triggered buy.

    Stateless: ignores ticks and drawdown entirely. This matches Task
    1.6's acceptance criteria for this specific strategy ("doesn't use
    drawdown or ticks in its sizing").

    Canonical constructor keyword is `allocation_pct`, per
    implementation_task_specs.md Task 1.1's own proposed reading of
    Run_Instructions' (buggy) `allocations` example parameter --
    everything in this codebase built against that name. `percentage`
    is also accepted (also keyword-only) since src/live_execution.py,
    pushed directly to main mid-session, calls this constructor with
    that name instead -- see the chat this was produced in. Passing
    both is only allowed if they agree; the stored attribute is always
    `self.allocation_pct` either way, so every existing reader of that
    attribute (Task 4.6's params capture, this class's own
    calculate_trade_value) is unaffected by which name a caller used.
    """

    def __init__(self, allocation_pct: float | None = None, percentage: float | None = None):
        """Configure the fixed allocation fraction.

        allocation_pct and percentage are two accepted names for the
        same value (see the class docstring); exactly one is required,
        and supplying both is allowed only if they agree. Must be in
        (0, 1].
        """
        if allocation_pct is None and percentage is None:
            raise ConfigurationError(
                "FixedPortfolioPercentage requires allocation_pct (or percentage)"
            )
        if allocation_pct is not None and percentage is not None and allocation_pct != percentage:
            raise ConfigurationError(
                f"allocation_pct ({allocation_pct!r}) and percentage ({percentage!r}) were both "
                "given and disagree -- pass only one"
            )
        value = allocation_pct if allocation_pct is not None else percentage
        if not 0.0 < value <= 1.0:
            raise ConfigurationError(f"allocation_pct must be in (0, 1], got {value}")
        self.allocation_pct = value

    def record_tick(self, context: MarketContext) -> None:
        """No-op: this strategy holds no rolling state, so a tick
        carries no information it needs to retain."""
        pass

    def calculate_trade_value(self, context: MarketContext) -> float:
        """A fixed fraction of current equity.

        Sizing off equity rather than initial capital means position
        size compounds with gains and shrinks after losses, without any
        explicit rebalancing step.
        """
        return context.equity * self.allocation_pct


class _BaselineScaledStrategy(SizingStrategy):
    """Shared machinery for the two model-driven strategies.

    Both apply the same two-stage shape: a hard ceiling of
    equity * max_trade_pct, then an exponential reduction as price
    falls below a fixed baseline, then the strategy's own model
    multiplier. Only the model differs, so the ceiling, the baseline
    handling and the numerical guards live here once.

    ON THE BASELINE (the design document's Section 9): it is the first
    price the strategy observes, captured on the first record_tick and
    then IMMUTABLE. Re-baselining on each grid purchase would let the
    reference drift down with the market, which is exactly when the
    protection is supposed to bite -- the multiplier would return to
    1.0 partway through a sustained decline. An explicit
    baseline_price overrides capture, which is what makes a backtest
    reproducible across differently-sliced data (a walk-forward fold
    otherwise captures a different baseline per fold).
    """

    def __init__(
        self,
        max_trade_pct: float,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        if not 0.0 < max_trade_pct <= 1.0:
            raise ConfigurationError(f"max_trade_pct must be in (0, 1], got {max_trade_pct}")
        if inverse_scale_kappa < 0.0:
            raise ConfigurationError(f"inverse_scale_kappa must be >= 0, got {inverse_scale_kappa}")
        if baseline_price is not None and baseline_price <= 0:
            raise ConfigurationError(f"baseline_price must be positive, got {baseline_price}")
        self.max_trade_pct = max_trade_pct
        self.baseline_price = baseline_price
        self.inverse_scale_kappa = inverse_scale_kappa
        self._baseline: float | None = baseline_price

    def _capture_baseline(self, price: float) -> None:
        """First observed price becomes the baseline, once and never again."""
        if self._baseline is None and price > 0:
            self._baseline = price

    def _inverse_multiplier(self, price: float) -> float:
        """exp(-kappa * drawdown-below-baseline), capped at 1.0.

        The max(0, ...) on the drawdown is deliberate and asymmetric:
        this is protection against sustained declines, so a price ABOVE
        the baseline must not push the multiplier above 1.0 and inflate
        the position beyond the hard ceiling.
        """
        if self.inverse_scale_kappa == 0.0 or self._baseline is None or self._baseline <= 0:
            return 1.0
        drawdown = max(0.0, (self._baseline - price) / self._baseline)
        return math.exp(-self.inverse_scale_kappa * drawdown)

    def _model_multiplier(self, context: MarketContext) -> float:
        """The subclass's own [0, 1] multiplier."""
        raise NotImplementedError

    def calculate_trade_value(self, context: MarketContext) -> float:
        """Ceiling, then every multiplier, then clamp back to the ceiling.

        Multiplicative composition has the property that matters here:
        each independent factor can only REDUCE exposure, so no model
        can compensate for another's caution. The final clamp is belt
        and braces -- with both multipliers in [0, 1] it cannot bind,
        but it means a future model returning something out of range
        degrades to the ceiling rather than to an unbounded order.
        """
        if context.equity <= 0 or context.price <= 0:
            return 0.0
        ceiling = context.equity * self.max_trade_pct
        multiplier = self._inverse_multiplier(context.price) * self._model_multiplier(context)
        if not math.isfinite(multiplier):
            return 0.0
        return clamp(ceiling * multiplier, 0.0, ceiling)


class BellCurveProbabilitySizing(_BaselineScaledStrategy):
    """Sizes by how far price has fallen from its rolling high, through
    a Gaussian centred on a target drawdown.

    The model is NOT "deeper drawdown means bigger position". It peaks
    at mu and falls away on BOTH sides, which encodes three regimes:
    an ordinary shallow pullback is not yet interesting, a drawdown
    near mu is historically characteristic and gets full size, and a
    drawdown far beyond mu is outside historical experience and gets
    scaled back rather than doubled down on. That third case is the
    capital-preservation half of the model and the reason a plain
    monotonic function would not do.
    """

    def __init__(
        self,
        max_trade_pct: float,
        lookback_days: float,
        bars_per_day: int,
        mu: float = 0.20,
        sigma: float = 0.10,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        super().__init__(max_trade_pct, baseline_price, inverse_scale_kappa)
        if sigma <= 0:
            raise ConfigurationError(f"sigma must be positive, got {sigma}")
        if not 0.0 <= mu <= 1.0:
            raise ConfigurationError(f"mu must be in [0, 1], got {mu}")
        self.lookback_days = lookback_days
        self.bars_per_day = bars_per_day
        self.mu = mu
        self.sigma = sigma
        self._rolling_high = RollingMax(bars_from_days(lookback_days, bars_per_day))

    def record_tick(self, context: MarketContext) -> None:
        """Advance the rolling high on EVERY bar.

        Not only on triggered bars: the rolling high is a property of
        the market, not of this strategy's trading, and updating it
        only when a grid purchase happened would make the window depend
        on the grid step.
        """
        self._capture_baseline(context.price)
        if context.price > 0:
            self._rolling_high.update(context.price)

    def _drawdown_from_high(self, price: float) -> float:
        high = self._rolling_high.value
        if high is None or high <= 0:
            return 0.0
        return clamp((high - price) / high, 0.0, 1.0)

    def _model_multiplier(self, context: MarketContext) -> float:
        d = self._drawdown_from_high(context.price)
        return clamp(math.exp(-((d - self.mu) ** 2) / (2.0 * self.sigma**2)), 0.0, 1.0)


class RsiMomentumSizing(_BaselineScaledStrategy):
    """Sizes up as RSI falls into oversold territory.

    Above the threshold the strategy still participates, at
    baseline_multiplier, rather than standing aside entirely -- the
    grid trigger has already decided that a purchase is warranted, and
    this model only modulates how much.

    While RSI is unseeded (fewer than `period` changes observed) the
    baseline multiplier is used. That is the conservative direction: it
    sizes as though the market were NOT oversold, so an unwarmed
    strategy under-allocates rather than betting on an indicator it
    cannot yet compute.
    """

    def __init__(
        self,
        max_trade_pct: float,
        period: int = 14,
        oversold_threshold: float = 30.0,
        baseline_multiplier: float = 0.10,
        aggression_factor: float = 0.90,
        exponent: float = 1.0,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        super().__init__(max_trade_pct, baseline_price, inverse_scale_kappa)
        if not 0.0 < oversold_threshold < 100.0:
            raise ConfigurationError(
                f"oversold_threshold must be in (0, 100), got {oversold_threshold}"
            )
        if not 0.0 <= baseline_multiplier <= 1.0:
            raise ConfigurationError(
                f"baseline_multiplier must be in [0, 1], got {baseline_multiplier}"
            )
        if not 0.0 <= aggression_factor <= 1.0:
            raise ConfigurationError(
                f"aggression_factor must be in [0, 1], got {aggression_factor}"
            )
        if exponent <= 0:
            raise ConfigurationError(f"exponent must be positive, got {exponent}")
        self.period = period
        self.oversold_threshold = oversold_threshold
        self.baseline_multiplier = baseline_multiplier
        self.aggression_factor = aggression_factor
        self.exponent = exponent
        self._rsi = WilderRSI(period)

    def record_tick(self, context: MarketContext) -> None:
        """Feed every bar's close to RSI.

        RSI is path-dependent, so skipping untriggered bars would make
        the indicator depend on the grid step -- two sweep combinations
        would then compute different RSI values from identical data.
        """
        self._capture_baseline(context.price)
        if context.price > 0:
            self._rsi.update(context.price)

    def _model_multiplier(self, context: MarketContext) -> float:
        rsi = self._rsi.value
        if rsi is None or rsi > self.oversold_threshold:
            return clamp(self.baseline_multiplier, 0.0, 1.0)
        # How far into oversold territory, as a fraction of the way
        # from the threshold to zero.
        fraction = (self.oversold_threshold - rsi) / self.oversold_threshold
        scaled = fraction**self.exponent
        return clamp(self.baseline_multiplier + scaled * self.aggression_factor, 0.0, 1.0)
