# volatility-ai

Grid-based volatility-harvesting strategy for leveraged ETFs (primarily
TQQQ): buy on configurable price-drop steps, harvest each lot at its own
profit target, never sell below cost basis. `README.md` is the full,
detailed reference (architecture, config schema, safety invariants,
statistical validation, promotion path, troubleshooting) — read it before
touching anything load-bearing. This file is a condensed map plus the
gotchas README doesn't (yet) have.

## Project directories (each is a session root)

The repo is split so a session can be opened in one directory and see
only what that job needs. Open the **root** for cross-cutting work (the
UI↔backend contract, deployment, a change that spans layers); open one
of the others to keep the context small.

| Session root | Nested CLAUDE.md | Scope | Size |
|---|---|---|---|
| `engine/` | [engine/CLAUDE.md](engine/CLAUDE.md) | the trading kernel: decision cycle, no-loss guard, OMS, ledger, warehouse, brokers, config | ~15k lines |
| `research/` | [research/CLAUDE.md](research/CLAUDE.md) | algorithm development: strategies, sweep/search, metrics, ML | ~12k lines |
| `fidelity_gateway/` | [fidelity_gateway/CLAUDE.md](fidelity_gateway/CLAUDE.md) | the Playwright/HTTP route into Fidelity: session, capture, recon, the gated place path | ~4k lines |
| `server/` | [server/CLAUDE.md](server/CLAUDE.md) | FastAPI backend: routes, durable queue, shards, history | ~6k lines |
| `web/` | [web/CLAUDE.md](web/CLAUDE.md) | React/TS frontend | ~17k lines |
| `tools/` | [tools/README.md](tools/README.md) | ops scripts, data prep, research probes — nothing in `engine/` or `research/` imports these | ~13k lines |
| `config/` | [config/CLAUDE.md](config/CLAUDE.md) | sweep configs vs. `live:`-enabled deployment configs | |
| `tests/` | [tests/CLAUDE.md](tests/CLAUDE.md) | unit / integration / e2e / fixtures | ~33k lines |
| `cli.py` (root) | | single entrypoint: `test \| backtest \| search \| submit \| live \| serve \| shard \| backup \| restore \| fetch-data`, the Docker `ENTRYPOINT` | |

## The dependency direction, which the split depends on

```
web/  ──HTTP──>  server/  ──>  research/  ──>  engine/  <──  fidelity_gateway/
                                                  ^
                                          engine/core is layer 0
```

**`engine/` never imports `research/`.** The engine calls a strategy only
through the `SizingStrategy` port in `engine/core/sizing.py`; every
concrete algorithm is an adapter behind it, and
`research/strategies/strategy_registry.py` is the only module that knows
the concrete set exists. If an engine module seems to need something
from `research/`, move the shared thing down into `engine/core/` instead
of adding the import — that is exactly how `market_context.py` and the
`SizingStrategy` ABC ended up there.

`engine/core` imports no other engine package at import time. Verify any
claim here rather than trusting it:

```bash
python -c "import sys,engine.core.config; print(sorted(m for m in sys.modules if m.startswith(('engine.','research.'))))"
```

## The one invariant that matters most

`engine/trading/no_loss_guard.py` is the **single** place a sell is checked
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
