"""
Backtest/live configuration containers. Task 6.1 (A4 follow-through,
documentation completeness).

Originally built narrower, to unblock src/live_execution.py pushed
directly to main mid-session; extended here to the canonical schema
architecture_overview.md / implementation_task_specs.md Task 6.1
requires (strategy, backtest, grid, costs, risk, search, execution,
output, live). Every field maps to a real, already-implemented
capability in this codebase -- none were added just because the
schema names a category; where no backing implementation exists
(e.g. a drawdown-based risk limit -- RiskManager, Task 3.1, has none),
no field was added for it, per this task's own "do not document
parameters that haven't been implemented yet."

BacktestConfig.validate() delegates to src/validation.py's helpers
(Task 4.9) rather than re-implementing range/cross-field checks.

from_yaml() deserializes through from_dict() -- the same path
programmatic construction uses -- rather than a second, parallel
YAML-only schema, per this task's explicit instruction.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from src.cost_models import (
    DynamicSlippageModel,
    SlippageCommissionModel,
    TransactionCostModel,
    ZeroCostModel,
)
from src.exceptions import ConfigurationError
from src.risk_manager import RiskManager
from src.validation import (
    validate_grid_steps,
    validate_non_negative,
    validate_one_of,
    validate_positive,
    validate_positive_int,
    validate_profit_targets,
    validate_unit_interval,
)


@dataclass(frozen=True)
class StrategyConfig:
    """Which sizing strategy to run and how to construct it.

    strategy_id is an opaque string label; this codebase has no
    id-to-class registry, so the caller maps it (see Run_Instructions).
    strategy_params are the constructor kwargs for that class.
    """

    strategy_id: str
    strategy_params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestSection:
    """Instrument and capital settings for a run."""

    symbol: str = "TQQQ"
    initial_cash: float = 100_000.0
    # Metadata/provenance only -- not yet wired to actively filter or
    # load historical_data (OptimizationController takes an
    # already-loaded DataFrame; no date-range/data-loading step exists
    # in this codebase to wire these into). Kept as optional, documented
    # placeholders for "date/time range, data settings" rather than
    # omitted, since they're genuinely useful record-keeping even
    # unwired -- but not claimed to do more than that.
    start_date: str | None = None
    end_date: str | None = None
    data_path: str | None = None


@dataclass(frozen=True)
class GridConfig:
    """The grid search space: drop thresholds and profit targets.

    Held as tuples rather than lists so the config stays immutable and
    hashable, which matters for the artifact hashing in Task 6.3.
    """

    steps: tuple
    profit_targets: tuple


@dataclass(frozen=True)
class CostConfig:
    """Maps to src/cost_models.py (Task 2.2). model_type="zero"
    (default) builds ZeroCostModel(); "slippage_commission" builds
    SlippageCommissionModel from commission_per_trade/slippage_bps;
    "dynamic_slippage" builds DynamicSlippageModel from
    base_bps/vol_multiplier/commission_per_trade.

    base_bps and vol_multiplier default to 0.0/1.0 -- DynamicSlippageModel's
    own no-op defaults -- so they only need setting when model_type is
    actually "dynamic_slippage"; every existing "zero"/"slippage_commission"
    config round-trips unchanged with these fields simply unused.
    """

    model_type: str = "zero"
    commission_per_trade: float = 0.0
    slippage_bps: float = 0.0
    base_bps: float = 0.0
    vol_multiplier: float = 1.0

    def build(self) -> TransactionCostModel:
        """Construct the real TransactionCostModel this config describes.

        Config carries data; this turns it into behavior. Raises
        ConfigurationError for an unrecognized model_type rather than
        silently falling back to zero cost, which would understate
        every subsequent result.
        """
        if self.model_type == "zero":
            return ZeroCostModel()
        if self.model_type == "slippage_commission":
            return SlippageCommissionModel(
                commission_per_trade=self.commission_per_trade, slippage_bps=self.slippage_bps
            )
        if self.model_type == "dynamic_slippage":
            return DynamicSlippageModel(
                base_bps=self.base_bps,
                vol_multiplier=self.vol_multiplier,
                commission_per_trade=self.commission_per_trade,
            )
        raise ConfigurationError(
            "costs.model_type must be 'zero', 'slippage_commission', or 'dynamic_slippage', "
            f"got {self.model_type!r}"
        )


@dataclass(frozen=True)
class RiskConfig:
    """Maps to src/risk_manager.py (Task 3.1), plus the
    dd_exposure_start/full/floor_pct drawdown-conditioned exposure
    throttle. Deliberately still omits halt_new_buys_if_drawdown_exceeds
    (the live-only CircuitBreaker threshold) -- that remains
    programmatic-only, unrelated to this config-driven throttle, which
    runs identically in both live and backtest."""

    max_concurrent_lots: int | None = None
    max_total_exposure: float | None = None
    dd_exposure_start: float | None = None
    dd_exposure_full: float = 0.60
    dd_exposure_floor_pct: float = 0.0

    def build(self) -> RiskManager:
        """Construct the real RiskManager this config describes.

        Both static limits default to None (unlimited), and
        dd_exposure_start defaults to None (no-op throttle), so an
        omitted risk section yields an unconstrained manager rather than
        an error.
        """
        return RiskManager(
            max_concurrent_lots=self.max_concurrent_lots,
            max_total_exposure_pct=self.max_total_exposure,
            dd_exposure_start=self.dd_exposure_start,
            dd_exposure_full=self.dd_exposure_full,
            dd_exposure_floor_pct=self.dd_exposure_floor_pct,
        )


@dataclass(frozen=True)
class SearchConfig:
    """Maps to run_sweep's search_strategy/rank_by/search_direction/
    search_seed (Task 5.3)."""

    strategy: str = "grid"
    rank_by: str = "Capital Velocity Index"
    direction: str = "maximize"
    seed: int | None = None


@dataclass(frozen=True)
class ExecutionConfig:
    """on_flat_reentry maps to run_sweep (Task 3.3). intrabar_priority
    maps to validate_finalists_intraday/simulate_single_intraday (Task
    2.3) and, since fill_model was added, to run_sweep as well.

    fill_model selects how a bar produces fills: "close" (default,
    original behavior -- a level must be reached by the bar's CLOSE)
    or "intrabar" (a level TOUCHED during the bar fills, at that
    level, modelling the resting limit orders a grid strategy actually
    uses). See OptimizationController._simulate_single for the
    measured difference -- roughly 1.85x more fills on both sides on
    this repo's own minute data -- and for why "close" remains the
    default despite that."""

    on_flat_reentry: str = "stale_reference"
    intrabar_priority: str = "sell_first"
    fill_model: str = "close"
    # Task 7.15's no-loss guard, made switchable rather than absolute.
    # TRUE (default) preserves today's behavior exactly: a sell whose
    # net proceeds would not cover the lot's allocated cost basis is
    # rejected. FALSE permits it.
    #
    # The guard is not arbitrary caution -- it encodes a real retail
    # edge. An institution is periodically FORCED to liquidate
    # (redemptions, mandates, risk limits); a retail book is not, so
    # declining to realize a loss is a structural advantage genuinely
    # available here. The cost is that lots accumulate through a decline
    # and ride it fully marked to market, which is why max drawdown
    # saturates near 80% on this dataset.
    #
    # NOTE this flag alone does not sell losers. Sells are only ever
    # ATTEMPTED on lots whose profit target has been touched, so
    # disabling the guard permits marginally-unprofitable target sells
    # (the cost-floor case) -- it does not create a capitulation exit.
    # See max_lot_age_days for that.
    enforce_no_loss: bool = True
    # Permits a strategy to close a lot for a reason unrelated to price
    # -- a regime flip, a shutdown -- realising a loss if the lot is
    # underwater. See src/no_loss_guard.SellReason.
    #
    # HALF of a two-part gate, and deliberately useless alone: a loss can
    # only be realised when this is True AND the strategy implements
    # lots_to_liquidate. Neither condition on its own changes anything,
    # so switching this on cannot by itself alter a single result.
    #
    # Defaults False, which reproduces every recorded result exactly.
    allow_signal_exit: bool = False
    # Sessions between a sale and its proceeds becoming spendable.
    #
    # 0 (default) is instant redeployment, which is what every recorded
    # result in this project was produced with. 1 is T+1, which is what
    # a CASH account actually imposes -- and the target deployment is
    # one: a Fidelity Traditional IRA, where buying with unsettled
    # proceeds is a good-faith violation.
    #
    # This does not model the violation RULE, it models the CASH. A
    # strategy that cannot fund a buy simply does not make it, which is
    # the conservative direction and the one that reveals how much of a
    # result depended on money that would not have been there.
    settlement_days: int = 0


@dataclass(frozen=True)
class OutputConfig:
    """What a sweep returns. return_full_results=True additionally
    yields per-combination trade blotters and equity curves."""

    return_full_results: bool = False


def expand_strategy_params(strategy_params: dict) -> list[dict]:
    """Turn list-valued strategy params into a grid of concrete kwargs.

    `{"a": [1, 2], "b": 3}` becomes `[{"a": 1, "b": 3}, {"a": 2, "b": 3}]`,
    mirroring how grid.steps/grid.profit_targets already sweep. Without
    this the sweep could only ever see ONE strategy parameter set --
    strategy_params was passed through as a single-element list -- so
    every tunable a strategy exposed was reachable from the Python API
    but not from a config file, which is where sweeps are actually
    defined.

    Scalars pass through untouched, so existing configs produce exactly
    one combination and are bit-identical to before.

    A list is ALWAYS a sweep axis here, never a literal value. That is a
    real constraint: a strategy taking a genuine list argument cannot
    express it in YAML. No current strategy does, and the alternative
    (a sentinel wrapper key) would add ceremony to every ordinary config
    to serve a case that does not exist yet.
    """
    if not strategy_params:
        return [{}]

    swept = {k: v for k, v in strategy_params.items() if isinstance(v, list)}
    if not swept:
        return [dict(strategy_params)]

    for key, values in swept.items():
        if not values:
            raise ConfigurationError(
                f"strategy_params[{key!r}] is an empty list -- it would produce zero "
                "combinations and silently sweep nothing."
            )

    fixed = {k: v for k, v in strategy_params.items() if not isinstance(v, list)}
    keys = list(swept)
    combinations = []
    for values in itertools.product(*(swept[k] for k in keys)):
        combo = dict(fixed)
        combo.update(dict(zip(keys, values, strict=True)))
        combinations.append(combo)
    return combinations


def _as_account_tuple(value) -> tuple:
    """Coerce an allowed_accounts value to a tuple of strings.

    A bare string is REJECTED rather than coerced: tuple("Z12345678")
    yields nine single-character entries, and an allowlist that silently
    became nine one-character accounts would still be non-empty, still
    pass every emptiness check, and match nothing -- or, worse, match
    something. That is precisely the quiet misconfiguration an allowlist
    exists to prevent, so it fails loudly instead.
    """
    if isinstance(value, str):
        raise ConfigurationError(
            "live.fidelity.allowed_accounts must be a LIST of account "
            f"numbers, not a bare string (got {value!r}). A string would be "
            "read as one entry per character."
        )
    try:
        return tuple(str(item) for item in value)
    except TypeError as exc:
        raise ConfigurationError(
            f"live.fidelity.allowed_accounts must be a list, got {type(value).__name__}"
        ) from exc


@dataclass(frozen=True)
class FidelityConfig:
    """Fidelity-venue settings. Only meaningful when live.broker == "fidelity".

    allowed_accounts is the user's explicit requirement and the reason
    this type exists at all. fidelity-api provides no allowlist and no
    validation: it selects an account with a case-insensitive SUBSTRING
    match against dropdown text. That fails closed on ambiguity
    (Playwright strict mode raises on 2+ matches) and on zero matches (a
    timeout), which is good -- but a truncated account number that
    uniquely matches the WRONG button would simply be clicked. So the
    allowlist is enforced here, before anything reaches the library, and
    matched exactly rather than by substring.

    Held as a tuple for the same reason GridConfig's lists are: the
    config must stay immutable and hashable for artifact hashing.

    dry_run defaults to True and flipping it is the deliberate go-live
    act. It is a separate switch from live.paper_trading because they
    mean different things: paper_trading selects a PAPER-mode OMS, while
    dry_run controls whether the browser stops at the order preview.
    A Fidelity account has no paper mode, so dry_run is the only thing
    standing between a preview and a real order.
    """

    allowed_accounts: tuple = ()
    account: str | None = None
    dry_run: bool = True


@dataclass(frozen=True)
class LiveConfig:
    """Live-trading switches.

    paper_trading=True (the default) routes to a PAPER-mode OMS that
    cannot touch real capital. Setting it False additionally requires
    passing promotion evidence (Task 7.7); it is not sufficient alone.

    step and profit_target are the SINGLE grid parameters the live loop
    trades, deliberately separate from grid.steps/grid.profit_targets.
    Those are lists a sweep explores; taking element [0] of a sweep list
    would make the parameters real capital trades on an implicit side
    effect of sweep ordering. They are required whenever enabled=True
    and validated as such -- there is no default, because there is no
    safe default for "which strategy is running".

    feed defaults to IEX because it is available on every Alpaca
    account. SIP covers the full market but requires a paid data
    subscription; selecting it without one makes every data request
    fail. The feed whitelist is ALPACA's -- it is only validated when
    broker == "alpaca", since those names mean nothing to another venue.

    broker defaults to "alpaca" so that every config written before
    Fidelity existed keeps its exact previous meaning. A second venue
    must be opted into by name, never arrived at by default.
    """

    enabled: bool = False
    paper_trading: bool = True
    step: float | None = None
    profit_target: float | None = None
    broker: str = "alpaca"
    fidelity: FidelityConfig | None = None
    feed: str = "iex"
    poll_interval_seconds: float = 60.0
    # Bounds one tick's harvest work. A tick that tried to place an
    # unbounded number of sell orders could stall past the next tick;
    # the remainder is simply picked up on the following pass.
    max_sells_per_tick: int = 25


@dataclass(frozen=True)
class BacktestConfig:
    """The complete, validated configuration for a run.

    Single source of truth for a sweep's settings, constructible from a
    dict or YAML (both go through from_dict, so they validate
    identically). Frozen, so a validated config cannot drift afterward.
    """

    strategy: StrategyConfig
    grid: GridConfig
    backtest: BacktestSection = field(default_factory=BacktestSection)
    costs: CostConfig = field(default_factory=CostConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    live: LiveConfig = field(default_factory=LiveConfig)

    @classmethod
    def from_dict(cls, data: dict) -> BacktestConfig:
        """Build a config from a nested dict.

        `strategy` (with strategy_id) and `grid` are required; every
        other section is optional and falls back to documented defaults,
        so a minimal config is genuinely runnable. Raises
        ConfigurationError naming the missing section otherwise.

        Note this only assembles the object -- call validate() to check
        ranges and cross-field constraints.
        """
        strategy_data = data.get("strategy")
        if not strategy_data or "strategy_id" not in strategy_data:
            raise ConfigurationError("config['strategy']['strategy_id'] is required")
        strategy = StrategyConfig(
            strategy_id=strategy_data["strategy_id"],
            strategy_params=dict(strategy_data.get("strategy_params", {})),
        )

        grid_data = data.get("grid")
        if not grid_data:
            raise ConfigurationError("config['grid'] is required")
        grid = GridConfig(
            steps=tuple(grid_data.get("steps", ())),
            profit_targets=tuple(grid_data.get("profit_targets", ())),
        )

        backtest_data = data.get("backtest", {})
        backtest = BacktestSection(
            symbol=backtest_data.get("symbol", "TQQQ"),
            initial_cash=backtest_data.get("initial_cash", 100_000.0),
            start_date=backtest_data.get("start_date"),
            end_date=backtest_data.get("end_date"),
            data_path=backtest_data.get("data_path"),
        )

        costs_data = data.get("costs", {})
        costs = CostConfig(
            model_type=costs_data.get("model_type", "zero"),
            commission_per_trade=costs_data.get("commission_per_trade", 0.0),
            slippage_bps=costs_data.get("slippage_bps", 0.0),
            base_bps=costs_data.get("base_bps", 0.0),
            vol_multiplier=costs_data.get("vol_multiplier", 1.0),
        )

        risk_data = data.get("risk", {})
        risk = RiskConfig(
            max_concurrent_lots=risk_data.get("max_concurrent_lots"),
            max_total_exposure=risk_data.get("max_total_exposure"),
            dd_exposure_start=risk_data.get("dd_exposure_start"),
            dd_exposure_full=risk_data.get("dd_exposure_full", 0.60),
            dd_exposure_floor_pct=risk_data.get("dd_exposure_floor_pct", 0.0),
        )

        search_data = data.get("search", {})
        search = SearchConfig(
            strategy=search_data.get("strategy", "grid"),
            rank_by=search_data.get("rank_by", "Capital Velocity Index"),
            direction=search_data.get("direction", "maximize"),
            seed=search_data.get("seed"),
        )

        execution_data = data.get("execution", {})
        execution = ExecutionConfig(
            on_flat_reentry=execution_data.get("on_flat_reentry", "stale_reference"),
            intrabar_priority=execution_data.get("intrabar_priority", "sell_first"),
            fill_model=execution_data.get("fill_model", "close"),
            enforce_no_loss=bool(execution_data.get("enforce_no_loss", True)),
            allow_signal_exit=bool(execution_data.get("allow_signal_exit", False)),
            settlement_days=int(execution_data.get("settlement_days", 0)),
        )

        output_data = data.get("output", {})
        output = OutputConfig(return_full_results=output_data.get("return_full_results", False))

        live_data = data.get("live", {})
        fidelity_data = live_data.get("fidelity")
        fidelity = None
        if fidelity_data is not None:
            fidelity = FidelityConfig(
                # tuple() for immutability/hashability, matching
                # GridConfig. A bare string would silently become a
                # tuple of CHARACTERS, so it is rejected rather than
                # coerced -- allowed_accounts: "Z123" reading as eight
                # single-character accounts is exactly the kind of quiet
                # misconfiguration an allowlist must not have.
                allowed_accounts=_as_account_tuple(fidelity_data.get("allowed_accounts", ())),
                account=fidelity_data.get("account"),
                dry_run=bool(fidelity_data.get("dry_run", True)),
            )
        live = LiveConfig(
            enabled=live_data.get("enabled", False),
            paper_trading=live_data.get("paper_trading", True),
            step=live_data.get("step"),
            profit_target=live_data.get("profit_target"),
            broker=live_data.get("broker", "alpaca"),
            fidelity=fidelity,
            feed=live_data.get("feed", "iex"),
            poll_interval_seconds=live_data.get("poll_interval_seconds", 60.0),
            max_sells_per_tick=live_data.get("max_sells_per_tick", 25),
        )

        return cls(
            strategy=strategy,
            grid=grid,
            backtest=backtest,
            costs=costs,
            risk=risk,
            search=search,
            execution=execution,
            output=output,
            live=live,
        )

    @classmethod
    def from_yaml(cls, yaml_source: str, is_path: bool = True) -> BacktestConfig:
        """is_path=True (default): yaml_source is a file path, read and
        parsed. is_path=False: yaml_source is the YAML text itself
        (useful for tests/inline config without a real file). Either
        way, deserializes through from_dict -- the identical path
        programmatic construction uses, so YAML-loaded and
        programmatically-built configs are validated identically."""
        import yaml

        if is_path:
            with open(yaml_source) as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_source)
        if not isinstance(data, dict):
            raise ConfigurationError(
                f"YAML config must deserialize to a mapping, got {type(data).__name__}"
            )
        return cls.from_dict(data)

    def validate(self) -> None:
        """Front-loaded validation, mirroring
        src/validation.py::validate_run_sweep_config's own contract
        (fail before any simulation/live work starts), reusing its
        actual helper functions rather than duplicating range checks."""
        if not self.strategy.strategy_id:
            raise ConfigurationError("strategy.strategy_id must not be empty")
        validate_positive(self.backtest.initial_cash, "backtest.initial_cash")
        validate_grid_steps(self.grid.steps)
        validate_profit_targets(self.grid.profit_targets)

        validate_one_of(
            self.costs.model_type,
            ("zero", "slippage_commission", "dynamic_slippage"),
            "costs.model_type",
        )
        validate_non_negative(self.execution.settlement_days, "execution.settlement_days")
        validate_non_negative(self.costs.commission_per_trade, "costs.commission_per_trade")
        validate_non_negative(self.costs.slippage_bps, "costs.slippage_bps")
        validate_non_negative(self.costs.base_bps, "costs.base_bps")
        validate_non_negative(self.costs.vol_multiplier, "costs.vol_multiplier")

        if self.risk.max_concurrent_lots is not None:
            validate_positive_int(self.risk.max_concurrent_lots, "risk.max_concurrent_lots")
        if self.risk.max_total_exposure is not None:
            validate_unit_interval(self.risk.max_total_exposure, "risk.max_total_exposure")
        # dd_exposure_start/full/floor_pct: validated by attempting to
        # build the real RiskManager rather than re-deriving its
        # ordering/ramp-base logic a second time here -- see
        # src/risk_manager.py's constructor for the authoritative checks.
        self.risk.build()

        validate_one_of(self.search.strategy, ("grid", "bayesian", "random"), "search.strategy")
        validate_one_of(self.search.direction, ("maximize", "minimize"), "search.direction")

        validate_one_of(
            self.execution.on_flat_reentry,
            ("stale_reference", "reset_to_market"),
            "execution.on_flat_reentry",
        )
        validate_one_of(
            self.execution.intrabar_priority,
            ("sell_first", "buy_first"),
            "execution.intrabar_priority",
        )
        validate_one_of(self.execution.fill_model, ("close", "intrabar"), "execution.fill_model")

        # Live parameters are range-checked when SUPPLIED, but their
        # PRESENCE is not required here. LiveExecutionLoop takes step
        # per call, so plenty of legitimate live.enabled configs never
        # need a config-level step at all; only the long-running trading
        # loop does, and it enforces that itself (see
        # src/live_trading_loop.py). Demanding them here would reject
        # configs that are genuinely complete for their use.
        if self.live.step is not None:
            validate_positive(self.live.step, "live.step")
        if self.live.profit_target is not None:
            validate_positive(self.live.profit_target, "live.profit_target")
        validate_positive(self.live.poll_interval_seconds, "live.poll_interval_seconds")
        validate_positive_int(self.live.max_sells_per_tick, "live.max_sells_per_tick")
        validate_one_of(self.live.broker, ("alpaca", "fidelity"), "live.broker")

        # The feed whitelist is ALPACA's -- "iex"/"sip" are names of
        # Alpaca data feeds and mean nothing at another venue, so
        # applying it to a Fidelity deployment would reject a config for
        # failing to name a feed it does not have. A Fidelity deployment
        # still needs a market-data source, but that is a separate
        # connection from the trading venue (see the plan's section H).
        if self.live.broker == "alpaca":
            validate_one_of(
                self.live.feed,
                ("iex", "sip", "delayed_sip", "otc", "boats", "overnight"),
                "live.feed",
            )

        if self.live.broker == "fidelity":
            if self.live.fidelity is None:
                raise ConfigurationError(
                    "live.broker='fidelity' requires a live.fidelity section "
                    "naming allowed_accounts -- there is no safe default for "
                    "which brokerage account real orders go to."
                )
            if not self.live.fidelity.allowed_accounts:
                raise ConfigurationError(
                    "live.fidelity.allowed_accounts must not be empty. The "
                    "library selects accounts by case-insensitive SUBSTRING "
                    "match on dropdown text, so an unconstrained account "
                    "string could match the wrong account."
                )

        if self.live.fidelity is not None:
            # Checked whenever the section is PRESENT, not only when the
            # broker is active: a config that names an account outside
            # its own allowlist is wrong however it is later used, and
            # catching it here means a broker switch cannot turn a latent
            # contradiction into a live order against the wrong account.
            for account in self.live.fidelity.allowed_accounts:
                if not str(account).strip():
                    raise ConfigurationError(
                        "live.fidelity.allowed_accounts contains a blank entry"
                    )
            account = self.live.fidelity.account
            if account is not None and account not in self.live.fidelity.allowed_accounts:
                raise ConfigurationError(
                    f"live.fidelity.account={account!r} is not in "
                    f"allowed_accounts={list(self.live.fidelity.allowed_accounts)!r}. "
                    "Exact match is required -- never a substring or a nickname."
                )

    def to_dict(self) -> dict:
        """Inverse of from_dict() -- round-trips through the same nested
        shape (BacktestConfig.from_dict(config.to_dict()) == config).
        Tuples (grid.steps/profit_targets, held as tuples internally for
        immutability/hashability) are converted back to lists, since
        JSON has no tuple type and this needs to be JSON-serializable
        for Task 6.3's configuration hash."""
        return {
            "strategy": {
                "strategy_id": self.strategy.strategy_id,
                "strategy_params": dict(self.strategy.strategy_params),
            },
            "grid": {
                "steps": list(self.grid.steps),
                "profit_targets": list(self.grid.profit_targets),
            },
            "backtest": {
                "symbol": self.backtest.symbol,
                "initial_cash": self.backtest.initial_cash,
                "start_date": self.backtest.start_date,
                "end_date": self.backtest.end_date,
                "data_path": self.backtest.data_path,
            },
            "costs": {
                "model_type": self.costs.model_type,
                "commission_per_trade": self.costs.commission_per_trade,
                "slippage_bps": self.costs.slippage_bps,
                "base_bps": self.costs.base_bps,
                "vol_multiplier": self.costs.vol_multiplier,
            },
            "risk": {
                "max_concurrent_lots": self.risk.max_concurrent_lots,
                "max_total_exposure": self.risk.max_total_exposure,
                "dd_exposure_start": self.risk.dd_exposure_start,
                "dd_exposure_full": self.risk.dd_exposure_full,
                "dd_exposure_floor_pct": self.risk.dd_exposure_floor_pct,
            },
            "search": {
                "strategy": self.search.strategy,
                "rank_by": self.search.rank_by,
                "direction": self.search.direction,
                "seed": self.search.seed,
            },
            "execution": {
                "on_flat_reentry": self.execution.on_flat_reentry,
                "intrabar_priority": self.execution.intrabar_priority,
                "fill_model": self.execution.fill_model,
                "enforce_no_loss": self.execution.enforce_no_loss,
                "allow_signal_exit": self.execution.allow_signal_exit,
                "settlement_days": self.execution.settlement_days,
            },
            "output": {"return_full_results": self.output.return_full_results},
            "live": {
                "enabled": self.live.enabled,
                "paper_trading": self.live.paper_trading,
                "step": self.live.step,
                "profit_target": self.live.profit_target,
                "broker": self.live.broker,
                # Omitted entirely when absent rather than emitted as
                # None, so that from_dict(to_dict(c)) == c holds for
                # every Alpaca config: from_dict builds a FidelityConfig
                # for any non-None value, and a None round-trips back to
                # None either way -- but an explicit null in the emitted
                # YAML would suggest a section that was configured and
                # left blank, rather than one that does not apply.
                **(
                    {
                        "fidelity": {
                            "allowed_accounts": list(self.live.fidelity.allowed_accounts),
                            "account": self.live.fidelity.account,
                            "dry_run": self.live.fidelity.dry_run,
                        }
                    }
                    if self.live.fidelity is not None
                    else {}
                ),
                "feed": self.live.feed,
                "poll_interval_seconds": self.live.poll_interval_seconds,
                "max_sells_per_tick": self.live.max_sells_per_tick,
            },
        }

    def to_run_sweep_kwargs(self, strategy_class) -> dict:
        """Builds the actual kwargs for
        OptimizationController.run_sweep(**kwargs) -- constructs real
        TransactionCostModel/RiskManager instances via costs.build()/
        risk.build(), not just passes config values through unchanged.
        strategy_class is an explicit argument since BacktestConfig only
        holds strategy_id (a string identifier). src/strategy_registry.py
        can now resolve one, but this signature stays explicit so a
        caller can sweep a class the registry does not know about."""
        return {
            "grid_steps": list(self.grid.steps),
            "profit_targets": list(self.grid.profit_targets),
            "strategy_class": strategy_class,
            "strategy_params_grid": expand_strategy_params(self.strategy.strategy_params),
            "cost_model": self.costs.build(),
            "risk_manager": self.risk.build(),
            "on_flat_reentry": self.execution.on_flat_reentry,
            "fill_model": self.execution.fill_model,
            "intrabar_priority": self.execution.intrabar_priority,
            "enforce_no_loss": self.execution.enforce_no_loss,
            "symbol": self.backtest.symbol,
            "initial_cash": self.backtest.initial_cash,
            "search_strategy": self.search.strategy,
            "search_seed": self.search.seed,
            "search_direction": self.search.direction,
            "rank_by": self.search.rank_by,
            "return_full_results": self.output.return_full_results,
        }
