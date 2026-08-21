# volatility-ai

A grid-based volatility-harvesting strategy for leveraged ETFs (primarily
TQQQ), with a backtesting engine, statistical validation, risk controls,
and live-execution scaffolding.

The system buys on configurable price-drop steps and harvests each lot at
its own profit target. Its defining constraint is a **no-loss invariant**:
it never intentionally sells a lot below its cost basis, and that rule is
enforced structurally rather than by convention.

![tests](https://img.shields.io/badge/tests-905%20passing-brightgreen)
![python](https://img.shields.io/badge/python-3.12%2B-blue)
![lint](https://img.shields.io/badge/lint-ruff-orange)

---

## Table of contents

- [Status and scope](#status-and-scope)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Getting market data](#getting-market-data)
- [Docker](#docker)
- [Configuration](#configuration)
- [Core concepts](#core-concepts)
- [Architecture](#architecture)
- [Safety invariants](#safety-invariants)
- [Statistical validation](#statistical-validation)
- [Going live: the promotion path](#going-live-the-promotion-path)
- [Testing](#testing)
- [Code style](#code-style)
- [Extending the system](#extending-the-system)
- [Troubleshooting](#troubleshooting)
- [Project layout](#project-layout)
- [Known gaps](#known-gaps)
- [License](#license)

---

## Status and scope

**What works today, end to end:**

- Backtesting with parameter sweeps (exhaustive or Bayesian search)
- Transaction cost modeling, including volatility-aware slippage
- Risk limits, a drawdown circuit breaker, and tick sanity-checking
- Walk-forward and Monte Carlo validation
- Durable SQLite persistence, crash recovery, and broker reconciliation
- A full order lifecycle state machine and audit trail
- Docker packaging with a single CLI entrypoint
- **Live/paper trading against Alpaca**, via `src/alpaca_broker.py` and the
  tick loop in `src/live_trading_loop.py`

**What to understand before running it with money:**

> **Paper is the default and real capital is gated.** `live.paper_trading`
> in the config decides which Alpaca endpoint is used. Reaching `Mode.LIVE`
> additionally requires a passing `PromotionEvaluation` — there is no
> boolean shortcut, so real capital is unreachable without recorded
> evidence that a paper-trading stage met its criteria.

> **Four sizing strategies exist**, selected by `strategy.strategy_id`:
> `fixed`, `bell_curve`, `rsi`, and `bayesian_dual_scale`. Only `fixed`
> has been through the promotion path; the other three are new and
> unvalidated live. The parameters the loop trades come from
> `live.step` / `live.profit_target`, which are deliberately separate from
> the `grid.*` sweep lists — see [Configuration](#configuration).

> **Feed parity is handled, but only if you keep it that way.** Both the
> live loop and `fetch-data` default to IEX, so backtest and production
> observe the same tape. That is not merely a preference: SIP's *realtime*
> endpoint rejects free accounts (`subscription does not permit querying
> recent SIP data`) even though its *historical* endpoint works, so it is
> possible to backtest on SIP and then be unable to trade on it. Change
> one side's feed and you have silently broken parity.

> **The default ranking metric can be uninformative.** `Capital Velocity
> Index` is `closed_lots / total_lots`, so it saturates at exactly 1.0
> whenever every lot closes — which is the normal case on a long dataset.
> When that happens, `search.rank_by` is sorting on a constant and the
> "top" row is arbitrary. Rank by `Total Return %` instead, and check the
> spread before trusting any ordering.

---

## Requirements

- **Python 3.12+** (`pyproject.toml` sets `requires-python = ">=3.12"`; the
  test suite is exercised against 3.12)
- Dependencies pinned in `requirements.txt`, with floors verified as a
  mutually-compatible set

| Package | Required for |
|---|---|
| `pandas`, `numpy` | Core — everything |
| `pyyaml` | `BacktestConfig.from_yaml` |
| `optuna` | Optional — only `search_strategy: bayesian` |
| `alpaca-py` | Required for live/paper trading; unused by backtests |
| `pytest`, `ruff` | Development only |

Optional dependencies fail *loudly and early* if missing: `BayesianSearch`
raises `ConfigurationError` at construction rather than silently falling
back to grid search.

---

## Quickstart

```bash
git clone https://github.com/AshitakaLax/volatility-ai.git
cd volatility-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Verify the install
python cli.py test -q
```

### Getting market data

`fetch-data` downloads real bars from Alpaca into `data/`:

```bash
export APCA_API_KEY_ID=... APCA_API_SECRET_KEY=...
python cli.py fetch-data --symbol TQQQ --days 730
```

That writes three things — a timestamped CSV, a `..._latest.csv` symlink,
and a `.meta.json` sidecar recording symbol, window, feed, adjustment, row
count and SHA-256. The sidecar is what keeps a sweep result traceable to
the exact data it ran on after you later refresh. `data/` is git-ignored;
downloads are tens of megabytes.

Three defaults are deliberate and worth knowing:

- **`--feed iex`.** SIP is the full consolidated tape and its *historical*
  endpoint works on a free account, but SIP *realtime* does not — it
  returns `subscription does not permit querying recent SIP data`. The
  live loop can therefore only ever observe IEX, so backtesting on SIP
  would tune parameters against a tape production cannot see. Match the
  feed you will trade on.
- **`--adjustment all`.** An unadjusted split reads as a ~66% single-bar
  crash (TQQQ split 3:1 in January 2022), which makes a grid strategy fire
  every rung at a price that never existed. The only thing that would flag
  it is a `logging.warning` that scrolls past in a sweep.
- **Regular trading hours only.** The live loop only ticks while Alpaca's
  clock says the market is open, so extended-hours bars are bars it can
  never act on. Pass `--include-extended-hours` to keep them.

The downloader runs `data_validation.validate()` *before* writing, so it
cannot emit a CSV the backtest would later reject.

**One honest limitation:** with regular-hours filtering the 16:00 bar is
followed by the next day's 09:30 bar, so a routine overnight gap on a 3x
ETF becomes a single bar-to-bar move that fires several grid rungs at an
open price nothing traded between. Minute-bar fills at the open are
therefore systematically optimistic. This is inherent to bar-based
backtesting, not a bug in the downloader.

### Run your first backtest

The CSV schema, which `fetch-data` emits and the backtest expects:

```csv
timestamp,open,high,low,close,volume
2024-01-02T14:30:00+00:00,50.0,50.075,49.925,50.0,12000000
```

Timestamps must be UTC-aware and strictly increasing. A 35-bar fixture
ships at `tests/fixtures/regression_ohlcv.csv` if you just want to see it
run without downloading anything.

Create `config/my-config.yaml`:

```yaml
strategy:
  strategy_id: fixed
  strategy_params:
    allocation_pct: 0.05      # 5% of equity per triggered buy
grid:
  steps: [0.005, 0.01, 0.015]       # buy on 0.5% / 1% / 1.5% drops
  profit_targets: [0.003, 0.005]    # harvest at 0.3% / 0.5% gain
```

Then:

```bash
python cli.py backtest \
  --config config/my-config.yaml \
  --data tests/fixtures/regression_ohlcv.csv \
  --output output/results.csv
```

This evaluates all 6 combinations (3 steps × 2 targets) and prints a
summary ranked by Capital Velocity Index.

### Or use the Python API directly

```python
import pandas as pd
from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage

df = pd.read_csv("data/TQQQ_1Min_latest.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)

controller = OptimizationController(historical_data=df)
results = controller.run_sweep(
    grid_steps=[0.005, 0.01, 0.015],
    profit_targets=[0.003, 0.005],
    strategy_class=FixedPortfolioPercentage,
    strategy_params_grid=[{"allocation_pct": a} for a in (0.02, 0.05)],
)
print(results.head())
```

---

## Docker

One image, one entrypoint, four subcommands.

```bash
docker build -t volatility-ai .
docker run --rm volatility-ai --help
```

Via compose, which also wires up volumes correctly:

```bash
docker compose run --rm test
docker compose run --rm test -k my_test -v          # args pass through

docker compose run --rm backtest \
  --config /app/config/my-config.yaml \
  --data /app/data/TQQQ_1Min_latest.csv

docker compose run --rm live --config /app/config/my-config.yaml --check-only
```

**Volumes.** `/app/state` is a *named* volume, not a bind mount, so the
SQLite ledger and audit log survive across separate `docker compose run`
invocations — which is what actually exercises the restart-recovery design
through the container lifecycle. `./data` and `./config` mount read-only;
`./output` is writable.

**Credentials** come only from an uncommitted env file via `env_file:` —
never baked into the image, and excluded from the build context by
`.dockerignore` even if one exists locally.

### Long-running deployment services

`docker-compose.yml` also defines `live-staging` and `live-production`,
with isolated state volumes (`state_staging`, `state_production`) so paper
and real-money ledgers can never mix.

Each needs its own uncommitted env file (`.env.staging`, `.env.production`)
holding the credentials for that Alpaca account.

```bash
docker compose up -d live-staging          # paper, 24/7
docker compose logs -f live-staging
docker compose stop live-staging           # SIGTERM: finishes the tick, then exits
```

Both run with `restart: unless-stopped`, and the loop handles `SIGTERM` by
finishing the current tick and settling in-flight orders before exiting —
so `docker stop` and a host reboot are both safe.

> ⚠️ **Run `live-staging` first, for long enough to mean something.**
> `live-production` trades real capital and is additionally gated on
> promotion evidence. Verify the audit trail and reconciliation on paper
> before going near it.

---

## Configuration

`BacktestConfig` (`src/config.py`) is the single source of truth. Build it
from a dict or YAML — both deserialize through the same path, so they
validate identically.

Only `strategy` and `grid` are required. Every other section falls back to
documented defaults, so a minimal config genuinely runs.

```yaml
strategy:
  strategy_id: fixed              # you map this to a class; see below
  strategy_params:
    allocation_pct: 0.05

grid:
  steps: [0.005, 0.01]            # each must be > 0 and < 1.0
  profit_targets: [0.003, 0.005]

backtest:
  symbol: TQQQ
  initial_cash: 100000.0

costs:
  model_type: zero                # "zero" | "slippage_commission"
  commission_per_trade: 0.0
  slippage_bps: 0.0

risk:
  max_concurrent_lots: null       # null = unlimited
  max_total_exposure: null        # null = unlimited, else 0.0-1.0

search:
  strategy: grid                  # "grid" | "bayesian"
  rank_by: Capital Velocity Index
  direction: maximize             # "maximize" | "minimize"
  seed: null                      # only used by bayesian

execution:
  on_flat_reentry: stale_reference  # or "reset_to_market"
  intrabar_priority: sell_first     # used by intraday validation

output:
  return_full_results: false      # true -> also get blotters + equity curves

live:
  enabled: false
  paper_trading: true             # true is a hard safety gate, see below
  step: 0.01                      # required by the trading loop
  profit_target: 0.005            # required by the trading loop
  feed: iex                       # iex (free) or sip (paid subscription)
  poll_interval_seconds: 60.0
  max_sells_per_tick: 25
```

**`live.step` / `live.profit_target` are separate from `grid.*` on
purpose.** The `grid` lists are a search space a sweep explores. These two
are the single parameter set the live loop actually trades. Defaulting them
to `grid.steps[0]` would make the parameters real capital runs an implicit
side effect of sweep ordering, so the loop refuses to start without them
being stated. Pick them from a backtest result, deliberately.

They are validated by `LiveTradingLoop`, not by `BacktestConfig.validate()`
— a config can legitimately set `live.enabled` without running the daemon.

**`strategy_id` requires a manual mapping.** This codebase has no
id-to-class registry, so you supply one:

```python
STRATEGY_REGISTRY = {"fixed": FixedPortfolioPercentage}
strategy_class = STRATEGY_REGISTRY[config.strategy.strategy_id]
results = controller.run_sweep(**config.to_run_sweep_kwargs(strategy_class))
```

Validation is **front-loaded** — `config.validate()` checks ranges and
cross-field constraints before any simulation starts, so a bad config fails
in milliseconds rather than after a long sweep.

---

## Core concepts

**Lot.** One purchase, tracked individually with its own cost basis and its
own `target_sell_price`, fixed at creation. Lots are never pooled, so each
exits on its own economics.

**Grid step.** The fractional price drop from the last buy that triggers the
next one. `0.01` means buy again after a 1% decline.

**Profit target.** The fractional gain at which a lot becomes eligible to
harvest. Eligibility is not permission — see the no-loss guard.

**MarketContext.** An immutable snapshot of one bar: OHLC plus portfolio
state (cash, equity, peak equity, drawdown, open lot count). It is what the
strategy sees, and it is frozen so a strategy cannot alter its own inputs.

**Capital Velocity Index.** The default ranking metric: closed lots ÷ total
lots. It rewards capital that recycles rather than capital that sits.

### Metrics produced

`Final Equity` · `Total Return %` · `Realized PnL` · `Trade Count` ·
`Closed Trade Count` · `Open Trade Count` · `Capital Velocity Index` ·
`Max Drawdown %`

---

## Architecture

### The canonical decision cycle

Backtest and live execution **share one implementation** of the strategy
call sequence (`src/decision_cycle.py`). This is not a convention — both
call the same functions, and a test asserts neither re-implements the
comparison locally.

```
┌───────────────────────────────────────────────┐
│  1. record_tick(context)     — every bar      │
│  2. harvest eligible lots    — sell before buy│
│  3. _check_grid_trigger()                     │
│  4. calculate_trade_value()                   │
│  5. risk clamp                                │
│  6. no-loss guard            ← exits only     │
└───────────────────────────────────────────────┘
```

Steps 1 and 3 are deliberately *separate* functions: `record_tick` fires at
the top of a bar, but the grid trigger is only evaluated **after** that
bar's harvest sells. Collapsing them would silently change when stateful
strategies observe the market.

### Module map

| Module | Responsibility |
|---|---|
| `optimization_controller.py` | Sweep orchestration; `_simulate_single` runs one combination |
| `src/decision_cycle.py` | The canonical strategy call sequence, shared by backtest and live |
| `src/size_calculators.py` | `SizingStrategy` ABC + `FixedPortfolioPercentage` |
| `src/ledger.py` | Lot-based position tracking, full and partial closes |
| `src/no_loss_guard.py` | **The** no-loss comparison — one implementation |
| `src/cost_models.py` | Zero / static slippage / volatility-aware slippage |
| `src/risk_manager.py` | Exposure clamps + `CircuitBreaker` |
| `src/market_context.py` | `MarketContext`, `SimulationResult` |
| `src/config.py` | `BacktestConfig` and its nested sections |
| `src/validation.py`, `src/data_validation.py` | Config and dataset validation |
| `src/search_strategies.py` | `GridSearch`, `BayesianSearch` (Optuna) |
| `src/walk_forward.py`, `src/monte_carlo.py` | Out-of-sample validation |
| `src/persistence.py` | SQLite ledger store, crash recovery |
| `src/audit.py` | Durable, append-only event log |
| `src/order_lifecycle.py` | Order state machine + broker status mapping |
| `src/reconciliation.py` | Local vs. broker state comparison |
| `src/runtime_lifecycle.py` | Startup sequence and graceful shutdown |
| `src/promotion.py` | Paper→live promotion gate |
| `src/retry_policy.py` | Error classification and bounded backoff |
| `src/secrets.py` | Credential loading and redaction |
| `src/idempotency.py`, `src/duplicate_order_guard.py` | Event and order deduplication |
| `src/tick_validation.py` | Per-tick sanity checks |
| `src/historical_data.py` | Bulk bar download -> backtest-ready CSV |
| `src/sizing_indicators.py` | Incremental rolling max / Wilder RSI, shared by strategies |
| `src/bayesian_sizing_calculators.py` | `BayesianDualScaleSizing` (dual-timescale Beta posterior) |
| `src/strategy_registry.py` | `strategy_id` -> sizing-strategy class |
| `src/alpaca_broker.py` | The `LiveBroker` implementation — order submission, lookup, snapshot |
| `src/alpaca_market_data.py` | Latest bar and market clock |
| `src/live_trading_loop.py` | The tick loop: fills, harvest, buy, persist, shutdown |
| `src/exceptions.py` | Domain exception hierarchy |

### Exception hierarchy

All domain errors descend from `TradingSystemError`, so callers can catch
broadly or precisely:

```
TradingSystemError
├── ConfigurationError      bad config, missing credentials, failed gates
├── DataValidationError     unusable historical data
├── StrategyError           strategy-level failures
├── RiskError               risk-limit violations
├── ExecutionError          order/execution failures
│   ├── NoLossViolation             a sell would realize a loss
│   └── AmbiguousSubmissionError    outcome unknown — reconcile, never retry
├── ReconciliationError     local and broker state disagree
└── PersistenceError        durable write/read failures
```

---

## Safety invariants

These are enforced *structurally* — the code has no path to violate them —
rather than by documentation or convention.

### 1. Never sell at a loss

`src/no_loss_guard.py` is the single place this is evaluated. Two
independent inline copies existed previously and had already begun to
drift; they were folded into one, and a test scans the codebase for any
reintroduced duplicate.

```
allocated_cost_basis = buy_price × quantity
net_sell_proceeds    = quantity × effective_sell_price − sell_costs
permitted            ⟺ net_sell_proceeds ≥ allocated_cost_basis − 1e-8
```

A nominally profitable target that becomes a loss after commission and
slippage is **rejected before submission**.

> **Practical consequence worth knowing:** under realistic slippage, very
> thin profit targets stop being viable exits at all. A 0.5% target against
> a volatile bar's modeled slippage will simply never clear the guard. Two
> safety mechanisms interacting correctly — but it shapes which
> `profit_targets` are worth testing.

### 2. A halt never forces liquidation

`CircuitBreaker`, `RuntimeLifecycle`, and `Reconciler` expose **no**
liquidation method — asserted by test. A halt blocks *new buys*; existing
lots remain fully eligible for normal profitable harvest.

### 3. Halts require a human

States are `ACTIVE`, `HALTED_NEW_BUYS`, and `MANUAL_RESET_REQUIRED`. A
recovering drawdown moves to `MANUAL_RESET_REQUIRED` — it does **not**
auto-resume, because the point is to force a human to look. Resets require
a named operator, and the halt persists across restarts (repeated restarts
cannot clear it).

### 4. Reconciliation never invents a transaction

Auto-repair fires only when a broker-confirmed fill lands on an order
already held as live under our own client order ID. Everything ambiguous
halts. There is no method to manufacture a fill, lot, or cash movement.

### 5. Ambiguity is never retried

A transport failure *after* an order submission is `AMBIGUOUS` — it is
unknown whether the broker received it. It raises a distinct exception type
so it cannot be caught by the same `except` branch as ordinary failures,
and it routes to reconciliation-by-client-order-ID rather than a retry.

### 6. Credentials never reach logs

`LiveCredentials` overrides `__repr__`/`__str__`, so credentials cannot
appear in a log line, f-string, `%`-format, `.format()` call, or traceback
— even when the object is logged directly. Audit payloads are redacted
before writing; deployment artifacts *reject* secret-looking keys outright.

---

## Statistical validation

A single backtest is one sample, not a result. Two tools exist for this,
and using them is the difference between a finding and a coincidence.

### Walk-forward

Selects parameters on a training window and scores them **only** on the
following held-out window. Result columns are prefixed `train_` and `test_`
so in-sample and out-of-sample figures cannot be confused.

```python
from src.walk_forward import WalkForwardRunner

runner = WalkForwardRunner(
    lambda df_slice: OptimizationController(historical_data=df_slice),
    train_window=250,
    test_window=50,
    step=50,
)
folds = runner.run(
    df,
    grid_steps=[0.005, 0.01],
    profit_targets=[0.003, 0.005],
    strategy_class=FixedPortfolioPercentage,
    strategy_params_grid=[{"allocation_pct": 0.05}],
)
```

### Monte Carlo

Block-bootstraps the return series into synthetic paths — contiguous
blocks, not individual days, so volatility clustering survives. Returns
5th/25th/50th/75th/95th percentiles.

```python
from src.monte_carlo import MonteCarloRunner

summary = MonteCarloRunner().run(
    controller_factory=lambda p: OptimizationController(historical_data=p),
    n_paths=500,
    block_size=20,
    step=0.01,
    target=0.005,
    strategy_class=FixedPortfolioPercentage,
    strategy_params={"allocation_pct": 0.05},
    historical_data=df,
    seed=42,
)
```

Each path gets an independent child seed derived from `seed`, so runs are
reproducible without any two paths sharing a random stream.

> **If two configurations differ by less than the Monte Carlo spread, they
> do not differ.** Sweeping many combinations and taking the maximum is
> multiple-comparison shopping; it reliably finds the luckiest, not the
> best.

---

## Going live: the promotion path

Real capital is **structurally unreachable** from a backtest result.

```
  Backtest              Paper                 Live
  Mode.SIMULATION  →    Mode.PAPER      →     Mode.LIVE
                                                 ↑
                                      requires a passing
                                      PromotionEvaluation
```

`Mode.PAPER` is a first-class mode, not a boolean on `LIVE`, so reaching
real capital is an explicit, auditable step. Constructing a `Mode.LIVE`
OMS requires a passing `PromotionEvaluation` — there is no
`enable_live=True` shortcut, and a truthy-but-not-passing object is
rejected.

**Promotion criteria** (`src/promotion.py`), all machine-checked and
recorded in the artifact rather than left to judgment:

| Criterion | Default |
|---|---|
| Minimum paper-trading duration | 5 days |
| Minimum strategy decisions | 20 |
| Minimum fills | 5 |
| Accounting discrepancies | 0 |
| Duplicate-order incidents | 0 |
| No-loss guard violations | 0 |
| Unresolved reconciliations | 0 |
| Unhandled exceptions | 0 |

`evaluate_promotion` reports **every** unmet criterion at once, not just the
first. A gate configured with zero required days or fills is itself
rejected — it would pass a strategy that never traded.

### Credentials

Environment only. Never in config, never in source control, never in an
artifact.

| Variable | Purpose |
|---|---|
| `APCA_API_KEY_ID` | Alpaca API key ID |
| `APCA_API_SECRET_KEY` | Alpaca API secret key |

Missing credentials raise `ConfigurationError` naming exactly which
variables are absent — never a silent fallback to simulation.

Use a **paper** key pair for staging and a **live** key pair for
production; they are different credentials at Alpaca, and `paper_trading`
only selects the endpoint — it does not make a live key safe.

### Running the loop

```bash
# Health check: connect, reconcile, exit. Places no orders.
python cli.py live --config config/staging.yaml --check-only

# Bounded run, useful for a first supervised session.
python cli.py live --config config/staging.yaml --max-ticks 20

# Unbounded: what the containers run. Stops on SIGTERM/SIGINT.
python cli.py live --config config/staging.yaml
```

Startup walks `STARTING → LOAD_CONFIG → LOAD_STATE → CONNECT_BROKER →
RECONCILE → VALIDATE_DATA_CLOCK → READY` and refuses to trade unless it
reaches `READY`. Each tick then: applies confirmed fills, records the tick,
harvests lots at target, and evaluates the grid trigger for a buy.

**Fills are asynchronous.** Submitting an order mutates nothing; a later
tick polls the broker and only the confirmed increment moves cash or lots.
An in-flight order is therefore invisible to sizing — the strategy
under-counts what it may already own rather than spending twice.

---

## Testing

```bash
python cli.py test              # everything
python cli.py test -q           # quiet
python cli.py test -k promotion # filtered
pytest tests/unit -q            # or invoke pytest directly
```

**905 passing** (a parallelism timing test auto-skips on single-core
machines).

| Suite | Count |
|---|---|
| `tests/unit` | 660 |
| `tests/integration` | 143 |
| Regression baseline | 1 |
| Live-execution parity | 3 |

### The regression baseline

`tests/test_regression_baseline.py` pins a full sweep result value-for-value
and asserts **no extra columns** appear. It has caught real behavioral drift
repeatedly across development. If you change result columns intentionally,
update the baseline deliberately — do not loosen the assertion.

### Testing conventions

- SDK behavior is **verified, not assumed** — tests enumerate `alpaca-py`'s
  real `OrderStatus` enum and fail if a future release adds a value
- Clocks and sleeps are injected, so bounded-window logic tests
  deterministically without real delays
- CLI behavior is tested through real subprocesses, since exit codes and
  argument parsing are what a `docker run` actually exercises

---

## Code style

Formatting and linting are both handled by **ruff**, configured in
`pyproject.toml`.

```bash
ruff format .            # apply
ruff format --check .    # verify only (CI)
ruff check .             # lint
ruff check --fix .       # lint + safe fixes
```

`line-length = 100`, chosen by measuring the existing code (p95 was 87, p99
was 106) rather than accepting the 88 default, which would have rewrapped
~4.5% of all lines instead of ~1.6%.

Two exemptions, both documented in `pyproject.toml` with reasons: `E501` at
lint level (operator-facing error strings deliberately name specific deltas
so they are actionable without reading source), and `C408` in `tests/` only
(kwargs-builder dicts).

---

## Extending the system

### Adding a sizing strategy

Subclass `SizingStrategy` and implement two methods:

```python
from src.size_calculators import SizingStrategy


class DrawdownScaledSizing(SizingStrategy):
    """Scale in harder as drawdown deepens."""

    def __init__(self, base_pct: float, scale: float):
        self.base_pct, self.scale = base_pct, scale

    def record_tick(self, context) -> None:
        """Called every bar, unconditionally. Update rolling state here."""

    def calculate_trade_value(self, context) -> float:
        """Called only on a confirmed grid trigger."""
        scaled = self.base_pct * (1 + self.scale * context.drawdown)
        return context.equity * min(scaled, 0.5)
```

Optionally override `_check_grid_trigger(context, last_buy_price, step)` to
change *entry timing* rather than sizing.

> **Note the asymmetry:** `record_tick` fires on every bar, but
> `calculate_trade_value` fires only on triggers. Accumulate rolling state
> in `record_tick`, or a stateful strategy will see a sparse,
> downward-biased sample of the market.

### Comparing strategies

`run_sweep` takes one `strategy_class` per call, and result rows carry no
strategy identifier — so merging two sweeps produces sparse columns you
must disambiguate by hand:

```python
merged = pd.concat([sweep_a, sweep_b], ignore_index=True)
# allocation_pct  base_pct  scale   <- which row is which algorithm?
#           0.05       NaN    NaN
#            NaN      0.05    2.0
```

Adding a strategy registry, a `strategy_id` result column, and a
`compare_strategies` helper is the natural next step. Note that adding a
column will trip the regression baseline by design.

### Adding a cost model

Subclass `TransactionCostModel` and implement `apply_buy` / `apply_sell`,
each returning `(effective_price, cost)`. Slippage folds into the price;
commissions are the separate cost term. Models are **pure** — they compute
and return, never mutate.

---

## Troubleshooting

**`DataValidationError` on load.** The dataset is empty, has missing
columns, contains NaN/inf or non-positive prices, or has an unsorted or
duplicated index. The message names the offending timestamps (truncated to
five, with a `+N more` suffix).

**`ConfigurationError: grid step must be < 1.0`.** A step of `1.0` is a 100%
drop, which can never trigger twice from any positive price — it is
incompatible with the grid mechanics, not merely out of range.

**Every sell is rejected; `Closed Trade Count` is 0.** Modeled costs exceed
your profit target. Either raise `profit_targets` or reduce
`costs.slippage_bps` / `commission_per_trade`. This is the no-loss guard
working correctly.

**`BayesianSearch requires the 'optuna' package`.** Install `optuna`, or
use `search_strategy: grid`.

**`live` exits with `RECOVERY_REQUIRED`.** Startup could not safely
continue. The stderr message names the stage: missing credentials (it names
the variables), credentials the broker rejected, or an unreadable ledger.

**`live` exits with `RECONCILIATION_REQUIRED`.** Local state and the broker
disagree. This is deliberately not self-healing — the diagnostic names the
specific delta, and a human must resolve it. The circuit-breaker halt
persists across restarts, so restarting the container will not clear it.

**`live.step and live.profit_target are both required`.** The trading loop
needs the single parameter set it will trade. They are not defaulted from
`grid.steps` / `grid.profit_targets`, because those are sweep lists.

**The loop runs but never trades.** Check that the market is open (it skips
closed sessions), and that the IEX feed is returning bars — on a thin
symbol IEX can report no bar for an interval, which is logged and skipped
rather than filled in.

**Sweeps are slow.** Use `n_jobs > 1` for process-level parallelism, or
`search_strategy: bayesian` to explore a large space with a fraction of the
evaluations.

---

## Project layout

```
volatility-ai/
├── cli.py                     # single entrypoint: test | backtest | live
├── optimization_controller.py # sweep orchestration
├── Dockerfile
├── docker-compose.yml         # test/backtest/live + staging/production
├── pyproject.toml             # ruff config, Python floor
├── requirements.txt
├── Run_Instructions           # detailed usage walkthrough
├── CHANGELOG.md               # design decisions and rationale
├── config/
│   ├── staging.yaml           # paper account
│   └── production.yaml        # real capital
├── src/                       # 35 modules -- see the module map
└── tests/
    ├── unit/                  # 660 tests
    ├── integration/           # 143 tests
    └── fixtures/              # synthetic OHLCV + regression baseline
```

`CHANGELOG.md` documents *why* decisions were made, including several
resolved specification contradictions. It is worth reading before changing
anything load-bearing.

---

## Known gaps

Tracked honestly rather than hidden:

1. **`Capital Velocity Index` saturates and is the default `rank_by`.**
   It is `closed_lots / total_lots`, so on any dataset long enough for
   every lot to close it is exactly 1.0 for every combination and ranks
   nothing. Verified on 2 years of TQQQ minute bars: all 9 combinations
   scored 1.0. The metric was implemented from a name with no specified
   formula (see `src/performance_analyzer.py`'s docstring); it needs
   either a denominator that does not saturate — time-weighted capital
   deployed, say — or demotion from the default.
2. **`ACCEPTED → UNKNOWN` is not a permitted transition.** The order state
   machine follows its specified table literally. In practice an accepted
   order *can* become unknown (connection drop, query timeout), and today
   such an order stays recorded as `ACCEPTED`. **This needs a decision
   before trading real capital** — it is the difference between knowing you
   have lost track of an order and believing you have not.
3. **No live test against a real Alpaca account.** The broker adapter and
   trading loop are covered by tests against fakes and against the
   installed SDK's real request/response models, but nothing here has yet
   placed an order at Alpaca — not even on paper. Run staging first and
   read the audit trail before trusting it.
4. **Fills are polled, not streamed.** The loop queries order status once
   per tick rather than consuming Alpaca's trade-update websocket. Fills
   are therefore recognized within one poll interval rather than
   immediately. Correct, but not the lowest-latency design available.
5. **No CI.** 905 tests and a clean ruff run, but nothing enforces them
   automatically on push.
6. **No strategy registry.** `strategy_id` requires a manual mapping.
7. **Multi-strategy comparison is manual.** See
   [Extending the system](#extending-the-system).
8. **Macro/seasonality fields are inert.** `MarketContext` carries
   `time_of_day_flag`, `is_macro_event_day`, and `macro_surprise_factor`,
   but nothing consumes them. Investigated and deliberately deferred — see
   `CHANGELOG.md`.

---

## License

No license file is currently present. Add one before distributing.

---

## Disclaimer

This software is for research and educational purposes. Leveraged ETFs such
as TQQQ carry substantial risk, including volatility decay that can produce
losses even when the underlying index is flat over the same period. Nothing
here is financial advice. Backtested performance is not indicative of future
results, and the statistical caveats in
[Statistical validation](#statistical-validation) exist because it is easy
to fool yourself. **Do not deploy real capital without completing the
promotion path — and understanding the known gaps above.**
