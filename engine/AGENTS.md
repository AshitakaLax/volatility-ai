# engine/ — Trading Kernel

**Generated:** 2026-09-24T02:20:00Z — score 16 (>15, always create)

## OVERVIEW
The trading kernel: decision cycle, ledger, OMS, risk, warehouse, brokers. Knows nothing about concrete strategies.

## STRUCTURE
```
engine/
├── core/       # BacktestConfig (frozen), SizingStrategy port, MarketContext, Ledger, Persistence, Audit, Secrets
├── trading/    # decision_cycle (6-step), no_loss_guard, risk_manager, live_trading_loop, runtime_lifecycle
├── execution/  # order_lifecycle, order_management_system, reconciliation, cost_models, fill_accounting
├── data/       # historical_data, alpaca_market_data, tick_validation, calendars
├── warehouse/  # connection, schema, ingest, bars, queries — DuckDB/Polars lake
├── brokers/    # alpaca_broker (LiveBroker impl), broker_selection (deferred imports)
├── ui/         # dashboard.py (Streamlit)
├── promotion.py
└── tests/      # kernel-only suite
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Config schema | `core/config.py:441` | `BacktestConfig` frozen; `from_dict`/`from_yaml` same path |
| Strategy port | `core/sizing.py:35` | `SizingStrategy` ABC; `record_tick` vs `calculate_trade_value` |
| Decision cycle | `trading/decision_cycle.py` | 6 steps: record_tick → harvest → grid trigger → size → risk → no-loss |
| No-loss guard | `trading/no_loss_guard.py` | `net_proceeds >= cost_basis -1e-8`; sole sell gate |
| Ledger | `core/ledger.py` | Per-lot cost basis, partial closes |
| OMS | `execution/order_management_system.py` | Local state + broker mapping |
| Warehouse read | `warehouse/bars.py` | ONLY read path; `queries.py` lag-aware ASOF |
| Promotion gate | `promotion.py` | `Mode.LIVE` requires `PromotionEvaluation` |

## CONVENTIONS
- `core/` imports no other engine package at import time — verify via `python -c "import sys,engine.core.config; print(...)"`.
- Warehouse is second optional-dep package (`requirements-warehouse.txt`); seam is `result_sink: Protocol` (stdlib-only), satisfied structurally by `DuckDBResultSink`.
- Causal transforms: trailing window + shift; `warehouse/queries.py` shifts by `lag_days` before ASOF.
- Cost models are pure: `apply_buy`/`apply_sell` → `(price, cost)`, never mutate.

## ANTI-PATTERNS
- Never import `research/server/tools` — move shared thing to `core/`.
- Never reimplement no-loss comparison; never sell below basis intentionally.
- Never retain `SimulationResult` in a sink (OOM on 1k+ configs).
- Never `time.sleep` in tests; never fake `alpaca-py` enums.
