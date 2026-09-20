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
                       lands in the operator's Run History, and because
                       history is capped at MAX_RUNS, each one silently
                       evicts one of their real runs.
"""

from __future__ import annotations

import os
import tempfile

_ROOT = tempfile.mkdtemp(prefix="vai-tests-")
# Assigned, not setdefault: an operator shell that exports the real
# directories must not quietly turn the test run back into a live one.
os.environ["VAI_QUEUE_DIR"] = os.path.join(_ROOT, "queue")
os.environ["VAI_RUN_HISTORY_DIR"] = os.path.join(_ROOT, "runs")
