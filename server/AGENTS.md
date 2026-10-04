# server/ — FastAPI Backend

**Generated:** 2026-09-24T02:20:00Z — score 14 (distinct domain)

## OVERVIEW
Loopback-only FastAPI backend for `web/` — durable queue, shards, history, live read-only.

## STRUCTURE
```
server/
├── app.py            # lifespan restores queue; mounts web/dist in prod
├── jobs.py           # JobQueue — durable single-worker (output/queue/)
├── contract.py       # pure translators: pre-condensed ↔ condensed wire shape
├── shards.py         # shard registration gated on git commit (simultaneous deploy)
├── shard_client.py   # cli.py shard — claims run, caches bars by fingerprint
├── backtest.py       # simulation over warehouse bars (validated via BacktestConfig)
├── live.py           # read-only (mode=ro, no broker import)
├── control.py        # only write: CircuitBreaker endpoint
├── history.py        # output/runs/ capped at MAX_RUNS
├── ml_insights.py    # read-only precomputed ML artifacts
└── tests/            # AST capability, run-resume, API
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Queue | `jobs.py` | Cooperative pause/cancel via `_ResumableSearch`; `_BestOnlySink` avoids OOM |
| Wire shape | `contract.py` | Applied at read boundary; old `output/runs/` translated, never rewritten |
| Distributed | `shards.py`, `shard_client.py`, `jobs.py:SHARDS` | Ownership check + timeout + last-wins |
| Live state | `live.py` vs `control.py` | Read-only vs single write — AST-enforced by `test_server_capability.py` |

## CONVENTIONS
- Default `127.0.0.1`, CORS explicit `127.0.0.1:5173` — never wildcard/`0.0.0.0` (loopback-only, no auth; balances/positions).
- No `--workers` — single-worker queue; multiple workers would each restore it.
- `run_backtest` never `return_full_results=True` — `_BestOnlySink` keeps best only; rebuild pre-restart best by re-simulating one config.
- Root `conftest.py` (not under `tests/`) isolates `VAI_QUEUE_DIR`/`VAI_RUN_HISTORY_DIR` via temp dirs.

## ANTI-PATTERNS
- Never widen `live.py`/`deployment.py` imports — AST test fails.
- Never change shard wire without simultaneous deploy of `shards.py` + `shard_client.py`.
- Never add auth-free `0.0.0.0` bind without deliberate security review.
