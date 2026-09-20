# tests/

The suite is split so each project directory (a session root — see the
root `CLAUDE.md`'s "Project directories" table) carries its own tests,
and a session opened there sees only what that job needs.

```bash
python cli.py test -q                    # everything: this dir + every section's own tests/
python cli.py test -k promotion          # filtered, still across all of them
python cli.py test engine/tests -q       # one section only
pytest engine/tests/test_config.py -q    # or invoke pytest directly on one file
```

`cli.py test` (see `cmd_test` in `cli.py`) inserts every section's
`tests/` directory automatically whenever the arguments don't already
name an explicit path or node id — see `TEST_ROOTS` there for the exact
list. Naming a path yourself (anything with a `/`, a `.py` suffix, or a
pytest `::` node id) runs exactly that instead.

| Location | Scope |
|---|---|
| `engine/tests/` | the trading kernel: decision cycle, no-loss guard, ledger, OMS, warehouse, brokers, config |
| `research/tests/` | strategies, sweep/search orchestration, metrics, ML |
| `server/tests/` | the FastAPI backend: routes, the durable queue, shards, history |
| `fidelity_gateway/tests/` | the Fidelity session/broker/recon integration |
| `tools/tests/` | ops scripts, data-prep, research probes |
| **`tests/`** (here) | only what genuinely spans two of the above as PEERS — see below |
| `tests/e2e/` | `test_pi_backtest.py` — exercises the actual Raspberry Pi deployment path |
| `tests/fixtures/` | `regression_ohlcv.csv` (35-bar synthetic OHLCV), `regression_baseline.py`, `drawdown_non_trigger_bar.csv` — the ONE shared fixture directory; every section reaches it via the dotted import `from tests.fixtures.regression_baseline import ...`, never a copy of its own |

Root `conftest.py` (repo root, sibling of `cli.py` — **not** under
`tests/`) holds the `VAI_QUEUE_DIR`/`VAI_RUN_HISTORY_DIR` isolation that
keeps a test run from writing into `output/` and corrupting an
operator's real queue or Run History. It has to live there rather than
in any one section's `tests/`, because pytest only auto-loads a
`conftest.py` for tests that have it as an ancestor DIRECTORY, and after
the split no single directory below root is an ancestor of every
section's `tests/`.

## What belongs at the root, versus in a section

A test's home is whichever top-level directory owns the module it is
PRIMARILY about — even when that module legitimately imports another
section (`research` depending on `engine` is the whole point of the
DAG, not a reason to file a strategy test at the root). The root is for
tests whose actual subject is the seam BETWEEN two sections, as peers,
not a routine dependency:

- `test_broker_contract.py`, `test_broker_selection.py` — `engine.brokers`
  and `fidelity_gateway` are two independent adapters to the same
  `LiveBroker` shape; these prove they agree / that selection dispatches
  correctly between them.
- `test_minutes_since_open_agreement.py`, `test_task_7_1_live_backtest_parity.py`
  — two INDEPENDENTLY WRITTEN implementations (a scalar one in
  `engine/`, a vectorized one in `research/`) that must produce
  identical answers; the whole reason either test exists is to catch
  the day they drift.
- `test_cli_docker_entrypoint.py`, `test_cli_backtest_window.py` —
  `cli.py` itself is the root-level entrypoint, owned by no section.
- `test_run_instructions_blocks.py`, `test_task_7_9_macro_signals_discovery.py`
  — whole-repo documentation/consumer audits that scan more than one
  section's source by design.

## The regression baseline

`fixtures/regression_baseline.py` pins a full sweep result value-for-value
and asserts **no extra columns** appear. It has caught real behavioral
drift repeatedly. If you change result columns *intentionally*, update
the baseline deliberately; do not loosen the assertion to make it pass.

## Conventions to follow when adding tests

- **SDK behavior is verified, not assumed.** Tests enumerate `alpaca-py`'s
  real `OrderStatus` enum and fail if a future release adds a value —
  don't hand-write a fake enum subset and call it coverage.
- **Clocks and sleeps are injected**, so bounded-window / retry-timing
  logic is tested deterministically, with no real delays. Don't add a
  `time.sleep` to a test to make timing work.
- **CLI behavior goes through real subprocesses** (see
  `tests/test_cli_docker_entrypoint.py`), since exit codes and
  argument parsing are what `docker run` actually exercises — don't test
  `cli.py`'s `main()` by calling it in-process if the thing under test is
  argument handling.
- **`server/live.py`'s read-only boundary is enforced by an AST-walking
  test** (`server/tests/test_server_capability.py`) — widening what it
  imports should fail there, not silently pass.
- **A module-level `import X.Y` also binds `sys.modules["X"].Y` as an
  attribute of the parent package, and Python does not undo that when a
  test later deletes or reassigns `sys.modules["X.Y"]`.** A fixture that
  saves/restores exact module OBJECTS by reference (rather than merely
  re-importing under the same name) still is not enough on its own —
  `server/tests/test_ml_optional_dependency.py`'s teardown restores the
  PARENT package's attribute too, after that gap let it leave
  `sys.modules["server"].app` pointing at a stale, test-created module
  even once `sys.modules["server.app"]` itself was correctly restored.
  It surfaced only once `test_ml_optional_dependency.py` and
  `test_server_api.py` landed in the same flat `server/tests/` directory
  and started running in the same session — a LATENT bug the old
  `tests/unit` vs `tests/integration` split happened to keep apart.
  If a fixture reloads/deletes a dotted module, restore the parent
  attribute too, not just the `sys.modules` entry.
- **Structural "there is only one of these" scanners are a pattern here,
  and they read source off disk by path — so a file move can silently
  gut OR silently over-broaden them; check which, don't assume neither.**
  The no-loss duplicate scanner and the subpackage split are the
  original example: a non-recursive `glob` matched almost nothing once
  the library stopped being flat. The tests/ → per-section split is the
  opposite failure mode: `test_no_loss_guard.py` and
  `test_task_7_9_macro_signals_discovery.py` both `rglob` the whole
  `engine/`/`research/` trees for a forbidden pattern, and once their
  own test suites moved INSIDE those trees (`engine/tests/`,
  `research/tests/`), the scan started sweeping its own test files —
  a test asserting what the forbidden text looks like now reads as an
  instance of it. Both are fixed with an explicit
  `if "tests" in path.relative_to(REPO_ROOT).parts: continue`. The live
  scanners:
  - `engine/tests/test_no_loss_guard.py` — one no-loss comparison, in `no_loss_guard.py`
  - `research/tests/test_signal_exit.py` — every sell site routes through the shared helper
  - `engine/tests/test_synthetic_bars.py` — the shared predicate isn't inlined
  - `server/tests/test_server_capability.py` — AST-walks `server/`'s read-only boundary
  - `tools/tests/test_tools_are_importable.py` — one `Escalating`, and the escalation
    formula written exactly once (`tools/harness.py`) — a non-recursive
    `glob("tools/*.py")`, unaffected by the tests/ split since
    `tools/tests/` is a subdirectory a non-recursive glob never reaches
  - `tests/test_task_7_9_macro_signals_discovery.py` — the macro-field consumer audit

  **When you move a file, grep the tests for its old path** (both
  `old/path/name.py` and the dotted `old.path.name` form — a test may
  import another test module directly, e.g. `test_broker_contract.py`
  importing fixtures out of `engine/tests/test_alpaca_broker.py`) **and
  grep production docstrings/comments for it too** — this project's
  comments routinely point a reader at "see tests/unit/test_x.py",
  and those go stale exactly the same way. Anchor `REPO_ROOT` off
  `Path(__file__).resolve().parents[N]` computed for the file's ACTUAL
  new depth (a flat `<section>/tests/x.py` is the same depth as the old
  `tests/unit/x.py` — 2 levels above the file — so N is usually
  unchanged; a file that moved to the flat root `tests/x.py`, one level
  shallower than `tests/unit/x.py`, needs N decremented by one). Prefer
  `rglob` over `glob` for a scanner that must cover a whole package —
  but exclude `tests/` explicitly once the scanner's own package
  contains one.

See `README.md`'s [Testing](../README.md#testing) section for the fuller
narrative; treat any exact test count there as approximate.
