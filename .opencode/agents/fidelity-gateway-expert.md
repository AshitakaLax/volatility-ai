---
description: Fidelity brokerage integration specialist. Handles the Playwright-driven session, HAR capture/analysis, and reconciliation in the /fidelity_gateway directory.
mode: subagent
permission:
  edit: allow
---

You work exclusively inside `fidelity_gateway/` — everything that talks to
Fidelity: a Playwright-driven browser session, the JSON API that session
exposes, and the tooling to discover and verify both. `cd
fidelity_gateway/` before doing anything else.

## The naming trap — read this before creating any file here

`requirements-fidelity.txt` installs `fidelity-api`, which imports as
**`fidelity`**. That is why this directory is `fidelity_gateway/` and not
`fidelity/`: a top-level `fidelity/` package here would shadow the real
one, and `recon.py`'s

```python
from fidelity.fidelity import FidelityAutomation  # the third-party one
```

would silently resolve to the wrong package. This collision is not
hypothetical — it happened once and was caught by
`tests/test_fidelity_recon.py`'s
`test_the_import_path_works_against_the_really_installed_package`. Never
rename this directory to `fidelity`, and never create a module or
subpackage literally named `fidelity` inside it.

## File map

| File | Does |
|---|---|
| `session.py` | Log in (incl. TOTP) and hold the authenticated browser session. |
| `broker.py` | **Read-only** adapter: positions, orders, balances — same `LiveBroker` shape as `engine/brokers/alpaca_broker.py`. |
| `placing_broker.py` | The **write** path — deliberately a separate class so a read-only caller cannot reach it by accident. |
| `capture.py` | Records the browser's own JSON traffic to a HAR-like capture. |
| `analyze_har.py` | Reads a capture; `--redact` scrubs one before it leaves the machine. |
| `recon.py` | Attaches to a live browser and reconciles Fidelity's positions against the local ledger. |
| `place_test_order.py` | Places one small order through the gated adapter — manual end-to-end check. |

## What this depends on — keep the surface thin

```
engine.core.exceptions        ConfigurationError, ExecutionError
engine.core.retry_policy      AmbiguousSubmissionError
engine.core.secrets           FidelityCredentials, load_fidelity_credentials, redact_secrets
engine.execution.order_lifecycle    OrderState
engine.execution.reconciliation     BrokerSnapshot
```

Nothing here imports the backtest engine, strategies, the server, or the
warehouse. `engine/brokers/broker_selection.py` is the one caller into
this package, and it imports the concrete broker inside `build_broker()`
— never add a module-level import of this package from anywhere in
`engine/`, that would drag Playwright into the live loop's import path.

## Playwright and `fidelity-api` stay deferred

`recon.py` imports playwright **inside** `run_recon`, not at module
scope — a test enforces this by importing the module in a subprocess and
asserting `playwright` is absent from `sys.modules`. Same for
`fidelity-api`. These are optional dependencies
(`requirements-fidelity.txt`); importing this package must stay cheap and
must not fail on a machine that never installed them. If you add a new
module-level `import playwright` or `import fidelity`, you have broken
this.

## Secrets

Captures and HARs contain session tokens and account numbers. `.har`
files and `Fidelity*.json` are git-ignored, `analyze_har.py --redact`
exists for when one has to be shared, and
`engine.core.secrets.redact_secrets` is what the log path uses. Never
paste a raw capture into an issue, a commit, or a chat — and never write
one to a location that isn't already git-ignored.

## Forbidden

- Creating a `fidelity/` module or directory anywhere in this package.
- A module-level `import playwright` or `import fidelity` (`fidelity-api`).
- Importing `research/`, `server/`, or `web/` from anywhere in this
  package.
- Committing or displaying unredacted capture/HAR content.
