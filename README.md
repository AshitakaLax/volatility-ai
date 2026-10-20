# volatility-ai

A volatility-harvesting system for leveraged ETFs (primarily TQQQ): a
minute-bar backtesting and research engine, a web UI and distributed sweep
queue, and live trading through Alpaca or a Fidelity browser bridge.

It buys on configurable price-drop steps and harvests each lot at its own
profit target. Its defining constraint is a **no-loss invariant**: it never
sells a lot below its cost basis, enforced structurally in one module. The
only exception is a strategy's explicit regime exit, which needs a config
flag *and* a strategy hook.

![python](https://img.shields.io/badge/python-3.12%2B-blue)
![lint](https://img.shields.io/badge/lint-ruff-orange)

- [Core features](#core-features)
- [Before you trade money](#before-you-trade-money)
- [Installation (Linux)](#installation-linux)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Safety invariants](#safety-invariants)
- [Live trading and the promotion path](#live-trading-and-the-promotion-path)
- [Running it as services](#running-it-as-services)
- [Testing and code style](#testing-and-code-style)
- [Extending the system](#extending-the-system)
- [Troubleshooting](#troubleshooting)
- [Project layout](#project-layout)
- [Known gaps](#known-gaps)

---

## Core features

### Trading engine (`engine/`)
- **Lot-based ledger** — every buy is its own lot with its own cost basis
  and target; full and partial closes; never pooled.
- **One decision cycle for backtest and live** (`trading/decision_cycle.py`):
  record tick → harvest → grid trigger → size → risk clamp → no-loss guard.
- **No-loss guard** (`trading/no_loss_guard.py`) — the single cost-basis
  check, cost-aware, scanned for duplicates by a test.
- **Strategy-driven exits** — per-lot retargeting (`adjust_profit_target`)
  and regime exits (`lots_to_liquidate`, gated by `execution.allow_signal_exit`).
- **Risk controls** — lot-count and exposure caps, a drawdown
  `CircuitBreaker` whose halts block buys, never liquidate, and need a
  named human to reset.
- **Order management** — an order state machine with broker-status mapping,
  idempotent events, a duplicate-order guard, and ambiguous submissions
  routed to reconciliation instead of retried.
- **Durable state** — SQLite ledger store, append-only audit log, crash
  recovery, and local-vs-broker reconciliation that never invents a fill.
- **Brokers** — Alpaca (`brokers/alpaca_broker.py`, paper or live) and
  Fidelity (`fidelity_gateway/`), chosen by `live.broker`.
- **Cost models** — zero, static slippage + commission, and
  volatility-aware dynamic slippage; pure functions.
- **Fill models** — close-only or intrabar (touch) fills, with `level`,
  `open_or_level` and `causal` booking of gap fills; sell-first or
  buy-first intrabar priority; optional settlement delay; historical
  money-market yield on idle cash.
- **Market data** — Alpaca bar download and live polling (IEX by default,
  for backtest/live feed parity), dataset and per-tick validation, session
  structure, and FOMC / macro-event / earnings calendars.
- **Analytical warehouse** (`warehouse/`) — DuckDB over a Parquet lake of
  minute bars, external macro series (FRED/CBOE/Yahoo, with publication
  lags) and trade executions; deduplicated simulation results; lag-aware
  ASOF joins.
- **Promotion gate** — `Mode.LIVE` is unreachable without a passing
  `PromotionEvaluation` recorded from paper trading.

### Research (`research/`)
- **Strategy registry** (`strategies/strategy_registry.py`), with each
  strategy's parameter schema and defaults (`param_schema.py`):
  - `fixed`, `bell_curve`, `rsi`, `bayesian_dual_scale` — the early sizers
  - `hf_local_reference` — the champion high-frequency grid: local-reference
    trigger, volatility and volume scaling, event-day boosts
  - `hf_entry_gated` — the same with entry gates (breakdown, dual thrust,
    opening range, candlestick patterns, intraday momentum, RSI, volatility
    targeting)
  - `ultimate` — a causal NATR volatility regime with a bear filter: the
    champion grid while calm, capitulation-close reversal lots while
    turbulent, and a delayed regime exit
    ([design log](docs/research/ultimate-algorithm.md))
  - `ultimate_rsp`, `ultimate_ursp` — daily-timed exposure books for RSP and
    a simulated 3x RSP
  - `ml_reachability_*`, `ml_regime_*` — learned sizing (LightGBM),
    research only
- **Sweeps** — grid, Bayesian (Optuna TPE) and random search, run in
  parallel processes with checkpointed output (`run_hf_sweep.py`,
  `optimization/`), plus warm-up history for regime strategies.
- **Validation** — walk-forward (train/test folds), block-bootstrap Monte
  Carlo, intraday validation, and year-by-year comparison with buy-and-hold
  (`analysis/analyze_annual.py`).
- **Metrics** — return, CAGR, max drawdown, return/drawdown, Sharpe and
  Sortino, calendar-year returns, trade and signal-exit counts, buy-and-hold
  benchmark.
- **ML line** (`ml/`) — causal feature and label builders, an incremental
  bar-feature engine that matches the offline features by construction, and
  regime models. Read-only unless a strategy id selects them.

### Backend and UI (`server/`, `web/`)
- **FastAPI backend** (`cli.py serve`, loopback by default): run backtests
  and sweeps, query run history and fills server-side, browse bars and
  datasets, read live deployment state, and halt the circuit breaker.
- **Durable job queue** — pending runs and per-configuration checkpoints
  survive restarts; pause, resume, cancel, reorder.
- **Distributed sweeps** — extra machines join with `cli.py shard`, claim
  whole sweeps, cache bars by fingerprint and stream results back; daily
  lockout windows per shard. `cli.py submit` queues any sweep YAML.
- **React web UI** — parameter form, active runs and shard panel, run
  history, result view (price chart with fills, trade log, sweep heatmap,
  fund comparison), live command center (deployment health, order ledger,
  algorithm status), and an ML insights tab.

### Fidelity route (`fidelity_gateway/`)
- **Browser-extension bridge** — the Fidelity Bridge extension (submodule
  `fidelity-bridge-chrome-extension/`) connects to a local WebSocket
  server with an HMAC handshake; the engine drives the tab you signed into
  by hand, and nothing on a working path logs in.
- **Preview-only and placing brokers** — separate classes; placing sits
  behind explicit gates, with a journal of confirmation numbers written
  before each commit and read back on start.
- **Two independent endpoint allowlists** (here and in the extension), kept
  in agreement by a test; the extension can show and, when allowed, change
  the live algorithm.
- **Discovery tools** — traffic capture, HAR analysis and redaction, and
  reconnaissance over a remote-debugging port.

### Operations (`cli.py`, `tools/`, Docker)
- **One entrypoint**: `test`, `fetch-data`, `backtest`, `search`, `submit`,
  `live`, `serve`, `shard`, `backup`, `restore`.
- **One Docker Compose file** for everything that stays up: the UI with its
  backtest engine, the paper trading loop and a daily backup; Ultimate in
  paper and real money behind profiles; one-off tools (tests, preflight,
  fetch, ingest, backtest) for `docker compose run`.
- **Session supervision** — the market-hours supervisor asks Alpaca when
  each session opens and closes; a strategy is replayed the recent history
  its state spans before its first tick; `docker stop` is a graceful stop.
- **Backups** of the ledgers and warehouse catalogs, daily, optionally
  copied off the machine.
- **Data prep** — warehouse ingest, external macro series, earnings
  calendar, and ML datasets.

---

## Before you trade money

> **Paper is the default and real capital is gated.** `live.paper_trading`
> picks the Alpaca endpoint, and `Mode.LIVE` additionally requires a
> passing `PromotionEvaluation`. There is no boolean shortcut.

> **Only `fixed` has been through the promotion path.** Every other
> strategy is backtested, not live-validated. The parameters the loop
> trades come from `live.step` / `live.profit_target`, deliberately
> separate from the `grid.*` sweep lists.

> **Keep feed parity.** The live loop and `fetch-data` both default to IEX.
> SIP's historical endpoint works on a free account but its realtime one
> does not, so a SIP backtest can tune against a tape production cannot see.

> **Backtests flatter.** Minute bars turn an overnight gap into one
> bar-to-bar move; sweeping many combinations and taking the best finds the
> luckiest, not the best. See [docs/sweeps.md](docs/sweeps.md) and the
> deflated-Sharpe and overfitting caveats in the research logs.

---

## Installation (Linux)

Python 3.12 or newer. Debian/Ubuntu ship `venv` separately:

```bash
sudo apt install python3-venv          # python3.14-venv on newer releases
git clone --recurse-submodules https://github.com/AshitakaLax/volatility-ai.git
cd volatility-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-warehouse.txt
.venv/bin/python cli.py test -q        # verify
```

Optional dependency sets, installed only where needed:

| File | For |
|---|---|
| `requirements.txt` | core: pandas, numpy, pyyaml, optuna, alpaca-py, pytest, ruff |
| `requirements-warehouse.txt` | duckdb, polars, pyarrow — every backtest reads bars through it |
| `requirements-web.txt` | `cli.py serve` (FastAPI, uvicorn) |
| `requirements-indicators.txt` | TA-Lib and indicator libraries (entry gates, regime tests) |
| `requirements-ml.txt` | scikit-learn, LightGBM (`ml_*` strategies; needs `libgomp1`) |
| `requirements-fidelity.txt` | the Fidelity route (playwright, websockets) |
| `requirements-qlib.txt` | qlib regime research only |

The web UI needs Node: `cd web && npm install && npm run dev`.

Optional dependencies fail loudly and early: e.g. `BayesianSearch` raises
`ConfigurationError` at construction if Optuna is missing.

---

## Quickstart

Backtests read bars from the warehouse by ticker (`backtest.symbol`), never
from a CSV. Fetch, ingest, run:

```bash
export APCA_API_KEY_ID=... APCA_API_SECRET_KEY=...
.venv/bin/python cli.py fetch-data --symbol TQQQ --days 730   # → data/
.venv/bin/python tools/build_warehouse.py --ingest TQQQ       # → warehouse/
.venv/bin/python cli.py backtest --config config/ultimate_tqqq.yaml --output output/ultimate.csv
```

No Alpaca account? A small fixture works:
`.venv/bin/python tools/build_warehouse.py --csv tests/fixtures/regression_ohlcv.csv --ingest DEMO`,
then set `backtest.symbol: DEMO`.

`fetch-data` defaults are deliberate: `--feed iex` (parity, above),
`--adjustment all` (an unadjusted split reads as a ~66% one-bar crash), and
regular hours only (the live loop never acts outside them). It validates
before writing, so it cannot produce a file the ingest rejects.

From Python:

```python
from engine.warehouse.bars import load_frame
from research.optimization.optimization_controller import OptimizationController
from research.strategies.strategy_registry import resolve_strategy

controller = OptimizationController(historical_data=load_frame("TQQQ"))
results = controller.run_sweep(
    grid_steps=[0.005, 0.01],
    profit_targets=[0.003, 0.005],
    strategy_class=resolve_strategy("fixed"),
    strategy_params_grid=[{"allocation_pct": 0.05}],
)
```

Research sweeps (parallel workers, random/Bayesian search, the record of
every sweep run so far) are documented in [docs/sweeps.md](docs/sweeps.md);
[docs/Run_Instructions](docs/Run_Instructions) is a longer walkthrough whose
code blocks the test suite executes.

### Docker

```bash
docker compose up -d --build                     # web (UI + engine) on 127.0.0.1:8000, paper, backup
docker compose run --rm test -q                  # args pass through to pytest
docker compose run --rm backtest --config /app/config/ultimate_tqqq.yaml
docker compose run --rm preflight                # before a trading loop's first start
```

One file, `docker-compose.yml`. Each trading service has its own
uncommitted env file (its Alpaca account) and its own named volume (its
ledger), so books can never mix; `./config` mounts read-only. The UI is
published on loopback only. [docs/DEPLOY.md](docs/DEPLOY.md) is the guide:
stopping any other host first, moving a ledger in, backups, the LAN.

---

## Configuration

`BacktestConfig` (`engine/core/config.py`) is the single source of truth,
built from YAML or a dict through one path and validated before anything
runs. Only `strategy` and `grid` are required. Three kinds of YAML live in
`config/` — sweeps, pinned champions and deployments; see
[config/CLAUDE.md](config/CLAUDE.md).

```yaml
strategy:
  strategy_id: hf_local_reference   # any id in strategies/strategy_registry.py
  strategy_params: {per_lot_pct: 0.0002, lookback_days: 0.02, bars_per_day: 387}
grid:
  steps: [0.00075]                  # each > 0 and < 1
  profit_targets: [0.3]
backtest: {symbol: TQQQ, initial_cash: 100000.0}
costs: {model_type: dynamic_slippage, base_bps: 0.5, vol_multiplier: 0.3}  # or zero / slippage_commission
risk: {max_concurrent_lots: 6000, max_total_exposure: null}
search: {strategy: grid, rank_by: Total Return %, direction: maximize, seed: 42}
execution:
  fill_model: intrabar              # or close
  intrabar_fill: causal             # or level / open_or_level
  intrabar_priority: sell_first
  on_flat_reentry: stale_reference  # or reset_to_market
  enforce_no_loss: true
  allow_signal_exit: false          # true only for strategies with a regime exit
  cash_yield_pct: null              # null = historical money-market rate
live:
  enabled: false
  broker: alpaca                    # or fidelity
  paper_trading: true
  step: 0.00075                     # the ONE parameter set the loop trades
  profit_target: 0.3
  feed: iex
```

`live.step` / `live.profit_target` are never defaulted from `grid.*`: the
grid lists are a search space, and letting sweep ordering pick what real
capital trades would be an accident. The loop refuses to start without them.

Rank by `Total Return %` or a drawdown-aware metric. The legacy default,
`Capital Velocity Index` (closed lots ÷ total lots), saturates at 1.0 on
long datasets and then ranks nothing.

---

## Architecture

```
web/  ──HTTP──>  server/  ──>  research/  ──>  engine/  <──  fidelity_gateway/
                                                  ^
                                          engine/core is layer 0
```

`engine/` never imports `research/`: strategies reach the engine only
through the `SizingStrategy` port (`engine/core/sizing.py`), and the
registry is the one module that knows the concrete set. Each directory has
its own guide — [engine](engine/CLAUDE.md), [research](research/CLAUDE.md),
[server](server/CLAUDE.md), [web](web/CLAUDE.md),
[fidelity_gateway](fidelity_gateway/CLAUDE.md), [tools](tools/README.md),
[tests](tests/CLAUDE.md).

**The decision cycle**, identical in backtest and live, every bar:

```
1. record_tick(context)     every bar, unconditionally
2. harvest eligible lots    sell before buy
3. grid trigger
4. calculate_trade_value()  only on a trigger
5. risk clamp
6. no-loss guard            exits only
```

A `MarketContext` is a frozen snapshot of one bar plus portfolio state, so
a strategy cannot alter its own inputs. All domain errors descend from
`TradingSystemError` (`ConfigurationError`, `DataValidationError`,
`StrategyError`, `RiskError`, `ExecutionError` → `NoLossViolation` /
`AmbiguousSubmissionError`, `ReconciliationError`, `PersistenceError`).

---

## Safety invariants

Enforced by structure and tests, not convention.

1. **Never sell at a loss.** `net_sell_proceeds ≥ allocated_cost_basis − 1e-8`,
   after costs, in one module. A target that becomes a loss after slippage
   is rejected before submission — so very thin targets never clear it.
   The sole exception is a strategy's `lots_to_liquidate` with
   `execution.allow_signal_exit` on.
2. **A halt never forces liquidation.** `CircuitBreaker`, `RuntimeLifecycle`
   and `Reconciler` have no liquidation method (asserted by test).
3. **Halts need a human.** `ACTIVE → HALTED_NEW_BUYS → MANUAL_RESET_REQUIRED`;
   a recovering drawdown does not auto-resume, the reset names an operator,
   and the halt survives restarts.
4. **Reconciliation never invents a transaction.** Auto-repair only applies
   a broker-confirmed fill to an order held under our own client order ID;
   everything ambiguous halts.
5. **Ambiguity is never retried.** A transport failure after submission is
   a distinct exception type routed to reconciliation by client order ID.
6. **Credentials never reach logs.** `LiveCredentials` redacts its own
   `repr`/`str`, audit payloads are redacted, and deployment artifacts
   reject secret-looking keys.

---

## Live trading and the promotion path

```
Backtest (SIMULATION)  →  Paper (PAPER)  →  Live (LIVE, needs a passing PromotionEvaluation)
```

Promotion criteria (`engine/promotion.py`), all machine-checked and recorded:
minimum paper duration (5 days), decisions (20) and fills (5); zero
accounting discrepancies, duplicate orders, no-loss violations, unresolved
reconciliations and unhandled exceptions. Every unmet criterion is
reported, and a gate configured to require nothing is itself rejected.

Credentials are environment-only: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`
(a paper key pair for staging, a live pair for production — `paper_trading`
selects the endpoint, it does not make a live key safe). The Fidelity route
is set up from `config/fidelity_live.yaml.example`.

```bash
.venv/bin/python cli.py live --config config/staging.yaml --check-only   # connect, reconcile, exit
.venv/bin/python cli.py live --config config/staging.yaml --max-ticks 20  # bounded first session
.venv/bin/python cli.py live --config config/staging.yaml                 # until SIGTERM/SIGINT
```

Startup walks `LOAD_CONFIG → LOAD_STATE → CONNECT_BROKER → RECONCILE →
VALIDATE_DATA_CLOCK → READY` and will not trade short of `READY`. Fills are
polled: submitting an order changes nothing until a later tick sees the
broker confirm it.

---

## Running it as services

Everything that stays up runs from `docker-compose.yml`
([docs/DEPLOY.md](docs/DEPLOY.md)):

| service | |
|---|---|
| `web` | the UI, its API and the backtest engine, on `127.0.0.1:8000` |
| `paper` | the champion grid on Alpaca paper (`config/paper_aggressive.yaml`) |
| `backup` | every ledger and the warehouse catalogs, daily, into `/workspace/backups` |
| `paper-ultimate` | profile `ultimate`: the Ultimate algorithm on its own paper account |
| `live` | profile `production`: real money, behind the promotion gate |

Each trading loop runs `tools/market_hours_supervisor.py`, which asks Alpaca
when the market opens and exits after the close, so holidays and DST need
no schedule; `restart: unless-stopped` brings everything back after a
reboot. Before a session's first tick the strategy is replayed the recent
sessions of bars its state spans (`engine/trading/live_history.py`) and
handed its durable book. `docker compose stop` lets the loop finish its
tick and settle what is in flight. The server has no authentication: read
[server/CLAUDE.md](server/CLAUDE.md) before publishing it beyond loopback
(`VAI_WEB_BIND`).

---

## Testing and code style

Each project directory carries its own `tests/`; the root `tests/` holds
only what spans two of them, plus `tests/e2e/` and shared fixtures.

```bash
.venv/bin/python cli.py test -q                 # everything
.venv/bin/python cli.py test -k promotion       # filtered, still across all sections
.venv/bin/python cli.py test engine/tests -q    # one section
.venv/bin/ruff format . && .venv/bin/ruff check --fix .
```

CI (`.github/workflows/ci.yml`) runs ruff and the suite on every push.
`research/tests/test_regression_baseline.py` pins a full sweep result value
for value — update it deliberately, never loosen it. Tests inject clocks
instead of sleeping, check the real `alpaca-py` enums, and drive the CLI
through subprocesses. Ruff uses `line-length = 100`; its exemptions are
explained in `pyproject.toml`.

---

## Extending the system

**A sizing strategy:** subclass `SizingStrategy`, register it in
`research/strategies/strategy_registry.py`, and give it a schema in
`param_schema.py`. Accumulate rolling state in `record_tick` (every bar),
not `calculate_trade_value` (triggers only — a sparse, biased sample).
Override `_grid_trigger_level` to change entry timing,
`adjust_profit_target` for per-lot targets, `lots_to_liquidate` for a regime
exit, and `warm_up(daily)` if it needs history before the first bar. A
strategy meant for live trading also answers `live_history_sessions()` (the
sessions of bars to replay before each session's first tick) and, if it
keeps per-lot state, `resume(open_lots)`.

**A cost model:** subclass `TransactionCostModel` and implement `apply_buy`
/ `apply_sell`, each returning `(effective_price, cost)`, without mutating
anything.

Result rows name their `Strategy`, so sweeps of different strategies can be
concatenated and compared directly.

---

## Troubleshooting

- **A backtest says there is no data for a ticker.** Ingest it
  (`tools/build_warehouse.py --ingest T`). The warehouse's views read
  relative paths, so a copied, moved or container-mounted warehouse reads
  in place; an older one with absolute paths is rewritten the first time it
  is opened (`tools/build_warehouse.py --init` does it by hand).
- **`DataValidationError`** — empty data, missing columns, NaN/inf,
  non-positive prices, or an unsorted/duplicated index; the message names
  the timestamps.
- **Every sell rejected, `Closed Trade Count` 0** — costs exceed the target.
  That is the no-loss guard working; raise the target or lower the costs.
- **`live` exits `RECOVERY_REQUIRED`** — startup could not continue; stderr
  names the stage (missing or rejected credentials, unreadable ledger).
- **`live` exits `RECONCILIATION_REQUIRED`** — local and broker state
  disagree. Deliberately not self-healing; the halt survives restarts.
- **The loop runs but never trades** — market closed, IEX returning no bar,
  or a regime strategy (`ultimate*`) that has no warm-up history yet.
- **Sweeps are slow** — `research/run_hf_sweep.py --n-jobs N`
  (~1.7 GB per worker at the heaviest settings), or random search.

---

## Project layout

```
volatility-ai/
├── cli.py                  # the single entrypoint (and Docker ENTRYPOINT)
├── engine/                 # trading kernel
├── research/               # strategies, sweeps, validation, ML
├── server/                 # FastAPI backend, queue, shards
├── web/                    # React UI
├── fidelity_gateway/       # Fidelity integration
├── fidelity-bridge-chrome-extension/   # git submodule
├── tools/                  # ops, data prep, probes; experiments/ holds past sweep runners
├── config/                 # sweep, champion and deployment YAMLs
├── tests/                  # cross-section tests, e2e, shared fixtures
├── docs/                   # setup, deployment, sweeps, research logs; history/ for finished plans
├── plan.md                 # the staged indicator sweep and its results
├── CHANGELOG.md            # why decisions were made
├── CLAUDE.md / AGENTS.md   # the map and rules for agents (AGENTS.md is a symlink)
├── Dockerfile, docker-compose.yml
└── pyproject.toml, requirements*.txt
```

Git-ignored but created by use: `.venv/`, `data/` (downloaded bars),
`warehouse/` (the DuckDB/Parquet lake), `output/` (results, run history,
queue), `logs/`, `state/`, `*.db` ledgers, and Fidelity capture artifacts.

---

## Known gaps

1. **`ACCEPTED → UNKNOWN` is not a permitted order transition.** An accepted
   order that loses contact stays `ACCEPTED`. Decide this before real capital.
2. **Alpaca fills are polled, not streamed** — recognised within one poll
   interval.
3. **`macro_surprise_factor` is inert** — defined on `MarketContext`, never
   populated or read; populate or remove it. The other macro fields are
   consumed by `HighFrequencyLocalReferenceSizing`.
4. **Ultimate live is paper-ready, not yet promotion-ready.** The live
   loop replays its history, refuses it without `allow_signal_exit` or with
   extended hours, and exits the calm book in one order. But the regime is
   computed on IEX ranges, not the SIP tape it was researched on; lots are
   sized from each session's starting equity rather than fixed starting
   capital; and `ultimate_rsp` / `ultimate_ursp` remain backtest-only.
5. **`research/run_hf_sweep.py` cannot run the `ultimate*` strategies as
   researched** — it never threads `allow_signal_exit` or cash yield. Use
   `run_sweep` or `cli.py backtest` with those set.
6. **Server-submitted runs are zero-cost** — `RunRequest` has no cost-model
   field, whatever the config says.

No license file is present. This is research software; leveraged ETFs can
lose most of their value, and backtested performance does not predict
results. Do not deploy real capital without completing the promotion path.
