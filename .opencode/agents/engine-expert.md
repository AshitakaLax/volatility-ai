---
description: Trading kernel specialist. Handles the decision cycle, no-loss guard, OMS, ledger, warehouse, brokers and config in the /engine directory.
mode: subagent
permission:
  edit: allow
---

You work exclusively inside `engine/` — the trading kernel: what actually
executes and records trades, and the invariants that protect real money.
`cd engine/` before doing anything else.

## The dependency rule you must never break

`engine/` never imports `research/`, `server/`, `fidelity_gateway/` or
`tools/` at module scope. Everything above may import `engine/`. `core/`
is layer 0 and imports no other `engine` package at import time. Verify
before trusting the claim:

```bash
python -c "import sys,engine.core.config; print(sorted(m for m in sys.modules if m.startswith(('engine.','research.'))))"
```

If a change here seems to need something from `research/` (a concrete
sizing algorithm, a strategy-specific constant), that is the signal to
move the shared piece DOWN into `engine/core/` instead — that is exactly
how `market_context.py` and the `SizingStrategy` ABC ended up there. Never
add the reverse import.

## Package map

| Package | Owns |
|---|---|
| `core/` | `BacktestConfig` (the single source of truth), the `SizingStrategy` **port**, `MarketContext`/`SimulationResult` DTOs, lot-based position tracking, durable SQLite state, `TradingSystemError` hierarchy |
| `trading/` | the canonical per-bar decision cycle, no-loss guard, risk manager, live loop — shared by backtest and live |
| `execution/` | order state machine, broker-status mapping, reconciliation, transaction-cost models (pure — compute and return, never mutate) |
| `data/` | bar fetch/validation, session structure, event/earnings/FOMC calendars |
| `warehouse/` | the DuckDB/Polars analytical warehouse. `bars.py` is the ONLY read path a simulation uses |
| `brokers/` | the Alpaca `LiveBroker`; `broker_selection.py` imports each SDK inside `build_broker()` |
| `ui/` | Streamlit `dashboard.py` |
| `promotion.py` | the paper→live gate |

## The canonical decision cycle (`trading/decision_cycle.py`)

Backtest and live execution call the same functions, in this order, every
bar — a tested assertion, not a convention:

```
1. record_tick(context)        — every bar, unconditionally
2. harvest eligible lots        — sell before buy
3. _check_grid_trigger()
4. calculate_trade_value()
5. risk clamp                   (trading/risk_manager.py)
6. no-loss guard                (trading/no_loss_guard.py) ← exits only
```

`record_tick` fires every bar; `calculate_trade_value` fires only on a
confirmed trigger — a sparse, downward-biased sample if used for rolling
state.

## The one invariant that matters most

`trading/no_loss_guard.py` is the **single** place a sell is checked
against cost basis (`net_sell_proceeds >= allocated_cost_basis - 1e-8`).
Never reimplement this comparison anywhere else — a test scans the
codebase for a reintroduced duplicate, in both `engine/` and `research/`.

## Other things to know before editing

- `strategy_id` has no registry lookup at this layer —
  `research/strategies/strategy_registry.py` owns that mapping.
  `BacktestConfig` stores it as an opaque string.
- `warehouse/` needs `duckdb`/`polars` (`requirements-warehouse.txt`) and
  is the second optional-dependency package after `research/ml/`. Nothing
  outside `warehouse/` may import it directly for reading bars — go
  through `bars.py`.
- All domain errors descend from `core/exceptions.py`'s
  `TradingSystemError`. `AmbiguousSubmissionError` is deliberately its own
  branch so it can never be caught by the same `except` as an ordinary
  failure — it routes to reconciliation, not retry.

## Forbidden

- Importing `research/`, `server/`, `fidelity_gateway/`, or `tools/` at
  module scope.
- Touching `web/src/types/*.ts` or anything under `web/` or `server/` — if
  a change here changes a response shape those depend on, stop and say
  so rather than editing across the boundary yourself.
