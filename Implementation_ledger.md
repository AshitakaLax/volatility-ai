# Implementation ledger

State tracker for the web UI build. Updated at the end of every response.
Roadmap: `implementation_plan.md`.

---

## Current position

| | |
|---|---|
| **Active phase** | Phase 2 — Server, split by capability |
| **Active step** | 2.1 `server/live.py` (read-only router) |
| **Branch** | `main` |
| **Last full suite** | **2038 passed**, 1 skipped — regression baseline byte-identical |
| **Frontend** | `npx tsc -b` clean under strict mode; `npm run build` succeeds |

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

---

## Next actions

1. **2.1** — `server/live.py`: read-only router over `src/dashboard_data`. AST test that
   it imports no broker, session or order type.
2. **2.2** — `server/control.py`: the only write path, `POST /api/live/halt` →
   `CircuitBreaker`. AST test that it reaches nothing else.
3. **2.3** — `server/backtest.py` + `server/jobs.py`: bidirectional, validated through
   `BacktestConfig`, runs enqueued (~23s each, never inline).
4. **2.4** — `server/app.py`, CORS to the Vite dev origin only, bind `127.0.0.1`.
5. Add `fastapi`/`uvicorn` to a new `requirements-web.txt` (kept out of
   `requirements.txt` so the trading path gains no web dependency).

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

---

## Known gaps carried into this build

* **UPRO and SPY are not downloaded.** On hand: TQQQ, QQQ, RSP, SOXL, SQQQ, VIXY.
* **`tools/stage*_grid.py` outputs** are JSONL under `output/`, which is git-ignored —
  the UI reads them where present and must degrade cleanly where absent.
