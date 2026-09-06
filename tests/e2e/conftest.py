"""Shared setup for the end-to-end tests against a real deployment.

--------------------------------------------------------------------
THESE SKIP RATHER THAN FAIL WITHOUT THE HARDWARE

`cli.py test` runs plain pytest from the repository root, so this
directory is collected like any other. On a machine with no Raspberry
Pi -- CI, a fresh clone, a laptop on a different network -- every test
here must SKIP, not fail. A suite that goes red because someone is not
on the right LAN teaches people to ignore red.

The probe below runs once per session and skips the whole module when
the deployment is not answering.

--------------------------------------------------------------------
WHAT THESE TESTS MAY AND MAY NOT DO

The Pi runs a live paper-trading loop. These tests exercise BACKTESTING
only, which is forwarded to the workstation and touches no ledger.

They must never call /api/live/halt. That endpoint is real: it writes to
the store the loop is trading against, and a test suite that could halt
a running deployment is a worse problem than no test at all. A test in
this file asserts the suite does not name it.
"""

from __future__ import annotations

import os

import httpx
import pytest

# The deployment under test. Overridable so the same tests can point at
# a local server, which is how they are debugged.
BASE_URL = os.environ.get("VAI_E2E_BASE", "http://172.16.0.137:8000").rstrip("/")

# Generous. A sweep is forwarded from the Pi to the workstation and back,
# and the engine is the slow part -- a tight timeout here would report a
# working system as broken.
TIMEOUT = httpx.Timeout(180.0, connect=5.0)


def _probe() -> str | None:
    """Why the deployment is unusable, or None if it is fine."""
    try:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            health = client.get(f"{BASE_URL}/api/health")
    except httpx.HTTPError as exc:
        return f"{BASE_URL} is unreachable ({type(exc).__name__})"
    if health.status_code != 200:
        return f"{BASE_URL}/api/health returned {health.status_code}"

    body = health.json()
    if not body.get("capabilities", {}).get("backtest_submit"):
        return "the deployment reports it cannot accept backtests"

    # The Pi FORWARDS backtests. If the engine host is down the UI still
    # works and live telemetry is fine, but nothing here can pass -- and
    # that is a skip, not a failure of this code.
    try:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            funds = client.get(f"{BASE_URL}/api/backtest/funds")
    except httpx.HTTPError as exc:
        return f"the backtest engine is unreachable ({type(exc).__name__})"
    if funds.status_code == 502:
        return f"the backtest engine host is down: {funds.json().get('detail', '')[:120]}"
    if funds.status_code != 200:
        return f"/api/backtest/funds returned {funds.status_code}"
    if not any(fund["available"] for fund in funds.json()["funds"]):
        return "the engine host has no downloaded data to backtest"
    return None


_UNAVAILABLE = _probe()


def pytest_collection_modifyitems(items):
    """Skip everything here when the deployment is not usable."""
    if _UNAVAILABLE is None:
        return
    skip = pytest.mark.skip(reason=f"e2e: {_UNAVAILABLE}")
    for item in items:
        if "tests/e2e" in str(item.fspath).replace("\\", "/"):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as session:
        yield session
