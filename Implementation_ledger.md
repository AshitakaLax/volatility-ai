# Implementation ledger

State tracker for the web UI build. Updated at the end of every response.
Roadmap: `implementation_plan.md`.

---

## Current position

| | |
|---|---|
| **Active phase** | All planned phases complete |
| **Active step** | — every planned item and three of five deferrals are built |
| **Branch** | `main` |
| **Last full suite** | **2106 passed**, 1 skipped — regression baseline byte-identical |
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

### Phase 5 — Section 2: Live telemetry ✅ 2026-09-05

| File | Notes |
|---|---|
| `server/deployment.py` | `GET /api/deployment` — git identity, uptime, cgroup memory. The only server module that runs a subprocess, and the capability test now says so. |
| `web/src/hooks/useLiveState.ts` | Fetch once + subscribe. Read-only by construction. |
| `.../live/DeploymentHealth.tsx` | Build, account switcher, connection health, and the staleness stated rather than implied. |
| `.../live/LiveOrderLedger.tsx` | Un-merged lots sorted by distance to target; null distance sorts last. |
| `.../live/CommandCenter.tsx` | Halt with confirmation + required reason; the two refused commands rendered greyed **with their reasons**. |

### Deferred items closed ✅ 2026-09-05

| Item | Notes |
|---|---|
| Real OHLC candles | `GET /api/backtest/bars` — date range, server-side OHLC downsample. Measured: 5,850 rows → 390 candles at 900s, all with low ≤ open,close ≤ high. |
| Engine-level date range | `RunRequest.start`/`.end`, applied **before** the bar cap. |
| Parameter sweep matrix | `configurations[]` per fund + `SweepMatrix.tsx` heatmap. |
| Event-loop stall (found while testing) | The backtest WS blocked on a `threading.Condition` for up to 10s from a coroutine. Now `asyncio.to_thread`: an unrelated request measured **23 ms** where it could have waited 10,000. |

### Live parameters, live RSI, and clickable sweep cells ✅ 2026-09-05

| Item | Notes |
|---|---|
| `src/live_trading_loop.py` | Persists `live.parameters` (symbol, step, profit_target, strategy_id, paper, poll interval) through every tick. |
| `src/dashboard_data.py` | Reads it; malformed JSON reports absent rather than raising. |
| `server/live.py` | `parameters` on `/state`; new `GET /api/live/indicators` computing RSI with `WilderRSI`. |
| `.../live/AlgorithmStatus.tsx` | Price, RSI, step, target, allocation — and flags an implausible target rather than only displaying it. |
| `.../backtest/SweepMatrix.tsx` | Cells stage their parameters in the run form, closing the brief's grid-step / sizing-model filter. |

### Parallel sweeps ✅ 2026-09-05

`server/backtest.py` gains `choose_jobs`, and `jobs.py`'s reasoning is corrected: the
trading loop runs on separate hardware, so a pool cannot starve it.

| bars × configs | serial | pooled (11 workers) |
|---|---|---|
| 13,260 × 12 | 4.2s | **0.69x — slower** |
| 100,000 × 6 | 8.2s | 1.35x |
| 300,000 × 6 | 19.8s | 2.25x |

Through uvicorn: 6 × 300k completed in **8.0s, 2.46x**, results identical at every
worker count.

---

## Next actions

Everything planned is built, and three of the five deferrals are now closed. Two
remain, both still deliberate:

1. **Clearing a halt from the UI.** Setting one is reversible by an operator outside
   the dashboard; adding the inverse is a SECOND write and would need its own
   justification against the one-write invariant that `control.py` is built on.
2. **Retiring `dashboard.py`.** The decision was to keep both until the React live
   view reaches parity. It now covers lots, halt state, deployment identity and the
   command centre; Streamlit still has the price ladder.

Worth doing next if the UI continues:

3. **The job queue still loses work on restart** (D5). A cheap middle ground that does
   not contradict D5: persist COMPLETED reports to disk so a finished run survives,
   while queued and running jobs stay disposable.
4. **Live RSI reads a data FILE**, which can lag the loop's own feed — stated on the
   card. Closing that gap means the loop persisting its own indicator readings, which is
   a change to the trading path for a number a reader can already derive.
5. **The parallel threshold is measured on ONE machine.** 500k bar-configurations is
   right for 12 cores under Windows spawn; a Linux host that forks would break even far
   lower. `n_jobs` is explicit-overridable for exactly that reason.

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

**D19 — Sweeps parallelise above a MEASURED threshold, not by default.**
The user corrected the premise `jobs.py` was written on: the trading loop is on
separate hardware, so a pool cannot starve it. But measuring first showed a blanket
default would have made the common case slower — 0.69x on a small interactive run,
because Windows spawns a fresh interpreter per worker and pickles the frame per task.
`choose_jobs` encodes the three measurements: serial below ~500k bar-configurations,
pooled above, never more workers than combinations, explicit `n_jobs` always honoured.
The report states what was USED, not what was requested.

**D17 — The loop records its own parameters.**
The store held what the loop DID and never what it was TOLD to do, so a 30% profit
target where 0.3% was meant was invisible without diffing a config against a ledger —
and it stranded 94 lots before anyone did. Written every tick with the other scalars,
so a restart under a changed config cannot leave the store describing the previous one.
Absent (an older store) renders as unknown, never as zeros.

**D18 — Live RSI reuses `WilderRSI`, computed server-side.**
The same class `RsiMomentumSizing` trades on and the backtest blotter records. A second
implementation on the dashboard would be free to disagree with the one making
decisions. Computed from bars rather than persisted, because adding a field to the
trading path for a number a reader can derive is the wrong trade.

**D15 — Two bar endpoints, deliberately.**
`/api/live/bars` serves the TAIL of a file for a running deployment and takes no date
range; `/api/backtest/bars` takes a range and is useless for live. Merging them would
mean one endpoint whose behaviour depends on which arguments were passed. This
supersedes D11 for the backtest chart — candles are now real OHLC, not synthesised
from executions.

**D16 — The window is applied before the bar cap.**
Capping first takes the tail of the FILE and then filters it, so any non-recent window
returns empty — on screen indistinguishable from "the strategy made no trades in that
period". Pinned by `test_the_window_is_applied_before_the_bar_cap`.

**D13 — Refused commands are rendered, not hidden.**
`liquidate_all` and `parameter_override` appear greyed with the sentence that
explains each. A control a reader expects and cannot find reads as a bug; one that
explains itself reads as a decision. Capabilities come from `/api/health` rather than
a constant in the bundle, which could disagree with the deployment it is talking to.

**D14 — Container stats are cgroup or null, and CPU is never reported.**
psutil is not a dependency and a status card does not justify one. More importantly a
"CPU 0%" meaning "could not measure" is a number someone would act on. cgroup exposes
cumulative microseconds; a percentage needs two samples over a known interval this
endpoint does not keep, so it is absent rather than approximated. `git_dirty` is null
rather than false when git cannot be reached, for the same reason.

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
* **Parallelism, through uvicorn rather than a script** — Windows spawn re-imports
  `__main__`, which under the server is uvicorn's runner, and that is exactly where it
  could have failed. 6 configurations × 300k bars: **8.0s against a 19.8s serial
  baseline (2.46x)**, results identical at every worker count. A first benchmark died
  with `BrokenProcessPool` — an artifact of running from stdin, not the bug it looked
  like, which is why the uvicorn check exists rather than a conclusion.
* **Live parameters and RSI, against a running server:** `GET /api/live/indicators`
  returned RSI **56.95** from 390 bars, matching `WilderRSI` driven directly over the
  same file; the real `paper_ledger.db` correctly reported `{}` for parameters, since it
  was written before the loop recorded them.
* **Deferred items, against a running server:** a 2×3 sweep windowed to 2026-03-02..20
  completed in 4.1s over 5,850 bars and returned all six cells, with `cells[0]` equal to
  the headline metrics; bars downsampled 5,850 → 390 with every candle well-formed; and
  an unrelated request during a backtest socket's heartbeat wait took **23 ms**.
* Two environment traps cost time and are recorded so they are recognised faster: a
  10-minute "hang" was a server that never started (`nohup` inherited `web/` as its cwd,
  so `server` was not importable), and a 404 on a new endpoint was a stale uvicorn plus
  two Vite instances on overlapping ports — not the routing bug it first looked like.
* **Phase 5 against the real paper store**, through the proxy: deployment reported
  `main@b9f50c7`, the store came back **halted** with "reconciliation required", and
  the ledger showed one adopted TQQQ lot at 72.3127 against a 94.0065 target — **30.52%
  away**, the stranded lot from the 30% profit-target bug found earlier this session.
  Surfaced as one row, with no log grepping.
* A `/api/deployment` 404 was first misdiagnosed as `include_router` not taking effect.
  It was registered; the debug filter read `.path` off router groups where it is not a
  plain string. Real cause: a stale uvicorn predating the module, plus a second Vite
  holding 5173 while a third reported 5175.
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

---

## Phase ML-0 — Training environment and public data ingestion (2026-09-06) — COMPLETE

**Delivered:** `src/ml/{__init__,sources,features,labels}.py`,
`tools/{fetch_market_inputs,build_ml_dataset,evaluate_ml_features}.py`,
`tests/unit/test_ml_labels.py` (36 tests), `requirements-ml.txt`.
Corrected a stale claim in `src/high_frequency_sizing.py`.

**118 public series ingested, 0 failures** — 56 FRED, 10 CBOE, 54 Yahoo (`data/external/`,
gitignored). No API keys. Datasets built for RSP / COWZ / SPYD: 95 features, 48 labels.

`python -m pytest tests/unit -q` -> **1857 passed, 1 skipped**. ruff clean.

### Decisions worth keeping

* **Publication lag is baked into the timestamps, not left to the caller.** Each source
  declares how late its number really is and is stamped at the moment it could first have
  been read, so `ExternalIndexSeries.scalar()` makes the as-of join safe by construction.
  Reused the dormant `ExternalIndexSeries` rather than writing a second join layer.
* **One request per FRED series.** The multi-id form returns a malformed body past a few
  ids and resets the connection at 29. Not worth working around for a few seconds.
* **Failures are recorded, not raised.** ~113 endpoints; some are retired or rate-limited
  on any given day. This caught four CBOE indices shipping close-only (`DATE,VVIX`)
  instead of OHLC on the first run.
* **Moody's over ICE BofA for credit.** FRED caps the BAML series at a rolling 3 years
  keyless (~28% coverage of the training window); `BAA10Y`/`AAA10Y` reach 1986.
* **Labels pinned to a brute-force reference.** This caught a real bug: the sparse table's
  top level spans `2**ceil(log2(h))`, so MFE for a 17-bar horizon was measured over 32
  bars. Also moved the table to float64 — float32 shifted MFE by ~1e-8, harmless alone,
  but `reached` compares against a float64 target and a limit order resting exactly ON
  its target is the ordinary case. Rounding there flips a label rather than perturbing it.
* **Paired per-fold comparison, not two means.** Fold-to-fold variance (~0.03) exceeds any
  lift being looked for; unpaired cannot resolve the question.
* **Multi-seed shuffled control.** Single-seed five-fold controls ranged 0.480–0.542 and
  read as leaks when nothing was wrong. Fifty fits: 0.5011 ± 0.0047.

### Result, stated so it can be wrong

Macro adds a consistent lift on **COWZ only** (+0.046 AUC, 5/5 folds) at `h390`;
RSP and SPYD indistinguishable, and all three indistinguishable at `h1950`. That is one
hit in six comparisons — about what chance yields. Recorded in `ml_plan.md` as a
**candidate to pre-register**, not a finding. AUC is not P&L.

### Carried gaps

* Nothing is wired into `SizingStrategy`. No model touches the engine.
* The COWZ result is un-replicated and on the shortest history of the three.
* `data/external/` is gitignored, so a fresh clone must re-run the fetch (~40s).

---

## Phase ML-1 — UI hookup, read-only (2026-09-07) — COMPLETE

**Delivered:** `server/ml_insights.py`, `server/ml_upstream.py`,
`tools/ablate_ml_features.py`, `web/src/components/ml/ModelInsights.tsx`,
`web/src/types/ml.ts`; extended `server/app.py`, `web/src/App.tsx`,
`web/src/lib/api.ts`, `tests/unit/test_server_capability.py`.

`pytest tests/unit -q` -> **1870 passed, 1 skipped**. `npm run build` and
`npm test` clean. ruff clean.

### The scope decision this response made explicit

Request was "hook up the AI trading model with the UI, deploy it to the
Raspberry Pi." There is no trained/saved model to deploy as a trading
input -- Phase ML-0's evaluation folds are not persisted -- and the one
measured result (COWZ) is un-replicated, one hit in six comparisons. Built
a **read-only research tab** instead of a `SizingStrategy` integration:
this satisfies "hook up with the UI" honestly, and deliberately does NOT
put an unvalidated, statistically weak signal on a path to money, which
would contradict `ml_plan.md`'s own gating (Phase 4 is "deployment, if it
survives" -- it has not yet survived even Phase 1). Stated here so the
scope narrowing is a recorded decision, not a silent one.

### Decisions worth keeping

* **Same upstream split as backtest, same env var.** `/api/ml/*` forwards
  under `VAI_BACKTEST_UPSTREAM` on the Pi, reusing `upstream.upstream_base()`
  rather than adding a second variable that could disagree with the first
  about whether a research/engine host is configured.
* **A new, smaller forwarding module rather than generalising
  `server/upstream.py`.** `/api/ml/*` is GET-only -- no submitted job, no
  progress socket -- and `upstream.py`'s POST-and-websocket backtest
  forwarding is production-critical and already tested; duplicating ~50
  lines was lower-risk than reshaping it for a caller that needs a third
  of what it does.
* **The router imports no `src.ml.*` and no `lightgbm`/`sklearn`.** It only
  formats JSON `tools/*.py` already wrote — pinned by
  `TestMlInsightsIsReadOnly::test_it_imports_no_ml_training_code`. Keeps it
  safe to run anywhere `server/app.py` runs, and keeps `requirements-ml.txt`
  off the Pi's image as that file's own docstring requires.
* **A missing artifact 404s naming the exact command to run**, rather than
  a fabricated empty result. "No data" and "nobody built this yet" are
  different facts and the UI treats them differently (`NotBuiltYet`).
* **The ablation tool was formalised, not left as an ad hoc script.** The
  category breakdown from the prior session's exploration is now
  `tools/ablate_ml_features.py`, producing a artifact the API can serve —
  and re-running it confirmed the earlier read: COWZ 5/14 categories
  consistent (vol block carries nearly all of it), RSP and SPYD both 0/14.

### Deploy status

Pushed to `origin/main`. **Could not deploy to the Pi from this session** —
checked SSH access to both configured hosts (`pivpn`/172.16.0.137,
172.16.0.130); both refused key authentication. Handed the user the exact
pull-and-rebuild command to run themselves.

### Carried gaps

* Nothing is wired into `SizingStrategy`. No model touches the engine —
  unchanged from Phase ML-0, and deliberately so this response.
* The Pi has not yet pulled this code; the tab does not exist there until
  the user runs the deploy step.
* `ml_insights.py`'s 404-with-hint relies on the workstation actually
  having run the `tools/*.py` pipeline — true today, but a fresh workstation
  checkout starts with an empty tab until that is re-run.

---

## Phase ML-2 — ML strategy wired into the backtest engine (2026-09-07) — COMPLETE

**Delivered:** `src/ml/{rolling,live_features,reachability_sizing}.py`,
`tools/train_ml_model.py`, `tests/unit/test_ml_{rolling,optional_dependency,
reachability_wiring}.py`; extended `src/strategy_registry.py`,
`server/backtest.py`, `optimization_controller.py`, `ParameterForm.tsx`.

Request was "hook up the ai trading model with UI... how do I select the ai
model for simulations" -- resolved by asking one scoped question (backtest-only,
no live capital either way) rather than guessing: build for all three funds
with the COWZ-only-measured caveat stated in the UI, vs. COWZ-only, vs. don't
build yet. User chose the first. `ml_reachability_rsp/_cowz/_spyd` are now
real, selectable `SizingStrategy` entries.

`pytest tests/unit -q` -> **1890 passed, 1 skipped**. `npm run build`/`npm test`
clean. ruff clean.

### Decisions worth keeping

* **36 training features, not the offline dataset's 95** -- exactly what a
  `SizingStrategy` can compute from `MarketContext` alone at inference time
  (21 bar-local + the 15-feature volatility block the ablation already
  singled out). Training on more than inference can supply would validate a
  model never actually running on its own inputs.
* **`features.py` refactored (`transformed_sources()`) so live and offline
  share one transform implementation** for the external block, rather than
  a second copy of the ratio-then-transform pipeline to keep in sync by hand.
* **RSI re-derived, not reused from `src.sizing_indicators.WilderRSI`.**
  That class implements classic Wilder seeding; the offline dataset used
  pandas' `ewm(adjust=False)`, which converges to the same place but differs
  during warmup and by a small persistent amount after -- confirmed by the
  parity test, which failed against `WilderRSI` and passes against the
  re-derived version.
* **A calendar train/test cutoff (2024-01-01), recorded in the model's own
  metadata sidecar as `measured_test_auc`** rather than trusted-but-unverified
  -- because this is the first tool in the project that PERSISTS a model a
  user can then backtest over any range, including its own training window.
* **Confidence only shrinks a position, via `_BaselineScaledStrategy`** --
  reused, not reimplemented, and consistent with every other model-driven
  strategy already in `src/size_calculators.py`.
* **No trigger override.** Shares the grid's known stranding vulnerability
  with every strategy but `hf_local_reference`; stated in the module
  docstring as a real, unaddressed limitation.
* **Measured, not assumed, performance: ~25x slower per bar (~600us vs
  ~23us).** `predict(num_threads=1, validate_features=False)` recovered
  ~25% of the model-call cost; a deeper rewrite of the feature tracker was
  judged not worth it against how weak the underlying signal still is.
  Surfaced in the UI, not just the code.

### Two bugs caught before they shipped, worth restating

* **A ticker mismatch reintroduced the "rank_by column not found" failure
  mode `server/backtest.py`'s own comment already named once**, buried
  behind `optimization_controller.py`'s per-combination error isolation.
  Caught only by driving the mismatch through the REAL API path
  (`run_backtest`), not by unit-testing the deep guard alone. Fixed with
  the same early check `build_config()` already does for `target_return`.
* **`server/app.py` imports `backtest` -> `strategy_registry`
  UNCONDITIONALLY at startup**, regardless of `VAI_BACKTEST_UPSTREAM` --
  so a module-level `import lightgbm` in the new strategy would have
  crashed the Pi's entire web container, not just backtesting (lightgbm is
  never installed there). Fixed with a lazy import inside `__init__`;
  verified by actually blocking the import and re-importing `server.app`
  fresh, not by code inspection.
* A third, smaller one, in the tests written to catch the first two: a
  fixture in `test_ml_optional_dependency.py` popped modules from
  `sys.modules` and reimported them by NAME at teardown, which is not the
  same as restoring the ORIGINAL objects -- a sibling test file's
  module-level `from x import y` held a now-stale reference, failing under
  the full suite while passing standalone. Fixed by saving and restoring
  the exact module objects by reference.

### Carried gaps

* Nothing reaches the paper/live loop. This strategy is `server/backtest.py`
  and `optimization_controller.py` only.
* No trigger override -- the stranding risk this project has repeatedly
  measured on other strategies applies here too, unaddressed.
* Fresh checkout needs `tools/train_ml_model.py` re-run before these three
  strategies work at all -- `data/ml/models/` is gitignored, same as every
  other derived data directory in this project.
