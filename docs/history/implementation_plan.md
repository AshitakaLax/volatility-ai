# Web UI implementation plan

A React/TypeScript dashboard over `volatility-ai`, in two sections:
**backtesting and multi-fund analytics first**, live telemetry second.

Companion file: `Implementation_ledger.md` carries the live state — active
step, what is done, what is next, and every architectural decision taken.

---

## Decisions taken before any code

| | Decision | Consequence |
|---|---|---|
| Transport | **Mixed.** Live data strictly read-only; backtesting **bidirectional** — the UI submits parameters and runs sweeps. | Two routers with deliberately different powers (Phase 2). |
| Live controls | **Halt only.** Maps to the existing `CircuitBreaker`. | No `liquidate_all`, no parameter overrides. |
| Missing metrics | **Added to `src/performance_analyzer.py`.** | Engine, CLI and UI share one definition of Win Rate. |
| Streamlit | **Keep both.** | `dashboard.py` stays until the React live view reaches parity. |

### Why `liquidate_all` is absent

`src/live_trading_loop.py`: *"NO FORCED LIQUIDATION, EVER. There is no code path in
this module that sells a lot for any reason other than its profit target being met
and the no-loss guard permitting it."* There is no implementation to call, and adding
one means a forced-sell path that realises losses. Recorded here so the omission
reads as a decision, not an oversight.

---

## What is reused rather than rebuilt

| Asset | Role |
|---|---|
| `src/dashboard_data.py` | The entire live read layer. Opens SQLite `file:...?mode=ro` — the driver refuses writes. The server imports it verbatim. |
| `optimization_controller.run_sweep` | The backtest engine. `return_full_results=True` → `SimulationResult(metrics, trade_blotter, equity_curve, params)`. |
| `src/strategy_registry.resolve_strategy` | strategy_id → class. The single mapping. |
| `src/config.BacktestConfig` | Validates submitted parameters. The API does not grow a parallel schema. |
| `tools/export_strategy_curves.py` | Already emits normalised equity curves + drawdown + annual returns. |
| `src/risk_manager.CircuitBreaker` | The halt. Persisted, survives restart, operator-reversible. |

**One engine run costs ~23 seconds** on 10y of minute bars (measured). Too slow for a
synchronous request — backtests are jobs, never inline.

---

## Phase 0 — Tracking artifacts ✅

| File | Purpose |
|---|---|
| `implementation_plan.md` | This file. |
| `Implementation_ledger.md` | Live state, updated every response. |

---

## Phase 1 — Python foundation (gates everything visual)

The blotter cannot currently express the requested data contract. Four headline
features are impossible until it can, so this phase comes before any UI.

### 1.1 Blotter identity — `optimization_controller.py`

`blotter_records` records five fields: `timestamp, side, price, qty, equity`. No order
id, no lot linkage, no ticker, no realised profit. Add:

| Field | Source (already in scope) |
|---|---|
| `lot_id` | `order["id"]` on buys; `lot.order_id` on sells |
| `ticker` | `symbol` |
| `matched_buy_id` | sells: the closing lot's own id |
| `profit_realized` | sells: `net_sell_proceeds - lot.buy_price * filled_qty` |
| `sell_reason` | sells: `sell_reason` |
| `bar_index` | `context.bar_index`, for hold-duration |

Unlocks: buy/sell markers tied to a lot, closed-cycle connectors, active target lines,
and the Open/Stuck vs Closed filter.

### 1.2 Trade metrics — `src/performance_analyzer.py`

**Computed from the enriched blotter, not from `lot.target_sell_price`.** The existing
`calculate_metrics` assumes every closed lot sold at its target; that holds only while
signal exits are off, and computing Win Rate that way would return 100% by
construction, since a target is always above its basis.

New `trade_metrics(blotter)`: `Profit Factor`, `Win Rate %`, `Max Consecutive Losses`,
`Average Hold Duration`.
New `curve_metrics(equity_curve)`: `Sharpe`, `Sortino` — the existing function
correctly explains it has no time series; `SimulationResult.equity_curve` does.
Added to `calculate_metrics`: `Stuck Capital Value`, `Harvest to Stuck Ratio`.

### 1.3 ⚠️ Capital Velocity Index is already defined, and differently

`performance_analyzer.py` defines it as `closed_lots / total_lots`, flagged in its own
docstring as *"an original, reasoned interpretation, not a confirmed pre-existing
formula"*. The UI spec describes closed ÷ **stuck**.

**Keep the existing definition** — it is the default `rank_by` and ranks every sweep
result recorded in `README.md`. The requested ratio ships beside it as
`Harvest to Stuck Ratio`. Redefining it silently would retroactively change published
rankings.

### 1.4 `tools/export_ui_data.py`

Dump a `MultiFundBacktestReport` per run so the UI has real fixtures before the server
exists.

---

## Phase 2 — Server, split by capability

```
server/
  app.py       mounts both routers; CORS to the Vite dev origin only
  live.py      READ-ONLY. Imports src/dashboard_data and nothing else.
                 GET /api/live/stores | /state | /activity | /bars
                 WS  /ws/live        pushes on store revision change
  control.py   THE ONLY WRITE PATH. POST /api/live/halt -> CircuitBreaker
  backtest.py  BIDIRECTIONAL. Validates via BacktestConfig, enqueues jobs.
                 GET  /api/backtest/runs | /runs/{id} | /funds
                 POST /api/backtest/runs      -> 202 + run_id
                 WS   /ws/backtest/{run_id}   progress + result
  jobs.py      in-process job queue; runs never execute inline
```

Two invariants, each pinned by an AST-level test in the style of
`test_dashboard_data.py::test_no_broker_or_session_is_reachable_from_the_dashboard`:

* `live.py` imports no broker, no session, no order type, holds no writable connection.
* `control.py` reaches `CircuitBreaker` and nothing else.

---

## Phase 3 — Frontend scaffold

`web/` — Vite + React + TypeScript (strict), Tailwind, shadcn/ui, lucide-react.
`src/types/backtest.ts`, `src/types/telemetry.ts`, `src/hooks/useWebSocket.ts`
(auto-reconnect, heartbeat, retry counter), `src/hooks/useBacktestRun.ts`.

## Phase 4 — Section 1: Backtesting & multi-fund (priority)

`RiskRewardMetrics.tsx`, `BacktestChart.tsx` (lightweight-charts: candles, markers,
closed-cycle connectors, target lines), `FilterPanel.tsx`, `ParameterForm.tsx` (the
bidirectional half), `FundComparison.tsx` (normalised overlay, comparison table,
parameter-sweep heatmap).

**Data on hand:** TQQQ, QQQ, RSP, SOXL, SQQQ, VIXY. **UPRO and SPY are not
downloaded** — `cli.py fetch-data` before the comparison view can show them.

## Phase 5 — Section 2: Live telemetry

`LiveOrderLedger.tsx`, `DeploymentHealth.tsx`, `CommandCenter.tsx` (halt with a
confirmation modal; refused actions shown greyed **with the reason**, not hidden).
Then RSI plumbing — it is private to `src/sizing_indicators.py:_rsi()`, is not a
`MarketContext` field, and adding it touches four construction sites plus the Task 7.9
gate — and the RSI filter last.

---

## Verification

* `python cli.py test -q` green; **regression baseline byte-identical** — Phase 1 adds
  columns and metrics, so any movement in an existing number is a bug.
* New metrics tested against hand-computed fixtures, not against themselves.
* Server invariants: the two AST tests, plus a test that a config naming a live broker
  is rejected by `POST /api/backtest/runs`.
* End-to-end: `uvicorn server.app:app` + `npm run dev`; submit a TQQQ sweep from the
  UI, confirm markers and connectors match `output/` for the same run.
* Halt path: trigger from the UI, assert the breaker persists and `cli.py live` refuses
  new buys on next start.
* `ruff check`, `ruff format`, `python tools/check_syntax.py`.

## Risks

* **Two live views** while Streamlit and React coexist. Both read
  `src/dashboard_data.py`, so they cannot disagree about data — only presentation.
* **In-process job queue.** A server restart loses queued runs. Acceptable for a
  single-operator tool.
* **CORS and bind address.** The server exposes balances and positions. Binds
  `127.0.0.1` by default; `0.0.0.0` for the Pi is a separate, explicit decision.
