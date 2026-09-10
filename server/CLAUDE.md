# server/

FastAPI backend for `web/`. Run with:

```bash
pip install -r requirements-web.txt
uvicorn server.app:app --host 127.0.0.1 --port 8000
```

## The boundary is the whole design

| Module | Power | Enforcement |
|---|---|---|
| `live.py` | **Read-only.** Opens the ledger store `mode=ro` — SQLite itself refuses a write. Imports no broker. | |
| `control.py` | **The only write.** One endpoint, reaching the existing `CircuitBreaker` and nothing else. | |
| `backtest.py` | **Bidirectional** — a simulation over a CSV can't touch a real position. Validated through `BacktestConfig`. | |
| `deployment.py` | Read-only: which build is running. | |
| `history.py` | Completed runs persisted to disk — a restart loses only queued/running jobs (`jobs.py`), acceptable for a single-operator tool. | |
| `jobs.py` | In-process queue for backtest runs (~23s per 10-year sweep, measured). | |
| `ml_insights.py` | Read-only, precomputed ML research artifacts. **Not on the path from a bar to an order** — no sizing strategy or live loop imports it. | |
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
