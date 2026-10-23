# volatility-ai

Grid-based volatility-harvesting strategy for leveraged ETFs (primarily
TQQQ): buy on configurable price-drop steps, harvest each lot at its own
profit target, never sell below cost basis. `README.md` is the full
reference (architecture, config schema, safety invariants, validation,
promotion path, troubleshooting) — read it before touching anything
load-bearing. This file is the condensed map plus the rules. `AGENTS.md`
is a symlink to it, so every agent tool reads the same text.

## Project directories (each is a session root)

Open the **root** for cross-cutting work (the UI↔backend contract,
deployment, a change that spans layers); open one of the others to keep
the context small.

| Session root | Guide | Scope |
|---|---|---|
| `engine/` | [engine/CLAUDE.md](engine/CLAUDE.md) | trading kernel: decision cycle, no-loss guard, OMS, ledger, warehouse, brokers, config |
| `research/` | [research/CLAUDE.md](research/CLAUDE.md) | strategies, sweep/search, metrics, ML |
| `fidelity_gateway/` | [fidelity_gateway/CLAUDE.md](fidelity_gateway/CLAUDE.md) | the route into Fidelity: session, extension bridge, capture, recon, gated placing |
| `fidelity-bridge-chrome-extension/` | its own README | **git submodule** (separate repo): the browser extension the bridge talks to; `npm test` |
| `server/` | [server/CLAUDE.md](server/CLAUDE.md) | FastAPI backend: routes, durable queue, shards, history |
| `web/` | [web/CLAUDE.md](web/CLAUDE.md) | React/TS frontend |
| `tools/` | [tools/README.md](tools/README.md) | ops scripts, data prep, probes — nothing in `engine/` or `research/` imports these |
| `config/` | [config/CLAUDE.md](config/CLAUDE.md) | sweep configs vs. `live:`-enabled deployment configs |
| `tests/` | [tests/CLAUDE.md](tests/CLAUDE.md) | unit / integration / e2e / fixtures |
| `cli.py` | | single entrypoint and Docker `ENTRYPOINT`: `test \| backtest \| search \| submit \| live \| serve \| shard \| backup \| restore \| fetch-data` |

## The dependency direction, which the split depends on

```
web/  ──HTTP──>  server/  ──>  research/  ──>  engine/  <──  fidelity_gateway/
                                                  ^
                                          engine/core is layer 0
```

**`engine/` never imports `research/`.** The engine calls a strategy only
through the `SizingStrategy` port in `engine/core/sizing.py`;
`research/strategies/strategy_registry.py` is the only module that knows
the concrete set exists. If an engine module seems to need something from
`research/`, move the shared thing down into `engine/core/` instead.
`engine/core` imports no other engine package at import time. Verify:

```bash
.venv/bin/python -c "import sys,engine.core.config; print(sorted(m for m in sys.modules if m.startswith(('engine.','research.'))))"
```

## The one invariant that matters most

`engine/trading/no_loss_guard.py` is the **single** place a sell is checked
against its cost basis (`net_proceeds >= allocated_cost_basis - 1e-8`).
Route any sell-logic change through it; a test scans `engine/` and
`research/` for a reintroduced duplicate. The only sale that may realise a
loss is a strategy's `lots_to_liquidate` **and** `execution.allow_signal_exit`
together (the Ultimate family's regime exit).

## Rules

- **Config is frozen and validated up front.** `BacktestConfig` is built
  by `from_dict`/`from_yaml`; `live.step`/`live.profit_target` are never
  defaulted from `grid.*` — the loop refuses to start without them.
- **`record_tick` fires every bar, `calculate_trade_value` only on a
  trigger.** Stateful strategies accumulate in `record_tick`.
- **Live starts every session cold.** The supervisor runs a process per
  session; a strategy whose state spans sessions answers
  `live_history_sessions()` (replayed through `record_tick` first) and, for
  per-lot state, `resume(open_lots)`. `live_algorithm.build_strategy`
  refuses a live config that is not the researched strategy (no
  `allow_signal_exit` for `ultimate*`, extended hours for a regular-session one).
- **Causal transforms only.** `research/ml/` rolls a trailing window then
  shifts; `warehouse/queries.py` shifts macro series by `lag_days` before
  the ASOF join.
- **Warehouse is an optional dependency.** Only `engine/warehouse/` imports
  duckdb/polars; `bars.py` is the only read path a simulation uses. A
  result sink must never raise and never retain a `SimulationResult`
  (~35 MB each — that has OOM'd a machine).
- **The server is loopback-only with no auth.** Binding `0.0.0.0` or
  widening CORS is a deliberate security decision. `server/live.py` and
  `deployment.py` are read-only — an AST test enforces it.
- **The UI↔server contract is hand-mirrored** (`server/contract.py` ↔
  `web/src/types/*.ts`), deliberately with no shared-contracts folder;
  change both or flag both. The shard wire protocol gates on the git
  commit: server and `cli.py shard` machines deploy together.
- **Never rename `fidelity_gateway/` to `fidelity/`** — it would shadow
  the `fidelity-api` package. Importing `fidelity_gateway` must not pull
  in playwright (test-enforced).
- **Tests never sleep** — inject clocks. Root `conftest.py` points
  `VAI_QUEUE_DIR`/`VAI_RUN_HISTORY_DIR` at temp dirs.
- **`tools/` paths are cited in ~130 places** (`README.md`, `plan.md`,
  `docs/`): grep before moving one.
- **Rank sweeps by `Total Return %` or Calmar, not `Capital Velocity
  Index`** — it saturates at 1.0 on long datasets.
- **`research/run_hf_sweep.py` never threads `allow_signal_exit` or cash
  yield**, so it cannot run the `ultimate*` strategies as researched; use
  `OptimizationController.run_sweep` with those set.

## Commands

```bash
.venv/bin/python cli.py test -q                 # full suite (~4,000 tests)
.venv/bin/python cli.py backtest --config C --output O   # bars from the warehouse by backtest.symbol
.venv/bin/python cli.py serve                   # API on 127.0.0.1:8000
.venv/bin/python tools/build_warehouse.py --ingest TQQQ  # CSV in data/ → Parquet lake
.venv/bin/ruff format . && .venv/bin/ruff check --fix .   # line-length 100
cd web && npm run dev                           # Vite on 127.0.0.1:5173, /api proxied to :8000
docker compose up -d --build                    # web (UI+engine, 127.0.0.1:8000), paper loop, daily backup -- docs/DEPLOY.md
```

## Docs index

- `README.md` — the full reference for concepts, config and operations
- `CHANGELOG.md` — why decisions were made; read before changing anything load-bearing
- `plan.md` — the staged indicator sweep and each stage's result
- `docs/` — Alpaca setup, the Docker Compose deployment (`DEPLOY.md`), pre-production checklist,
  `Run_Instructions` (a walkthrough whose code blocks the tests execute),
  `ml_plan.md`, the algorithm ledger and `docs/research/` design logs
- `docs/history/` — finished plans kept for the record (web UI build, old quick start)
