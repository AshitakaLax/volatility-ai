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
| `live.py` | **Read-only.** Opens the ledger store `mode=ro` — SQLite itself refuses a write. Imports no broker. | |
| `control.py` | **The only write.** One endpoint, reaching the existing `CircuitBreaker` and nothing else. | |
| `backtest.py` | **Bidirectional** — a simulation over warehouse bars can't touch a real position. Validated through `BacktestConfig`. | |
| `deployment.py` | Read-only: which build is running (served inside `/api/health`; no route of its own). | |
| `history.py` | Completed runs persisted to disk (`output/runs/`, capped at `MAX_RUNS`). | |
| `contract.py` | Pure translators from the **pre-condensed** wire shape (old `RunRequest` names, `parameters`/`timeframe`/`configurations`/`executions` reports) to the current one. Applied at the read boundary: `RunRequest`'s pre-validator, `JobQueue.restore`, `history.load*`. | |
| `jobs.py` | **Durable** single-worker queue: pending runs, their order and per-configuration checkpoints survive a restart (`output/queue/`, `VAI_QUEUE_DIR`). Pause / resume / cancel / reorder / run-next; restored by `app.py`'s lifespan hook, never at import. Each shard may also carry a daily lockout window (`set_shard_schedule`) -- independent of a manual pause, see its "LOCKOUT WINDOWS" doc section. | |
| `ml_insights.py` | Read-only, precomputed ML research artifacts. **Not on the path from a bar to an order** — no sizing strategy or live loop imports it. | |
| `shards.py` | **Distributed sweeps.** The HTTP face of the queue's shard bookkeeping (register / claim / sync / finish) plus the bar download a shard needs. Under `/api/backtest/` so the Pi forwards it with the rest. | |
| `shard_client.py` | The `cli.py shard` process: claims one sweep, runs the real `run_backtest` on that machine's cores, streams every finished configuration back. Caches bars on disk by fingerprint. | |
| `ml_upstream.py`, `upstream.py` | Forward requests to the workstation that actually has `data/external/`, `data/ml/` and `requirements-ml.txt` (the Pi deployment doesn't). | |

`tests/unit/test_server_capability.py` walks each module's AST and fails
if a module reaches for power its docstring disclaims — don't add an
import to `live.py` or `deployment.py` that would trip it; add the write
to `control.py` instead.

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
  `tests/integration/test_run_resume.py` pins both.

Tests never touch the real `output/queue/` or `output/runs/`:
`tests/conftest.py` points `VAI_QUEUE_DIR` and `VAI_RUN_HISTORY_DIR` at a
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
