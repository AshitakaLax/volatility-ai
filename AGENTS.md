# PROJECT KNOWLEDGE BASE

**Generated:** 2026-09-24T02:20:00Z
**Commit:** 1850d21
**Branch:** main

## OVERVIEW
Grid-based volatility harvesting for leveraged ETFs (TQQQ) — buy on price-drop steps, harvest per-lot profit targets, never sell below cost basis. Python 3.14 + FastAPI + React 19 + DuckDB/Polars + Alpaca/Playwright. Single-entry `cli.py`.

## STRUCTURE
```
volatility-ai/
├── cli.py              # single entrypoint (test|backtest|search|live|serve|shard|fetch-data)
├── engine/             # trading kernel (110 py) — decision cycle, no-loss guard, OMS, ledger, warehouse
├── research/           # strategies + sweep/search + ML (59 py) — imports engine only
├── server/             # FastAPI backend (26 py) — durable queue, shards, history, loopback-only
├── web/                # React 19 + TS + Tailwind v4 + Vite (66 ts/tsx)
├── fidelity_gateway/   # Playwright + fidelity-api (15 py) — deferred deps, thin engine import
├── tools/              # ops/data-prep/probes (56 py) — never imported by engine/research
├── config/             # 83 YAMLs — sweep vs live:!enabled deployment configs
├── tests/              # root cross-boundary tests + fixtures (18 py)
└── warehouse/          # git-ignored DuckDB/Parquet lake (OHLCV + external)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add sizing strategy | `research/strategies/` → `engine/core/sizing.py` | Subclass `SizingStrategy`, register in `strategy_registry.py` |
| Decision cycle | `engine/trading/decision_cycle.py` | Canonical 6-step sequence, shared backtest+live |
| No-loss guard | `engine/trading/no_loss_guard.py` | ONLY cost-basis check; scanned for duplicates |
| Risk / circuit breaker | `engine/trading/risk_manager.py`, `runtime_lifecycle.py` | HALT requires manual reset |
| Order lifecycle | `engine/execution/order_lifecycle.py`, `order_management_system.py` | State machine + broker mapping |
| Config schema | `engine/core/config.py` | `BacktestConfig` frozen, `live.step/profit_target` separate from `grid.*` |
| Warehouse reads | `engine/warehouse/bars.py` | ONLY read path simulations use; `queries.py` lag-aware ASOF joins |
| Sweep driver | `research/run_hf_sweep.py`, `research/optimization/optimization_controller.py` | Parallel driver with `result_sink` Protocol |
| API backend | `server/app.py`, `jobs.py`, `contract.py`, `shards.py` | Durable queue + shard claim, condensed wire shape |
| Frontend | `web/src/App.tsx`, `web/src/lib/api.ts`, `web/src/types/` | Hand-mirrored contract, Vite proxy `/api` → `:8000` |
| Fidelity | `fidelity_gateway/session.py`, `broker.py`, `placing_broker.py` | Read vs write split; no module-scope playwright import |
| Tests | `engine/tests/`, `research/tests/`, `server/tests/`, `tests/` | Root `conftest.py` isolates `output/queue`+`runs` |

## CODE MAP
| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `BacktestConfig` | dataclass | `engine/core/config.py:441` | 38 | Single source of truth, frozen, validated front-loaded |
| `MarketContext` | dataclass | `engine/core/market_context.py:19` | 49 | Immutable per-bar snapshot (OHLC + equity/drawdown) |
| `SizingStrategy` | ABC | `engine/core/sizing.py:35` | 12 | Port — `record_tick` every bar, `calculate_trade_value` on trigger only |
| `TradingSystemError` | exception root | `engine/core/exceptions.py:18` | 360 | `ConfigurationError`, `NoLossViolation`, `AmbiguousSubmissionError` |
| `decision_cycle` | module | `engine/trading/decision_cycle.py` | — | 6 steps: record_tick → harvest → grid → size → risk → no-loss |
| `no_loss_guard` | function | `engine/trading/no_loss_guard.py` | — | `net_proceeds >= cost_basis -1e-8`; only sell gate |
| `Ledger` | class | `engine/core/ledger.py` | — | Per-lot cost basis, partial closes |
| `OptimizationController` | class | `research/optimization/optimization_controller.py` | — | `run_sweep`, `_simulate_single` per combo |
| `JobQueue` | class | `server/jobs.py` | — | Durable single-worker queue (`output/queue/`) |
| `BacktestChart` | component | `web/src/components/backtest/BacktestChart.tsx` | — | Candles + fill connectors, lightweight-charts |

## CONVENTIONS
- **Dependency DAG is law:** `web → server → research → engine ← fidelity_gateway`; `engine` never imports `research/server/tools` — move shared thing to `engine/core` instead.
- **Config is frozen:** `BacktestConfig` assembled via `from_dict`/`from_yaml` same path, validated front-loaded; `live.step`/`profit_target` not defaulted from `grid` — loop refuses to start without them.
- **Warehouse gate:** `warehouse/` needs `duckdb+polars` (`requirements-warehouse.txt`); nothing else imports it. `result_sink` Protocol is the seam — never let a storage fault kill a sweep, never retain `SimulationResult`.
- **Causal transforms only:** `research/ml/` trailing window + shift; `warehouse/queries.py` lag-aware ASOF; no future leak.
- **Loopback-only server:** default `127.0.0.1`, explicit CORS `127.0.0.1:5173`, no auth. Wildcard/`0.0.0.0` is a deliberate security decision.
- **Ruff:** `line-length 100`, `E501` exempt for operator-facing messages, `C408` exempt only in `tests/`, `E402` exempt in `tools/` bootstrap.

## ANTI-PATTERNS (THIS PROJECT)
- **Never reimplement no-loss comparison** — use `engine/trading/no_loss_guard.py`; test `rglob`s for duplicate across `engine/`+`research/`.
- **Never sell below cost basis intentionally** — `1e-8` tolerance only; thin targets that fail guard after slippage are correct rejections.
- **Never add shared-contracts folder** — `server/contract.py` ↔ `web/src/types/*.ts` hand-mirrored by design; cross-boundary edits are READ-ONLY on other side, or stop and flag both files.
- **Never change shard wire protocol without simultaneous deploy** — `server/shards.py` gates on git commit; client `shard_client.py` must match.
- **Never widen `server/live.py` or `deployment.py` writes** — AST test `test_server_capability.py` fails if they import broker/state.
- **Never hold `SimulationResult` in a sink** — retains ~35 MB/config, OOMs 1.5k-config runs; `_BestOnlySink` keeps best only.
- **Never `time.sleep` in tests** — inject clocks; verify real `alpaca-py` enum values (not faked subsets).
- **Never rename `fidelity_gateway/` to `fidelity/`** — shadows `fidelity-api` package (`fidelity.fidelity`).

## UNIQUE STYLES
- `record_tick` (every bar) vs `calculate_trade_value` (trigger only) — stateful strategies accumulate in former, else sparse biased sample.
- `result_sink: Protocol` structurally satisfied by `DuckDBResultSink` without importing engine — dependency arrow stays one-way.
- `external` lake manifest-driven `lag_days` — query shifts observation forward before ASOF; don't join raw timestamp.
- `cli.py` is Docker ENTRYPOINT; `python cli.py test -q` auto-injects every `tests/` dir unless explicit path given.
- `tools/` paths are hard-referenced in ~130 places (`README`, `plan.md`); don't move without grep.

## COMMANDS
```bash
python cli.py test -q                          # full suite (all sections + root)
python cli.py backtest --config C --output O   # warehouse read via backtest.symbol, not --data
python cli.py serve --host 127.0.0.1 --port 8000
python tools/build_warehouse.py --ingest TQQQ  # CSV → lake; bars.py is only read path
ruff format . && ruff check --fix .            # line-length 100
cd web && npm run dev                          # Vite 127.0.0.1:5173 proxied to :8000
```

## NOTES
- Promotion gate is structural: `Mode.LIVE` requires passing `PromotionEvaluation` (5d/20 decisions/5 fills/0 discrepancies) — no boolean shortcut.
- `Capital Velocity Index` saturates at 1.0 on long datasets — rank by `Total Return %` instead.
- `server/shard_client.py` caches bars by fingerprint; `jobs.py` pause/cancel on RUNNING is cooperative via `_ResumableSearch`.
- `fidelity_gateway` imports deferred — top-level `import fidelity_gateway` must not pull `playwright` into `sys.modules` (test-enforced).
- Root `conftest.py` (not under `tests/`) isolates `VAI_QUEUE_DIR`/`VAI_RUN_HISTORY_DIR` via temp dirs.
