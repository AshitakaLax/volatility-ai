# server/

FastAPI backend for `web/`. Run with:

```bash
pip install -r requirements-web.txt
uvicorn server.app:app --host 127.0.0.1 --port 8000
# or, equivalently:
python cli.py serve
```

`cli.py serve` (repo root) is a thin wrapper: it checks fastapi/uvicorn
are installed (a clear message pointing at requirements-web.txt instead
of a bare ModuleNotFoundError if not), then shells out to the same
`uvicorn server.app:app` invocation. `--host`, `--port`, `--reload`
pass through; there is deliberately no `--workers` -- `jobs.py`'s
backtest queue is single-worker by design (see below), and multiple
uvicorn workers would each restore and run it independently.

## The boundary is the whole design

| Module | Power | Enforcement |
|---|---|---|
| `live.py` | **Read-only.** Deployments by id (`GET /api/live/deployments[/{id}[/commands\|/activity\|/bars\|/fills\|/bridge/events]]`, `/ws?deployment=`): the ledger read `mode=ro` — SQLite itself refuses a write — beside what the trader reports in its control directory: its status (what it will do next and why, its shadow of the config file's algorithm, its build, a Fidelity bridge's connection, why a start stopped) and its bar and fill journals. A Fidelity deployment's bridge host reports there too, under `bridge/` (`bridge_state`: readiness, the extension's connection, what is attached; and its event journal), up between sessions. Each card names the algorithm IN FORCE (`algorithm_in_force`: the trader's report, else the override laid over the YAML) and its venue (`broker`); a deployment registered before its config exists answers `setup`. Imports no broker; no route takes a path. | `test_server_capability.py` |
| `algorithms.py` | **The one writer of profiles.** `GET/POST /api/algorithms[...]`: a backtest cell kept as a candidate (`output/algorithms/`; a composed cell is named and labelled for its buy and sell, and marked when its sell may sell below cost), offered for a trial only on paper deployments whose trader's own `AlgorithmControl.check` takes it (`paper_refused` says why the others would not), a paper trial (queued through `live_control.queue_command`), its evaluation (`engine/promotion_record.py`), the owner's sign-off and publishing into `config/live_profiles/` (+ `promotions/`), the only folder mounted read-write into `web`. Ids are validated here and no route takes a path. | `test_server_capability.py` |
| `live_registry.py` | The deployments the Live page shows, by id: `config/deployments.yaml` (`VAI_DEPLOYMENTS` for tests) names each one's config, ledger and control directory as `web` sees them. Paper or real money comes from the config. | |
| `live_control.py` | **Queues commands; changes nothing itself.** `POST /api/live/deployments/{id}/commands` (pause/resume buys, disable now or wind down, enable; `check_connection`, read-only, goes to a Fidelity bridge host's own inbox) and `.../commands/{cid}/cancel` write into the deployment's control directory (`engine/trading/control_inbox.py`); the TRADER applies them (`engine/trading/operator_control.py`), so it stays the only writer of its ledger. What each deployment takes is its config's `live.control`; real money needs the id typed back. No login (the operator's choice); a cross-site guard on every POST. No liquidation command. | `test_server_capability.py` |
| `backtest.py` | **Bidirectional** — a simulation over warehouse bars can't touch a real position. Validated through `BacktestConfig`. | |
| `deployment.py` | Read-only: which build is running (served inside `/api/health`; no route of its own). | |
| `history.py` | Completed runs persisted to disk (`output/runs/<id>.json`), **uncapped** -- every run is kept. Beside each archive, rebuildable derived files under `output/runs/derived/`: a fills-free summary (served by `GET /runs/{id}`), a slim history index, and per-fund columnar fills (`.npz`). Archives are never rewritten; derived files are rebuilt whenever missing or older. | |
| `fills.py` | A run's fills, columnar, queried a page at a time -- `GET /runs/{id}/fills` (+ `.csv`). Reports carry `fills_count`, never fills inline (a busy run's are ~850k rows). Filter/cycle rules are a port of the browser's old ones; `tests/test_fills.py` pins them. | |
| `history_query.py` | Run History, server-side: one fund (required) filtered, sorted and paged -- `POST /history/query`, `GET /history/{funds,facets,runs}`. Rules ported from the browser's old `filters.ts`; `tests/test_history_api.py` pins them. | |
| `contract.py` | Pure translators from the **pre-condensed** wire shape (old `RunRequest` names, `parameters`/`timeframe`/`configurations`/`executions` reports) to the current one. Applied at the read boundary: `RunRequest`'s pre-validator, `JobQueue.restore`, `history.load*`. | |
| `jobs.py` | **Durable** single-worker queue: pending runs, their order and per-configuration checkpoints survive a restart (`output/queue/`, `VAI_QUEUE_DIR`). Pause / resume / cancel / reorder / run-next; restored by `app.py`'s lifespan hook, never at import. Each shard may also carry a daily lockout window (`set_shard_schedule`) -- independent of a manual pause, see its "LOCKOUT WINDOWS" doc section. | |
| `warehouse_status.py` | **Read-only**, GET only: the Warehouse tab. `GET /api/backtest/warehouse` (funds and how many sessions behind, sweeps and simulations, storage) through `engine/warehouse/inventory.py`'s read-only open -- the bar scan cached until the lake's files change, the rest for 30 s; `GET /api/backtest/system` (load, temperatures, memory, disks, the queue's remaining configurations, shards, newest backup). Under `/api/backtest` so a forwarding host forwards it. | `test_server_capability.py` |
| `ml_insights.py` | Read-only, precomputed ML research artifacts. **Not on the path from a bar to an order** — no sizing strategy or live loop imports it. | |
| `shards.py` | **Distributed sweeps.** The HTTP face of the queue's shard bookkeeping (register / claim / sync / finish) plus the bar download a shard needs. Under `/api/backtest/` so the Pi forwards it with the rest. | |
| `shard_client.py` | The `cli.py shard` process: claims one sweep, runs the real `run_backtest` on that machine's cores, streams every finished configuration back. Caches bars on disk by fingerprint. | |
| `ml_upstream.py`, `upstream.py` | Forward requests to the workstation that actually has `data/external/`, `data/ml/` and `requirements-ml.txt` (the Pi deployment doesn't). | |

`server/tests/test_server_capability.py` walks each module's AST and fails
if a module reaches for power its docstring disclaims — don't add an
import to `live.py` or `deployment.py` that would trip it. A new live
control is a new command type: queued by `live_control.py`, applied by the
trader in `engine/trading/operator_control.py` — never a ledger write here.

## Never widen this without thinking about it

No authentication exists. That's acceptable **only** on loopback, which
is why the default host is `127.0.0.1` and CORS is an explicit origin
list (`http://127.0.0.1:5173`, `http://localhost:5173`) — **never** a
wildcard. This server returns account balances, positions, and cost
bases. Binding `--host 0.0.0.0` or adding to the CORS list is a
deliberate, considered act, not a config tweak.

In production the built `web/dist` is mounted directly by `app.py`
(copied in by the Dockerfile's multi-stage build), giving one origin and
no CORS involvement at all — the dev-server CORS list above only matters
when running `vite dev` against a separately-running API.

## The backtest queue survives restarts — and why that changed

`jobs.py` used to be deliberately in-memory: losing a 30-second run on
restart was fine. A 4-day, 84-run sweep lost everything to a reboot, so
it now persists pending runs (`state.json`) and every finished
configuration of a running run (`<run_id>.rows.jsonl`). A restart costs
the in-flight batch, not the run. See `jobs.py`'s module docstring.

Two things that follow from it:

- **Pause/cancel on a RUNNING run are cooperative.** `run_backtest` stops
  handing out configurations through `_ResumableSearch.suggest()` (the
  one seam `run_sweep` consults before every configuration —
  `progress_callback` can't do it, its exceptions are swallowed), lets
  the batch in the process pool finish, then raises `RunStopped`.
- **`run_backtest` must never set `return_full_results=True` on the main
  sweep.** It retained ~35 MB per configuration on full-history intrabar
  runs; a 1,536-config chunk grew the server to 31.4 GB and bugchecked a
  15 GB machine. `_BestOnlySink` keeps only the running best, and a best
  that finished before a restart is rebuilt by re-simulating that one
  configuration (the engine is deterministic).
  `server/tests/test_run_resume.py` pins both.

Tests never touch the real `output/queue/` or `output/runs/`: the root
`conftest.py` (repo root, not under `tests/` -- it has to be an ancestor
of every project directory's own `server/tests/`, `tests/`, etc. to apply
to all of them) points `VAI_QUEUE_DIR` and `VAI_RUN_HISTORY_DIR` at a
temp directory before anything imports `server`.

## Distributed sweeps: one sweep per machine

A run (one sweep) is the unit of distribution. `jobs.py` tracks every
shard, including the built-in `local` one that is this process's own
worker, and hands each a run to own; `shards.py` is only the HTTP face of
that. Three rules stop two machines writing the same run -- ownership
checked on every report, a timeout that releases a silent shard's run,
and last-registration-wins for a name. See `jobs.py`'s "SHARDS" section.

Pausing a SHARD is not pausing a RUN: the shard stops taking
configurations and its sweep returns to the queue for another shard,
which resumes it from the same checkpoint a restart would use. Pausing a
run or the queue is unchanged.

    cli.py serve --host 0.0.0.0                 # the engine host
    cli.py shard --name fast-shard --main HOST  # each extra machine

## The wire contract is condensed — and old data still loads

`web/src/types/*.ts` is the contract; its header explains the shape.
Run-level fields are stated once, a fund's headline metrics are
`cells[0].m`, false/null flags are omitted, and fields that are a fixed
function of others (`Param` group/step/sweepable, rebased equity, a
lot's market value) are computed client-side. Figures with a single
Python definition -- `to_target`, `buying_power` -- stay server-side. Queue controls are one
`POST /runs/{id} {op}` and one `POST /queue {paused}`.

Archives in `output/runs/` and requests in `output/queue/state.json`
written before that change are translated by `contract.py` on read —
the files themselves are never rewritten (a restored queue is persisted
in the new shape on its next change). `RunRequest` still **accepts** the
old field names, so scripts and a queued multi-day sweep keep working.
The Pi and the workstation must deploy together: `upstream.py` relays
bytes unchanged.
