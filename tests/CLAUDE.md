# tests/

```bash
python cli.py test -q          # everything, via the CLI entrypoint
python cli.py test -k promotion
pytest tests/unit -q           # or invoke pytest directly
```

| Dir | Scope |
|---|---|
| `unit/` | fast, isolated, one module/behavior at a time |
| `integration/` | cross-module, end-to-end within the process (no real broker/network) |
| `e2e/` | `test_pi_backtest.py` — exercises the actual Raspberry Pi deployment path |
| `fixtures/` | `regression_ohlcv.csv` (35-bar synthetic OHLCV), `regression_baseline.py`, `drawdown_non_trigger_bar.csv` |

## The regression baseline

`fixtures/regression_baseline.py` pins a full sweep result value-for-value
and asserts **no extra columns** appear. It has caught real behavioral
drift repeatedly. If you change result columns *intentionally* (e.g.
adding a `strategy_id` column — see `src/CLAUDE.md`'s strategy-comparison
note), update the baseline deliberately; do not loosen the assertion to
make it pass.

## Conventions to follow when adding tests

- **SDK behavior is verified, not assumed.** Tests enumerate `alpaca-py`'s
  real `OrderStatus` enum and fail if a future release adds a value —
  don't hand-write a fake enum subset and call it coverage.
- **Clocks and sleeps are injected**, so bounded-window / retry-timing
  logic is tested deterministically, with no real delays. Don't add a
  `time.sleep` to a test to make timing work.
- **CLI behavior goes through real subprocesses** (see
  `tests/integration/test_cli_docker_entrypoint.py`), since exit codes and
  argument parsing are what `docker run` actually exercises — don't test
  `cli.py`'s `main()` by calling it in-process if the thing under test is
  argument handling.
- **`server/live.py`'s read-only boundary is enforced by an AST-walking
  test** (`tests/unit/test_server_capability.py`) — widening what it
  imports should fail there, not silently pass.
- **Structural "there is only one of these" scanners are a pattern here,
  and they read source off disk by path — so a file move silently guts
  them.** That is exactly what the subpackage split did: the no-loss
  duplicate scanner globbed `src/*.py` non-recursively, which after the
  split matched almost nothing, and it read two now-nonexistent root
  paths. Both are fixed (it now uses `rglob`, and it was verified to
  catch an injected duplicate rather than pass vacuously). The live ones:
  - `test_no_loss_guard.py` — one no-loss comparison, in `no_loss_guard.py`
  - `test_signal_exit.py` — every sell site routes through the shared helper
  - `test_synthetic_bars.py` — the shared predicate isn't inlined
  - `test_server_capability.py` — AST-walks `server/`'s read-only boundary
  - `test_tools_are_importable.py` — one `Escalating`, and the escalation
    formula written exactly once (`tools/harness.py`)

  **When you move a file, grep the tests for its old path.** These fail
  loudly *if* their paths are right and go quietly useless if not, so
  anchor new ones to `REPO_ROOT` and prefer `rglob` over `glob`.

See `README.md`'s [Testing](../README.md#testing) section for the fuller
narrative; treat any exact test count there as approximate — `src/` was
reorganized into subpackages more recently than that count was taken.
