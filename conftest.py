"""Session-wide isolation from this machine's real server state.

Lives at the REPO ROOT, not under tests/, on purpose: pytest loads a
conftest.py for every test file that has it as an ancestor directory,
and after the tests/ -> per-section split (engine/tests/, research/tests/,
server/tests/, fidelity_gateway/tests/, tools/tests/, plus tests/ itself
for genuine cross-boundary tests), no single directory below root is an
ancestor of all of them. This one is, so it is the only place this
isolation can live and still apply everywhere `server.jobs`/`server.history`
might get imported -- which per the engine/research DAG should only be
server/tests/, but a root cross-boundary test (tests/test_cli_docker_entrypoint.py
drives the server via subprocess) also benefits from it.

Set at import, before any test module imports server.*, so it holds for
the module-global job queue that integration tests drive through
TestClient as well as for anything constructed later. Individual tests
still repoint these with monkeypatch.setenv when they need a directory
of their own; that overrides this for the test and restores it after.

  VAI_QUEUE_DIR        server/jobs.py persists pending runs and their
                       checkpoints here. Left at its default, a run a test
                       queued would be written into output/queue/ -- and
                       the next REAL server start would restore it and
                       spend engine time on it.
  VAI_RUN_HISTORY_DIR  server/history.py archives completed runs here.
                       Left at its default, every test run that completes
                       would land in the operator's Run History.
  VAI_RECORD_WAREHOUSE off: server/backtest.py records every configuration
                       of a run in the warehouse, and several server tests
                       run against the REAL one's bars -- they would write
                       their configurations into its sim_results.duckdb.
                       Tests of the recording turn it on against a
                       warehouse of their own.
  VAI_EXTERNAL_DIR     research/strategies/risk_governor.py reads a
                       strategy's outside series here, and a strategy with
                       the governor on refuses to be built without them
                       (config/live_profiles/daily-ultimate-governed-tqqq
                       is validated by building it). data/external/ is
                       downloaded, so a clean checkout has none and a
                       working one has whatever was fetched last: neither
                       is a fixture. This is a flat series for every input
                       a signal names, over fixed dates -- no warning is
                       ever raised from it.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta

_ROOT = tempfile.mkdtemp(prefix="vai-tests-")
# Assigned, not setdefault: an operator shell that exports the real
# directories must not quietly turn the test run back into a live one.
os.environ["VAI_QUEUE_DIR"] = os.path.join(_ROOT, "queue")
os.environ["VAI_RUN_HISTORY_DIR"] = os.path.join(_ROOT, "runs")
os.environ["VAI_RECORD_WAREHOUSE"] = "0"
os.environ["VAI_EXTERNAL_DIR"] = os.path.join(_ROOT, "external")


def _write_flat_external_series(directory: str) -> None:
    from research.strategies.risk_governor import SIGNALS

    os.makedirs(directory, exist_ok=True)
    first = date(2024, 1, 1)
    days = [first + timedelta(days=n) for n in range(730)]
    rows = "".join(f"{day} 21:00:00+00:00,100.0\n" for day in days if day.weekday() < 5)
    for key in sorted({key for signal in SIGNALS.values() for key in signal.inputs}):
        with open(os.path.join(directory, f"{key}.csv"), "w", encoding="utf-8") as handle:
            handle.write("timestamp,close\n" + rows)


_write_flat_external_series(os.environ["VAI_EXTERNAL_DIR"])
