# volatility-ai

Grid-based volatility-harvesting strategy for leveraged ETFs (primarily
TQQQ): buy on configurable price-drop steps, harvest each lot at its own
profit target, never sell below cost basis. `README.md` is the full,
detailed reference (architecture, config schema, safety invariants,
statistical validation, promotion path, troubleshooting) — read it before
touching anything load-bearing. This file is a condensed map plus the
gotchas README doesn't (yet) have.

## Current package map

| Package | Nested CLAUDE.md | Responsibility |
|---|---|---|
| `src/core` | — | `BacktestConfig`, exceptions, ledger, audit, persistence, secrets, idempotency |
| `src/trading` | [src/CLAUDE.md](src/CLAUDE.md) | canonical decision cycle, no-loss guard, risk manager, live loop |
| `src/execution` | | order lifecycle, OMS, reconciliation, fill accounting |
| `src/strategies` | | `SizingStrategy` implementations, `MarketContext` |
| `src/data` | | historical/live bar fetch, calendars, tick validation |
| `src/analysis` | | cost models, performance metrics, validation, annualized reports |
| `src/optimization` | | sweep orchestration, grid/Bayesian search, walk-forward, Monte Carlo |
| `src/brokers` | | Alpaca + Fidelity broker adapters |
| `src/ml` | | reachability-sizing research: features, labels, live feature vectors (read-only research, not a trading input by default — see `src/ml/reachability_sizing.py`) |
| `src/ui` | | Streamlit `dashboard.py` |
| `src/scripts` | | `run_hf_sweep.py`, Fidelity recon/order-test scripts |
| `cli.py` (repo root) | | single entrypoint: `test \| backtest \| search \| live \| fetch-data`, the Docker `ENTRYPOINT` |
| `server/` | [server/CLAUDE.md](server/CLAUDE.md) | FastAPI backend for the web UI |
| `web/` | [web/CLAUDE.md](web/CLAUDE.md) | React/TS frontend |
| `tools/` | [tools/README.md](tools/README.md) (already a good CLAUDE.md-equivalent) | ops scripts, data prep, research probes — nothing here is imported by `src/` |
| `config/` | [config/CLAUDE.md](config/CLAUDE.md) | sweep configs vs. `live:`-enabled deployment configs |
| `tests/` | [tests/CLAUDE.md](tests/CLAUDE.md) | unit / integration / e2e / fixtures |

## The one invariant that matters most

`src/trading/no_loss_guard.py` is the **single** place a sell is checked
against its cost basis. It never sells for less than
`allocated_cost_basis - 1e-8` (accounting for costs). Any change that
touches sell logic should route through this module, not reimplement the
comparison — a test scans the codebase for a reintroduced duplicate.

## Commands

```bash
python cli.py test -q                 # full suite (905+ tests)
python cli.py backtest --config C --data D --output O
ruff format . && ruff check --fix .   # formatting + lint (pyproject.toml: line-length 100)
```

See README.md's [Testing](README.md#testing), [Configuration](README.md#configuration)
and [Safety invariants](README.md#safety-invariants) sections for depth.

## Docs index

- `README.md` — the full reference, kept current for *concepts and config*,
  stale for *some file paths* (see drift note above)
- `CHANGELOG.md` — why decisions were made, including resolved spec
  contradictions; read before changing anything load-bearing
- `plan.md` — the staged indicator sweep and each stage's result
- `docs/` — Alpaca setup, Raspberry Pi deployment, pre-production checklist
- `tools/README.md` — the ops/data-prep/research script map
