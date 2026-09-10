# src/

The library. Subpackages, one line each (see each file's own docstring
for the "why" — this codebase writes unusually thorough ones, read them
before assuming behavior):

| Package | Key modules | Owns |
|---|---|---|
| `core/` | `config.py`, `ledger.py`, `persistence.py`, `audit.py`, `secrets.py`, `exceptions.py`, `idempotency.py` | `BacktestConfig` (the single source of truth, validated front-loaded), lot-based position tracking, durable SQLite state, the `TradingSystemError` hierarchy |
| `trading/` | `decision_cycle.py`, `no_loss_guard.py`, `risk_manager.py`, `live_trading_loop.py`, `runtime_lifecycle.py`, `strategy_registry.py` | the canonical per-bar decision sequence, **shared by backtest and live** — see below |
| `execution/` | `order_lifecycle.py`, `order_management_system.py`, `reconciliation.py`, `fill_accounting.py`, `live_execution.py` | order state machine, broker-status mapping, local-vs-broker reconciliation |
| `strategies/` | `size_calculators.py`, `high_frequency_sizing.py`, `bayesian_sizing_calculators.py`, `market_context.py`, `indicator_library.py` | `SizingStrategy` implementations and the immutable `MarketContext` snapshot they read |
| `data/` | `historical_data.py`, `alpaca_market_data.py`, `data_validation.py`, `tick_validation.py`, `*_calendar.py` | bar fetch/validation (backtest CSVs and live polling), event/earnings/FOMC calendars |
| `analysis/` | `cost_models.py`, `performance_analyzer.py`, `validation.py`, `analyze_annual.py` | transaction cost models (pure — compute and return, never mutate), result metrics, annualized vs. buy-and-hold |
| `optimization/` | `optimization_controller.py`, `search_strategies.py`, `walk_forward.py`, `monte_carlo.py` | sweep orchestration (`_simulate_single` runs one combo), grid/Bayesian/random search, out-of-sample validation |
| `brokers/` | `alpaca_broker.py`, `fidelity_broker.py`, `fidelity_capture.py`, `broker_selection.py` | `LiveBroker` implementations |
| `ml/` | `features.py`, `labels.py`, `rolling.py`, `live_features.py`, `reachability_sizing.py`, `sources.py` | the reachability-sizing research line — see caveat below |
| `warehouse/` | `connection.py`, `schema.py`, `hashing.py`, `ingest.py`, `duckdb_sink.py`, `queries.py` | the DuckDB/Polars analytical warehouse: bars, sweep results, macro series, `ASOF` joins — see caveat below |
| `ui/` | `dashboard.py` | Streamlit view of a running deployment |
| `scripts/` | `run_hf_sweep.py`, `fidelity_recon.py`, `fidelity_place_test_order.py` | entry points too specific to live at repo root |

## The canonical decision cycle (`trading/decision_cycle.py`)

Backtest and live execution call **the same functions**, in this order,
every bar — not a convention, a tested assertion:

```
1. record_tick(context)        — every bar, unconditionally
2. harvest eligible lots        — sell before buy
3. _check_grid_trigger()
4. calculate_trade_value()
5. risk clamp                   (trading/risk_manager.py)
6. no-loss guard                (trading/no_loss_guard.py) ← exits only
```

Steps 1 and 3 are deliberately separate: `record_tick` fires at the top of
the bar, the grid trigger is evaluated only *after* that bar's harvest
sells. A stateful `SizingStrategy` accumulates rolling state in
`record_tick` (fires every bar) and must not rely on `calculate_trade_value`
for that (fires only on a confirmed trigger — a sparse, downward-biased
sample if used for state).

## No-loss guard

`trading/no_loss_guard.py` is the **only** place a sell is checked against
cost basis (`net_sell_proceeds >= allocated_cost_basis - 1e-8`). Two
independent inline copies existed once and had begun to drift; they were
folded into this one, and a test scans for any reintroduced duplicate.
Never reimplement this comparison elsewhere.

## `strategy_id` has no registry lookup at the config layer

`trading/strategy_registry.py` maps `strategy_id` → `SizingStrategy`
class; `BacktestConfig` itself does not resolve one. When adding a
strategy, register it there, not by hand-wiring `STRATEGY_REGISTRY` in a
script.

## `src/ml/` is research, not a trading input — by default

`ml/reachability_sizing.py` changes only *how much* a confirmed grid buy
is worth (confidence can shrink size toward zero, never grow past
`max_trade_pct`); it cannot decide whether to buy, move a profit target,
or sell. It is wired into the backtest engine as a real, selectable
strategy (see `strategy_registry.py`), but nothing defaults to it and no
live config enables it without deliberately setting `strategy_id`. The
rest of `ml/` (`features.py`, `labels.py`, `sources.py`) feeds
`tools/build_ml_dataset.py` and `server/ml_insights.py`'s read-only UI
tab, not the trading path.

**Causal-transform rule, everywhere in `ml/`:** every rolling statistic is
computed on a trailing window and then shifted, so the value at bar D
uses only bars < D. This is the easiest way to leak the future into a
backtest and it fails silently — don't add a feature that violates it.
`ml/rolling.py`'s `IncrementalBarFeatures` exists specifically because a
`SizingStrategy` sees the run bar-by-bar with no "whole DataFrame" hook —
it must agree with `features.py`'s offline computation by construction,
not by two implementations kept in sync by hand.

## `src/warehouse/` is the second optional-dependency package

`requirements.txt`'s rule is that the live loop and the Raspberry Pi must
never need an optional dependency to start, and that only `src/ml/` may
import one. `warehouse/` is the **second** exemption: it needs `duckdb`
and `polars` from `requirements-warehouse.txt`, and nothing in `src/`
outside it may import it.

The seam that keeps that true is `optimization/result_sink.py` — a
stdlib-only `Protocol`. `run_sweep` gained one keyword, `result_sink=None`,
and calls it in the parent process in both the sequential and parallel
branches. With no sink the behavior is byte-for-byte what it was, and
neither optional dependency is imported. `DuckDBResultSink` satisfies the
Protocol **structurally** — it never imports it — so the dependency arrow
only ever points one way.

Two rules a sink implementation must honor, both learned from real
incidents recorded in `optimization_controller.py`: it must not raise
(a storage fault must not destroy a multi-hour sweep), and it must not
retain the `SimulationResult` it is handed (retaining them is what
exhausted RAM on a 1,260-combination run). The blotter itself is built
unconditionally by `_simulate_single` because `trade_metrics` needs it,
so writing it out costs no extra memory — only holding it does.

`parameter_hash` builds on `core/artifacts.py`'s `canonical_hash` rather
than adding a third hashing scheme. Its `UNIQUE` constraint is the dedup
mechanism, so `dataset_version` and `broker_id` are inside the hash:
the same parameters against different data, or a different cost model,
are different experiments and must not collide.

The `external` lake (FRED/CBOE/Yahoo macro series from `data/external/`,
manifest-driven) carries a per-series `lag_days`. The lag-aware query in
`queries.py` shifts every observation forward by it before the `ASOF`
match, so a backtest bar only ever joins a macro value that had actually
been *published* by then — joining on the raw observation timestamp
leaks a print weeks early, the same silent lookahead `ml/`'s
causal-transform rule guards against.

## Exception hierarchy

All domain errors descend from `core/exceptions.py`'s `TradingSystemError`:
`ConfigurationError`, `DataValidationError`, `StrategyError`, `RiskError`,
`ExecutionError` (→ `NoLossViolation`, `AmbiguousSubmissionError`),
`ReconciliationError`, `PersistenceError`. `AmbiguousSubmissionError` is
deliberately a distinct type so it can never be caught by the same
`except` as an ordinary failure and routes to reconciliation, not retry.
