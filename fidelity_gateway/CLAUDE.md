# fidelity_gateway/

Everything that talks to Fidelity: a Playwright-driven browser session,
the JSON API that session exposes, and the tooling used to discover and
verify both. Self-contained on purpose — open a session **in this
directory** and you have the whole integration in front of you without
the backtesting engine, the sweep machinery, or the web stack.

```bash
pip install -r ../requirements-fidelity.txt   # playwright, websockets; fidelity-api + pyotp only for recon's legacy modes
```

Nothing on a working path logs in. Two ways reach the Fidelity tab you
signed into by hand:

- **The browser-extension bridge** (preferred): the Fidelity Bridge
  extension connects to `bridge/`'s server. No launch flags, no second
  profile. See "The browser-extension bridge" below.
- **A remote-debugging port**: attach over CDP to a Chromium browser you
  started with `--remote-debugging-port=9222` and its own
  `--user-data-dir`.

Only `recon.py`'s legacy launched-browser modes log in, and Fidelity
refuses those. Run the scripts as modules from the repo root:

```bash
python -m fidelity_gateway.bridge check --account <number> --account-name "<name>"
python -m fidelity_gateway.place_test_order --account <number> --check-only [--bridge]
python -m fidelity_gateway.recon --cdp-url http://localhost:9222 --account <number> \
    --i-understand-this-logs-into-my-real-brokerage-account
```

| File | Does |
|---|---|
| `session.py` | Issues every JSON call with `fetch()` inside the page you are signed into, replaying the auth headers it sniffs per backend. Owns the read-only / preview / place endpoint allowlists that gate every request. Never logs in. |
| `broker.py` | **Preview-only** adapter: quotes, previews (which mint a confNum and commit nothing), orders, positions, settled cash. The same `LiveBroker` shape as `engine/brokers/alpaca_broker.py`; its `submit_*` methods stop at the preview. |
| `placing_broker.py` | The **write** path: places and cancels real orders behind five explicit gates, journals each confNum before committing, and reads the journal back at construction. A separate class so a preview caller cannot reach it by accident. |
| `capture.py` | Records the browser's own JSON traffic to a HAR-like capture. |
| `analyze_har.py` | Reads a DevTools HAR export; `--redact` scrubs one before it leaves the machine. |
| `recon.py` | Reconnaissance, not reconciliation: with `--cdp-url`, records your browser's traffic while you use it. Its launched-browser modes are kept for the record; Fidelity refuses them. |
| `place_test_order.py` | Places one small order through the gated adapter — the manual end-to-end check. `--check-only` is the recovery report; `--bridge` goes through the extension instead of a debugging port. |
| `bridge/` | The browser-extension route. `BridgeServer` (WebSocket, client allow/block lists, HMAC handshake), `BridgePage` (stands in for a Playwright page, so `FidelitySession` is unchanged), the API key in `.env`, and `python -m fidelity_gateway.bridge keygen \| serve \| check`. |
| `tests/` | This section's own suite. `test_broker_selection.py`/`test_broker_contract.py` (the engine↔fidelity_gateway seam) live in the ROOT `tests/` instead — see `tests/CLAUDE.md`. |

## The browser-extension bridge

The extension is its own repository (`AshitakaLax/fidelity-bridge-chrome-extension`),
checked out here as the submodule `fidelity-bridge-chrome-extension/`
(`git submodule update --init`). It is separate on purpose: what the
extension allows cannot be changed from this repository. Its README
covers installing it; `PROTOCOL.md` there is the wire protocol both sides
implement.

- **Two independent locks on orders.** `FidelitySession`'s endpoint
  allowlist here, and the extension's own
  (`fidelity-bridge-chrome-extension/src/lib/endpoints.js`). The
  extension's previews and orders are each a switch in its settings, off
  by default. `test_bridge_extension.py` fails if the two allowlists stop
  naming the same paths.
- **The API key** is `FIDELITY_BRIDGE_API_KEY`, read from the environment
  or `.env`, and never accepted on a command line. `keygen` appends it to
  `.env` and refuses to replace an existing one. You paste the same key
  into the extension's welcome form.
- **Addresses.** The server refuses clients outside `--allow-client`
  (default: this computer) or on `--block-client`. The extension refuses
  engines outside its own allowed and blocked lists.
- **Nothing is ever sent as a script.** `BridgePage.evaluate` accepts
  only `session.FETCH_SCRIPT` and turns it into the extension's fixed
  `fetch` command.
- **Refused versus possibly sent.** A refusal made before anything was
  sent is a `BridgeRefusal`, which is a `ConfigurationError`. Anything
  that might have reached Fidelity is a `BridgeError`. `FidelitySession`
  passes `ConfigurationError` through unwrapped, so the placing broker
  calls only the second kind ambiguous.
- **Tests.** The protocol and address-policy tests reproduce the
  extension's shared vectors (`tests/vectors/`).
  `test_bridge_extension.py` runs the extension's real JavaScript under
  Node against a live `BridgeServer`; it skips when Node or the submodule
  is missing.

## Live trading through the bridge

`python cli.py live` with `live.broker: fidelity` gets its broker from
`live.py`'s `connect_live`:
1. Start the bridge and wait for the extension.
2. Build a session with order endpoints allowed exactly when
   `live.fidelity.dry_run` is false.
3. Build the broker through `engine/brokers/broker_selection.build_broker`.

Prices and the market clock still come from Alpaca (a clock-only,
paper-endpoint connection). `config/fidelity_live.yaml.example` is the
template.

- **Real orders need it all stated** in the config:
  - `dry_run: false`
  - `paper_trading: false`
  - `allowed_symbols` including `backtest.symbol`
  - a positive `max_order_value`
  - the account and its name

  `build_broker` refuses on any gap, and refuses a session that cannot
  place orders. Nothing falls back to previewing.
- **`dry_run: true` runs `--check-only` only.** A preview never fills,
  so the loop would track phantom orders forever.
- **Waits versus halts.** `FidelitySessionError` (signed out, transport
  down) and `BridgeUnavailable` (no extension, no Fidelity tab, trading
  switched off) are `BrokerUnavailableError`. The loop skips that tick,
  persists what it had applied, and tries again. Only
  `AmbiguousSubmissionError` halts.
- **The snapshot is scoped to `backtest.symbol`.** The account may hold
  other investments. Reconciliation still stops on the deployment's own
  symbol held by hand.
- **Limit prices round directionally**: buys down, sells up, as
  `AlpacaBroker` does.

## `fidelity` (the PyPI package) is not this package

`requirements-fidelity.txt` installs `fidelity-api`, which imports as
**`fidelity`**. That is why this directory is `fidelity_gateway/` and
not `fidelity/`: a top-level `fidelity/` package here shadows it, and
`recon.py` would stop being able to do

```python
from fidelity.fidelity import FidelityAutomation  # the third-party one
```

That collision is not hypothetical — it was introduced during this
split and caught by `fidelity_gateway/tests/test_fidelity_recon.py`'s
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
the warehouse — and nothing in `engine/` imports this at module scope.
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
