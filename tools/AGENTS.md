# tools/ — Ops & Data Prep

**Generated:** 2026-09-24T02:20:00Z — score 9 (distinct domain, never imported)

## OVERVIEW
Ops scripts, data prep, research probes. Nothing in `engine/` or `research/` imports this directory.

## STRUCTURE
```
tools/
├── build_warehouse.py      # CSV → lake (bars.py is only read path); --ingest TQQQ
├── harness.py              # Escalating harness, formula written once (test-guarded glob)
├── backup_databases.py
└── experiments/            # probe_*, measure_*, stage* — one-off probes
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Warehouse ingest | `build_warehouse.py --ingest TICKER` | Data-validation before write; warehouse lake `ticker/year` Parquet |
| ML dataset | `build_ml_dataset.py` | Feeds `research/ml/features.py` offline |
| Harness | `harness.py` | Single `Escalating` definition; `glob("tools/*.py")` non-recursive |
| Probes | `experiments/` | Named in ~130 places in README/plan — don't move without grep |

## CONVENTIONS
- Bootstrap: `sys.path` insertion before `import engine/research` — `E402` exempt in `pyproject.toml` for this reason only.
- `result_sink` Protocol seam — storage fault must not kill sweep; never hold `SimulationResult`.
- `data/` is intake only; backtests read warehouse via `load_frame(symbol)`, not CSVs.

## ANTI-PATTERNS
- Never let `engine/` or `research/` import `tools/` — move shared thing to `engine/core` instead.
- Never move `tools/` paths without grepping `README.md`, `plan.md`, `docs/` (hard-referenced).
- Never add second hashing scheme — use `core/artifacts.canonical_hash` + `parameter_hash`.
