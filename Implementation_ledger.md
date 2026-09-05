# Implementation ledger

State tracker for the web UI build. Updated at the end of every response.
Roadmap: `implementation_plan.md`.

---

## Current position

| | |
|---|---|
| **Active phase** | Phase 5 — Section 2: Live telemetry |
| **Active step** | 5.1 `LiveOrderLedger.tsx` |
| **Branch** | `main` |
| **Last full suite** | **2079 passed**, 1 skipped — regression baseline byte-identical |
| **Frontend** | `tsc -b` clean, `vite build` succeeds, **19 vitest tests** pass |

---

## Completed

### Phase 0 — Tracking artifacts ✅ 2026-09-05

| File | Notes |
|---|---|
| `implementation_plan.md` | Roadmap: phases, steps, file deliverables, verification. |
| `Implementation_ledger.md` | This file. |

### Phase 1 — Python foundation ✅ 2026-09-05

| Step | File | Notes |
|---|---|---|
| 1.1 | `optimization_controller.py` | Blotter gains `lot_id`, `ticker`, `bar_index` on both sides; `sell_reason` + `profit_realized` on sells. Verified: **10 of 10 sold lots join buy↔sell**. |
| 1.2 | `src/performance_analyzer.py` | `trade_metrics()` (Profit Factor, Win Rate %, Max Consecutive Losses, Average Hold Duration) and `curve_metrics()` (Sharpe, Sortino). `Stuck Capital Value` + `Harvest to Stuck Ratio` in `calculate_metrics`. |
| 1.2 | `optimization_controller.py` | Both folded into the metrics dict at the end of `_simulate_single`, where the blotter and equity curve exist. |
| 1.3 | `tests/fixtures/regression_baseline.py` | Eight new columns. **Every existing value re-derived and compared first; none moved.** |
| 1.3 | `tests/unit/test_ui_metrics.py` | 16 tests, expectations hand-computed in comments. |
| 1.4 | `tools/export_ui_data.py` | Emits the wire contract. Verified against a real TQQQ run. |
| 1.5 | `optimization_controller.py` | `rsi` on every blotter row, from the existing `WilderRSI` — the last missing contract field. **Not** added to `MarketContext`: see D7. |

### Frontend Phase 1 — Environment & shared types ✅ 2026-09-05

(The user's own numbering. This is Phase 3 in `implementation_plan.md`; pulled
forward because the Python contract is now complete.)

| File | Notes |
|---|---|
| `web/package.json` | React 19, Vite 6, Tailwind **v4**, lightweight-charts, lucide-react. |
| `web/vite.config.ts` | `@/*` alias (a shadcn prerequisite), `/api` + `/ws` proxy to `127.0.0.1:8000`, dev server bound to `127.0.0.1`. |
| `web/tsconfig.app.json` | Strict, plus `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `noUnusedLocals/Parameters`. |
| `web/components.json` | shadcn/ui config (new-york, slate, CSS variables). |
| `web/src/index.css` | Tailwind v4 theme in CSS — no `tailwind.config.js` by design. shadcn tokens plus **semantic** `--profit` / `--loss` / `--stuck`, separate from the accent. |
| `web/src/lib/utils.ts` | `cn()` (shadcn prerequisite) + `pct` / `usd` / `count`. |
| `web/src/types/backtest.ts` | `BacktestExecution`, `FundPerformanceMetrics`, `MultiFundBacktestReport`, filter and run-state types. |
| `web/src/types/telemetry.ts` | `InventoryLot`, `DeploymentState`, `ConnectionHealth`, `COMMANDS`. |
| `web/src/App.tsx` | Shell that fetches the real exported report and renders metric cards. |

### Phase 2 — Server, split by capability ✅ 2026-09-05

| File | Notes |
|---|---|
| `server/live.py` | Read-only. `/stores`, `/state`, `/activity`, `/bars`, `WS /ws`. Reads only through `src/dashboard_data` (`mode=ro`). |
| `server/control.py` | The only write. `POST /api/live/halt` → `CircuitBreaker`, read back through the read-only path so the write is verified, not assumed. |
| `server/backtest.py` | `/funds`, `/runs`, `POST /runs` (202), `WS /ws/{run_id}`. Validated via `BacktestConfig`; serialised by the exporter's own helpers. |
| `server/jobs.py` | One worker thread, Condition-based waits. No persistence — see the known gaps. |
| `server/app.py` | Mounts all three, loopback bind, explicit CORS origins, `/api/health` reporting capabilities. |
| `requirements-web.txt` | Separate from `requirements.txt` on purpose. |
| `tests/unit/test_server_capability.py` | 22 AST tests. Verified against deliberate violations. |
| `tests/integration/test_server_api.py` | 19 tests against a real store and a real engine run. |

### Phase 4 — Section 1: Backtesting & multi-fund ✅ 2026-09-05

| File | Notes |
|---|---|
| `web/src/lib/api.ts` | Typed client; surfaces FastAPI's `detail` rather than a bare status. |
| `web/src/lib/filters.ts` | Cycle matching, filtering, OHLC aggregation. The only deciding code in the frontend. |
| `web/src/lib/filters.test.ts` | 19 tests, verified against three deliberate bugs. |
| `web/src/hooks/useWebSocket.ts` | Reconnect with capped, jittered backoff; health reported. |
| `web/src/hooks/useBacktestRun.ts` | Submit + follow to completion. |
| `web/src/components/ui/primitives.tsx` | Card/Button/Input/Select/Badge/Field. |
| `.../RiskRewardMetrics.tsx` | Traditional metrics separated from grid behaviour. |
| `.../BacktestChart.tsx` | Candles, markers, **cycle connectors** on a canvas overlay, target lines from the run's own profit target. |
| `.../FilterPanel.tsx` | Timeframe, date range + presets, lot status, RSI bounds, fund. |
| `.../ParameterForm.tsx` | The bidirectional half. Percent → fraction on submit. |
| `.../FundComparison.tsx` | Normalised overlay + side-by-side table. |
| `web/vite.config.ts` | `ws: true` moved onto `/api` — the sockets live under it. |

---

## Next actions

1. **5.1** — `LiveOrderLedger.tsx`: lots, distance to target, distance to next step,
   over `GET /api/live/state` + `WS /api/live/ws`.
2. **5.2** — `DeploymentHealth.tsx`: git commit/branch, container health, account
   switcher over `/api/live/stores`.
3. **5.3** — `CommandCenter.tsx`: halt with a confirmation modal; `liquidate_all` and
   `parameter_override` greyed **with their reasons**, read from `/api/health`.
4. **5.4** — the parameter-sweep heatmap, which needs a multi-configuration run the
   API does not yet expose (it returns the best row per fund).
5. **Deferred:** a date-range filter that reaches the ENGINE rather than the view —
   currently `limit` caps bars from the end of the file, not an arbitrary window.

---

## Architectural decisions

**D1 — Transport is split by capability, not uniform.**
Live data read-only (`mode=ro`, driver-enforced); backtesting bidirectional. Came from
the user directly: *"for live orders it should be read only, but the ability to change
settings and inputs can be bidirectional especially for back testing."* Implemented as
two FastAPI routers with different import surfaces, each pinned by an AST test.

**D2 — Halt is the only write to live state.**
`emergency_halt` → `CircuitBreaker.halt_for_reconciliation()`, which already persists,
survives restart and is operator-reversible. `liquidate_all` is refused: no
implementation exists, and `live_trading_loop.py` states *"NO FORCED LIQUIDATION,
EVER."* The UI shows it greyed **with the reason** rather than hiding it.

**D3 — Trade metrics come from the blotter, not from `lot.target_sell_price`.**
Found while reading `src/ledger.py`: the backtest path calls `close_lot(lot)` with no
`execution_price`, so `last_execution_price` stays `None`, and
`calculate_metrics`'s realised PnL assumes every closed lot sold *at its target*. A
target is always above its basis, so a Win Rate computed that way would be **100% by
construction**. The new metrics read actual fills from the enriched blotter. This is
why 1.1 must land before 1.2.

**D4 — `Capital Velocity Index` keeps its existing definition.**
It is `closed_lots / total_lots` today, flagged in its own docstring as an unconfirmed
original interpretation. The UI spec describes closed ÷ *stuck*. Redefining it would
retroactively change every ranking in `README.md`, since it is the default `rank_by`.
The requested ratio ships beside it as `Harvest to Stuck Ratio`.

**D5 — Backtests are jobs, never inline.**
One engine run measured at ~23 seconds on 10y of minute bars. A synchronous POST would
time out. `POST /api/backtest/runs` returns 202 + `run_id`; progress arrives on
`/ws/backtest/{run_id}`.

**D11 — Candles are synthesised from executions, not fetched.**
`/api/live/bars` serves recent minute data for LIVE charting. A historical run may
span ten years, and pulling a million rows into a browser to draw 40 markers is the
wrong trade. Each execution contributes its own price point, so the line the markers
sit on is exactly the prices they executed at. A future chart wanting true OHLC needs
a bar endpoint that takes a date range.

**D12 — Connectors are canvas, not series.**
lightweight-charts has no segment primitive and one `LineSeries` per cycle would mean
thousands of series. An overlay canvas positioned with `timeToCoordinate` /
`priceToCoordinate` costs one canvas regardless. Capped at 400 and the cap is
reported in the header rather than applied silently.

**D9 — The FastAPI pin is load-bearing for Streamlit.**
`fastapi==0.115.6` caps `starlette<0.42`. Installing it downgraded starlette and broke
streamlit 1.58, which imports `DEFAULT_EXCLUDED_CONTENT_TYPES` from
`starlette.middleware.gzip` — `dashboard.py` stopped importing and took
`test_dashboard_data.py` with it. D-keep-both means a pin that disables one dashboard
is not acceptable. Now `fastapi==0.141.1`; re-check `import streamlit` after any
change to either pin.

**D10 — The halt reads its result back rather than echoing the request.**
An endpoint that reports success from its own inputs cannot tell you it silently did
nothing. `POST /api/live/halt` writes through `CircuitBreaker`, then returns what
`load_state` (read-only, separate connection) actually sees.

**D7 — RSI goes on the BLOTTER, not on `MarketContext`.**
`rsi_at_entry` is a reporting column the UI filters by. Putting RSI on
`MarketContext` would instead expose it to every *strategy* — a behaviour change
gated by `test_task_7_9_macro_signals_discovery`, needing the four-part discovery
block and all four construction sites. A blotter column needs none of that. It reuses
`WilderRSI`, the same class `RsiMomentumSizing` trades on, so the filter cannot
describe a different indicator than the chart it filters. Unseeded bars are **NaN,
not 0.0** — a zero would filter as extremely oversold and drag every early trade into
an RSI<30 query.

**D8 — Tailwind v4, no `tailwind.config.js`.**
v4 takes its theme from CSS. Semantic colours (`--profit`, `--loss`, `--stuck`) are
defined separately from the accent, because a grid book's harvested/stuck distinction
has to read at a glance in a table of hundreds of rows.

**D6 — `realized_pnl` in `calculate_metrics` is left as-is, and documented.**
It is only correct while signal exits are off, which is the default and the regression
baseline's configuration. Changing it would move a pinned number. The new metrics are
correct independently; the divergence is noted at the call site rather than silently
carried.

---

## Blockers

*None.*

## Verified this session

* `python cli.py test -q` → **2032 passed, 1 skipped**.
* `tests/test_regression_baseline.py` passes with eight added columns and **zero moved
  values** — checked by re-deriving every pinned figure before extending the fixture.
* `tools/export_ui_data.py --tickers TQQQ RSP --limit 40000` produces a complete report:
  21 closed cycles, every sell carrying `matched_buy_id` and `profit_realized`, equity
  curve normalised to 100.0 at its first point.
* RSP returned **0 executions** at `config/staging.yaml`'s 0.5% step over 40k bars. Not
  a bug — a low-volatility fund on a grid tuned for a 3x one. The UI must render "no
  executions" rather than an empty chart, which `executions()` already supports.
* **41 of 42 executions carry `rsi_at_entry`** (one falls inside the 14-bar warmup),
  and an RSI<30 filter over the export finds **14 real oversold entries**.
* `npx tsc -b --noEmit` clean under strict mode; `npm run build` emits 220 kB JS /
  11 kB CSS; the dev server serves the app and the real report.
* **Server, end to end against a running uvicorn and the real `paper_ledger.db`:** the
  live socket delivered state at revision 922 (1 open lot, halted) then heartbeats; a
  submitted run returned **202**, completed in **4s** over its own socket, and came back
  with 32 executions and **16 of 16 sells carrying `matched_buy_id`**.
* **Phase 4 through the Vite proxy** (the path a browser actually takes): a two-fund run
  submitted, watched to completion over the ws proxy, returning 50 TQQQ executions with
  **25 of 25 cycles linked**, 6 RSP executions with 3 of 3, RSI on every row, and both
  curves normalised to 100.0.
* The frontend tests were checked against three deliberate bugs — unknown RSI treated as
  in-range, an exclusive end date, aggregation by sampling — and each failed its own test.
* The capability tests were checked against deliberate violations — a broker import in
  `live.py`, a `LedgerStore` in `live.py`, a second route in `control.py`, a wildcard
  CORS origin — and each failed its own guard.

---

## Known gaps carried into this build

* **The job queue is in-process and unpersisted.** A server restart loses queued and
  running runs. Acceptable for a single-operator tool; a real task queue is a
  dependency and an operational surface this project does not need.
* **No authentication on the API.** Acceptable only because it binds `127.0.0.1`.
  Binding it to a LAN would need auth first — it serves balances and positions.

* **UPRO and SPY are not downloaded.** On hand: TQQQ, QQQ, RSP, SOXL, SQQQ, VIXY.
* **`tools/stage*_grid.py` outputs** are JSONL under `output/`, which is git-ignored —
  the UI reads them where present and must degrade cleanly where absent.
