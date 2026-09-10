# config/

Every file here is a `BacktestConfig` YAML (`src/core/config.py`). Three
kinds live side by side — check which one before editing:

| Kind | Examples | `live.enabled` | Purpose |
|---|---|---|---|
| **Sweep** | `search_hf_*.yaml`, `sweep_5y*.yaml`, `probe_*.yaml`, `lotcap_test_*.yaml` | false/absent | a `grid`/`bayesian`/`random` search space for `src/scripts/run_hf_sweep.py` or `python cli.py search`/`backtest` |
| **Pinned champion** | `best_known_2026-08-24.yaml`, `paper_aggressive.yaml`, `soxl_champion.yaml` | false | a single-point config reproducing one specific best-known result — not a search space, don't add a grid to it |
| **Deployment** | `staging.yaml`, `production.yaml`, `staging_hf_local_reference.yaml` | **true** | drives `python cli.py live` / the `live-staging` / `live-production` containers. `staging.yaml` → paper credentials, `production.yaml` → live credentials + a passing `PromotionEvaluation`. These are never sweep configs. |

`fidelity_local.yaml.example` is a template for local Fidelity-broker
credentials — copy, don't edit in place, and never commit the real one.

## Naming tells you the axis under test

`probe_*.yaml` files are **controlled, single-variable probes** — e.g.
`probe_vol_scaling.yaml` sweeps only `vol_scale_exponent` with everything
else pinned at a prior sweep's best. `lotcap_test_*.yaml` differ only in
`risk.max_concurrent_lots`. Read the target file's own header comment for
its specific rationale before assuming what it isolates.

## Reproducing a result

README's [Simulations run to date](../README.md#simulations-run-to-date)
table is the authoritative reproduction index: every config that has
actually been swept, the question it answered, the exact command, and
where its output CSV lives (or the commit it was recorded in, if the CSV
wasn't retained). Check there before re-running a sweep from scratch.

`live.step` / `live.profit_target` in a deployment config are **separate**
from a sweep's `grid.steps` / `grid.profit_targets` — the loop refuses to
start without them stated explicitly, on purpose (see
`README.md#configuration`).
