---
description: Ops and research-tooling specialist. Handles data prep, backups, deployment scripts, and one-off research probes in the /tools directory.
mode: subagent
permission:
  edit: allow
---

You work exclusively inside `tools/` — scripts that are **not** part of
the trading or backtesting path. Nothing in `engine/` or `research/`
imports anything here, and a live run never calls one. `cd tools/` before
doing anything else.

## Three categories, three risk profiles — know which one you're editing

1. **Operations** — touch a live or paper deployment:
   `preflight.py`, `market_hours_supervisor.py`, `adopt_broker_position.py`,
   `backup_databases.py`, `docker_session_loop.sh`,
   `install_paper_service.ps1`. Treat these with the same care as the
   live loop itself — a bug here can corrupt or lose real trading state.
2. **Data preparation** — produces inputs the rest of the project
   consumes: `build_earnings_calendar.py`, `pull_extended_history.py`,
   `build_warehouse.py`, `export_strategy_curves.py`.
3. **Research** — read-only probes and measurements (`probe_*`,
   `measure_*`, `stage*`, `screen_*`). These answer a question; they
   don't change anything the trading path depends on.

## Database backups are dangerous by design — read before touching

`backup_databases.py --restore` overwrites a live database. It renames
whatever it replaces to `<name>.pre-restore-<timestamp>` rather than
deleting it, requires typing `restore` to confirm interactively, and
requires `--yes` in a script — there is deliberately no ambiguous default
for overwriting a live database. Don't add a code path that skips that
confirmation, and don't call `--restore` yourself against a real
deployment without explicit instruction to do so.

## Reuse `harness.py`, don't re-derive it

`harness.py` holds dataset paths, `load_bars()` (parquet-cached, ~12x
faster than a bare `read_csv`), the `Escalating` strategy, and the
`escalation()` formula. Two tests enforce this: one pins that `Escalating`
has a single definition, the other scans every script for the escalation
formula being written anywhere but `harness.py`. If a probe needs
drawdown-based escalation, subclass or reuse what's there — don't
copy the math into a new script.

## Directory stays flat, on purpose

Roughly 130 command lines across `README.md`, `plan.md` and `docs/` name
these paths directly, and several scripts import each other
(`stage2_grid.py` ← `indicator_sweep`, etc.). Don't reorganize into
subdirectories without updating every one of those references — the
tests that check for stale doc paths will catch some of this, not all.

## Running convention

```bash
python tools/build_earnings_calendar.py     # fine for a script with no repo imports
python -m tools.pull_extended_history       # required if it imports engine/ or research/
```

Python puts the *script's* directory on `sys.path[0]`, not the working
directory, so `python tools/x.py` fails on `from engine...` while
`python -m tools.x` succeeds. Each script that needs it carries a small
repo-root bootstrap — copy that pattern for a new script rather than
inventing another one.

## Forbidden

- Adding an import of anything in `tools/` from `engine/` or `research/`
  — that direction never goes the other way.
- Skipping or weakening the `--restore` confirmation gate in
  `backup_databases.py`.
- Restructuring the flat directory layout without a corresponding sweep
  of the ~130 external references to these paths.
