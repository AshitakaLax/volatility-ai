# fidelity_gateway/

Everything that talks to Fidelity: a Playwright-driven browser session,
the JSON API that session exposes, and the tooling used to discover and
verify both. Self-contained on purpose — open a session **in this
directory** and you have the whole integration in front of you without
the backtesting engine, the sweep machinery, or the web stack.

```bash
pip install -r ../requirements-fidelity.txt   # playwright, fidelity-api, pyotp
python -m playwright install chromium
```

| File | Does |
|---|---|
| `session.py` | Log in (incl. TOTP) and hold the authenticated browser session. Owns `PLACE_ENDPOINTS`. |
| `broker.py` | **Read-only** adapter: positions, orders, balances. Implements the same `LiveBroker` shape `engine/brokers/alpaca_broker.py` does. |
| `placing_broker.py` | The **write** path, deliberately a separate class so a read-only caller cannot reach it by accident. |
| `capture.py` | Records the browser's own JSON traffic to a HAR-like capture. |
| `analyze_har.py` | Reads a capture; `--redact` scrubs one before it leaves the machine. |
| `recon.py` | Attaches to a live browser and reconciles Fidelity's positions against the local ledger. |
| `place_test_order.py` | Places one small order through the gated adapter — the manual end-to-end check. |

## `fidelity` (the PyPI package) is not this package

`requirements-fidelity.txt` installs `fidelity-api`, which imports as
**`fidelity`**. That is why this directory is `fidelity_gateway/` and
not `fidelity/`: a top-level `fidelity/` package here shadows it, and
`recon.py` would stop being able to do

```python
from fidelity.fidelity import FidelityAutomation  # the third-party one
```

That collision is not hypothetical — it was introduced during this
split and caught by `tests/unit/test_fidelity_recon.py`'s
`test_the_import_path_works_against_the_really_installed_package`,
which imports in a subprocess against the really-installed package.
Do not rename this directory to `fidelity`.

## What it depends on, and what depends on it

Upward, into the engine — a deliberately thin surface:

```
engine.core.exceptions        ConfigurationError, ExecutionError
engine.core.retry_policy      AmbiguousSubmissionError
engine.core.secrets           FidelityCredentials, load_fidelity_credentials, redact_secrets
engine.execution.order_lifecycle    OrderState
engine.execution.reconciliation     BrokerSnapshot
```

Nothing here imports the backtest engine, the strategies, the server or
the warehouse — and nothing in `src/` imports this at module scope.
`engine/brokers/broker_selection.py` is the one caller, and it imports the
concrete broker **inside** `build_broker()`, so choosing a broker never
drags Playwright into a process that only wanted Alpaca. Keep it that
way: a module-level import here would put the browser stack in the live
loop's import path.

## Playwright stays deferred

`recon.py` imports playwright **inside** `run_recon`, not at module
scope, and a test enforces it by importing the module in a subprocess
and asserting `playwright` is absent from `sys.modules`. The same
applies to `fidelity-api`. These are optional dependencies
(`requirements-fidelity.txt`); importing this package must stay cheap
and must not fail on a machine that never installed them.

## Secrets

Captures and HARs contain session tokens and account numbers. `.har`
files and `Fidelity*.json` are git-ignored, `analyze_har.py --redact`
exists for when one has to be shared, and `engine.core.secrets.redact_secrets`
is what the log path uses. Never paste a raw capture into an issue, a
commit, or a chat.
