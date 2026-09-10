# Deploying the Alpaca paper loop to a Raspberry Pi

This moves **Alpaca paper trading** onto a Pi running Docker. The
development machine keeps backtesting and Fidelity work; it stops
trading Alpaca entirely.

> **One host trades this account at a time.** Nothing in the code can
> enforce that. `StateStoreLock` is a *file* lock — it sees only
> processes on its own machine. Two loops on one Alpaca account is not a
> degraded mode: both hosts believe they are authoritative, and the
> ledger diverges from the venue. Alpaca's server-side dedupe on
> `client_order_id` stops the same decision becoming two positions, but
> it does nothing about two ledgers disagreeing about which one owns
> what. **Do step 1 before step 5.**

---

## 1. Decommission the old host

On the development machine, in the repo:

```powershell
# Stop it running again. Already done if you have not re-enabled it.
Disable-ScheduledTask -TaskName 'VolatilityAI-PaperTrading'
Get-ScheduledTask -TaskName 'VolatilityAI-PaperTrading' | Select-Object State
# Expect: Disabled

# Nothing mid-session.
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
  Where-Object { $_.CommandLine -match 'market_hours_supervisor|cli.py live' }
# Expect: no rows
```

To remove the task rather than disable it:

```powershell
.\tools\install_paper_service.ps1 -Remove
```

Keeping `cli.py backtest`, the sweeps, and the Fidelity tools on this
machine is fine. They touch no Alpaca account.

---

## 2. Prepare the Pi

A Pi 4 or 5 with 2 GB or more, 64-bit Raspberry Pi OS. The loop is idle
most of every minute — this is a scheduling and bookkeeping workload,
not a compute one.

```bash
sudo apt update && sudo apt install -y git docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"      # log out and back in for this
docker --version && docker compose version
uname -m                             # expect aarch64
```

`aarch64` matters: `python:3.12-slim` is multi-arch and resolves to
arm64 by itself, so no platform pinning is needed. A 32-bit OS reports
`armv7l` and will fight you over wheels — reimage rather than work
around it.

---

## 3. Clone and configure

```bash
git clone https://github.com/AshitakaLax/volatility-ai.git
cd volatility-ai
git checkout feat/fidelity-broker
```

Create `.env` **on the Pi**. It is gitignored and must never be
committed or copied through anything that logs its contents:

```bash
cat > .env <<'EOF'
APCA_API_KEY_ID=your_paper_key_id
APCA_API_SECRET_KEY=your_paper_secret
EOF
chmod 600 .env
```

**Use the paper keys.** Paper and live are different credentials against
different hosts, and live keys under `paper_trading: true` authenticate
perfectly well and then trade real money. Step 6 checks this for you
against the account number the venue reports, rather than against what
the config claims.

### Set the starting cash to the truth

A fresh ledger seeds its cash from `backtest.initial_cash`, **not** from
the broker. Leave it at the default and the loop believes it has
$100,000 while the account holds something else — which mis-sizes every
lot (`per_lot_pct × initial_capital`), starts the drawdown peak in the
wrong place, and makes reconciliation flag a cash divergence on the
first tick.

Read the real figure, then set it:

```bash
docker compose -f docker-compose.pi.yml run --rm --entrypoint python paper -c "
from src.secrets import load_live_credentials
from src.alpaca_broker import AlpacaBroker
a = AlpacaBroker(load_live_credentials(), paper=True).trading_client.get_account()
print(f'cash={float(a.cash):,.2f} equity={float(a.equity):,.2f}')"
```

Put that cash figure in `config/paper_aggressive.yaml` under
`backtest.initial_cash`. Do this **after** any pending liquidation has
filled, so the number is settled rather than in flight.

---

## 4. Build

```bash
docker compose -f docker-compose.pi.yml build
```

First build on a Pi takes a while — most of it is `pip install` pulling
arm64 wheels for pandas and numpy. Both publish them, so nothing should
compile; if you see a long `Building wheel for numpy`, you are on a
32-bit OS (see step 2).

---

## 5. Verify before trading

```bash
docker compose -f docker-compose.pi.yml run --rm \
  --entrypoint python paper tools/preflight.py \
  --config /app/config/paper_aggressive.yaml \
  --state-db /app/state/paper_ledger.db
```

Every line must be `ok`. The ones worth reading rather than skimming:

| check | why it is there |
|---|---|
| `paper/live key match` | Live keys in a paper config authenticate fine and trade real money. Checked against the venue's own account number. |
| `market data (iex)` | The data feed is a **separate entitlement** from trading. `sip` without a subscription logs in fine and then fails every bar request. |
| `extended clock` | Reads the *calendar* endpoint, not the clock, so it fails independently of everything above it. |
| `no OTHER host trading` | Always a warning — it is the one thing preflight **cannot** check. Step 1 is how you satisfy it. |

---

## 6. Start

```bash
docker compose -f docker-compose.pi.yml up -d
docker compose -f docker-compose.pi.yml logs -f paper
```

Expect, depending on when you start:

```
[loop] === starting session at ... ===
[...] EXTENDED session 04:00-20:00 ET -- 372 min left, 372 ticks at 60s
```

or, outside the window:

```
[...] pre-market opens 04:00 ET (513 min)
```

The dashboard is on `http://<pi-address>:8501`. It imports no broker
code and opens the store read-only, which is why exposing it on the LAN
is reasonable. It is still a view of your positions — put it behind the
LAN only, never a port-forward.

---

## How the scheduling works

There is no cron and no systemd timer. The supervisor asks Alpaca when
the market opens, sleeps until then, sizes the session, trades it, and
exits — so holidays, half-days, and DST need no schedule changes.
`tools/docker_session_loop.sh` runs that once, waits
`VAI_IDLE_SECONDS` (default 900), and runs it again.

The wait is explicit rather than delegated to Docker's restart policy,
because the supervisor exits in about two seconds on a non-trading day.
A bare `restart: unless-stopped` would spin it hundreds of times an hour
across a weekend. `restart: unless-stopped` is still set, covering what
the in-container loop cannot: a killed container, a daemon restart, a
reboot.

---

## Operations

```bash
# Follow the loop
docker compose -f docker-compose.pi.yml logs -f paper

# Current ledger, without stopping anything
docker compose -f docker-compose.pi.yml run --rm \
  --entrypoint python paper tools/preflight.py --skip-network

# Update to the latest code
git pull && docker compose -f docker-compose.pi.yml up -d --build

# Stop trading. The ledger survives in the named volume.
docker compose -f docker-compose.pi.yml stop paper

# Back up the ledger (one-off, manual)
docker compose -f docker-compose.pi.yml run --rm --entrypoint sh paper \
  -c 'cat /app/state/paper_ledger.db' > "ledger-$(date +%F).db"
```

For a scheduled backup, `tools/backup_databases.py` does the snapshot,
archive, and off-machine copy in one script. On the **workstation** it
bundles `warehouse/*.duckdb` plus any local ledger and pushes to the Pi:

```powershell
python tools/backup_databases.py --install-daily --remote-host pi@172.16.0.137 --at 03:30
```

To back up the **Pi's own** ledger with it, run the same script inside
the container against the state volume (it uses `sqlite3`'s online
`.backup()`, so the loop keeps trading):

```bash
docker compose -f docker-compose.pi.yml run --rm --entrypoint python paper \
  tools/backup_databases.py --db /app/state/paper_ledger.db \
  --remote-host user@workstation --remote-dir volatility-ai-backups
```

`docker compose down` leaves the `state` volume intact. `down -v`
**deletes it**, and with it every open lot the deployment knows about.
There is no other copy unless you made one.

---

## Known constraints

**Extended hours needs whole shares.** Orders outside the regular
session cannot be fractional, so a lot must be worth at least one share.
`per_lot_pct` is 0.0003 — about $82 against a ~$72 TQQQ share, roughly
14% of headroom. That is not much on a 3× ETF: **if TQQQ trades above
~$82, extended-hours buys start being refused.** The lot is a fixed
dollar amount captured once at startup while the share price moves
freely, so the two drift apart by construction. Raising `per_lot_pct` is
the stopgap; sizing lots in shares rather than dollars is the fix.

**The feed is `iex`, the sweeps used `sip`.** A backtest/live mismatch
that changes how many triggers fire. Stated in the config too.

**No extended-hours session has ever been backtested.** Every recorded
result came from regular-hours bars. Those books are thinner and spreads
wider.

**SD cards wear out.** The ledger is written every tick. If this runs
for months, move Docker's data root to an SSD, or schedule
`tools/backup_databases.py` (see Operations above) so a card failure
costs a day, not the whole ledger.

---

## The web UI, and why it is split across two machines

`http://172.16.0.137:8000` — the React dashboard, served by the Pi.

The split is forced by where things physically are, not chosen:

| | runs there | because |
|---|---|---|
| **Pi** | `paper`, the Streamlit dashboard, the UI, and `/api/live/*` | The ledger lives in **this host's Docker volume**. Nothing else can read it. |
| **Workstation** (`172.16.0.134:8000`) | the backtest engine and `/api/backtest/*` | Twelve cores and every bar file — and no trading loop competing for them. The Pi has four cores and one of the things using them is placing orders. |

`web` forwards `/api/backtest/*` to `VAI_BACKTEST_UPSTREAM` and serves
`/api/live/*` itself, so **the browser still talks to one origin**: no
CORS, no second address to configure, and no way for the two halves to
disagree about which host to ask. See `server/upstream.py`.

`/api/ml/*` — the "Model research" tab — follows the identical split
and the identical env var. `data/external/` and `data/ml/` (the fetched
public series, the training parquet, the evaluation and ablation JSON)
are gitignored and live only on the workstation, and the Pi's image
never installs `requirements-ml.txt`, so there is nothing local to serve
even if it wanted to. See `server/ml_insights.py` (the workstation-side
reader) and `server/ml_upstream.py` (the Pi-side relay, GET-only —
unlike backtest there is no job to submit, only JSON someone already
generated with `tools/{fetch_market_inputs,build_ml_dataset,
evaluate_ml_features,ablate_ml_features}.py`).

**This tab is research, not a trading input.** No sizing strategy reads
it and no live loop imports it — `tests/unit/test_server_capability.py`
holds `ml_insights.py` to that the same way `live.py` is held to
read-only. See `ml_plan.md`, "Phase ML-0" for what has actually been
measured, and how weak most of it still is.

### Starting the workstation half

    python -m uvicorn server.app:app --host 0.0.0.0 --port 8000

`0.0.0.0` rather than the usual loopback, because the Pi has to reach
it. If the Pi cannot (`curl` from there returns nothing), the cause is
almost always the workstation's own firewall rather than anything in
this project.

### If the workstation is off

The UI still loads and live telemetry still works — that half is local
to the Pi. Backtest requests return **502 naming the host they could not
reach**, which is the intended behaviour: a page that silently showed
nothing would be worse.

To run sweeps on the Pi instead, clear `VAI_BACKTEST_UPSTREAM`. Note
what that costs: sweeps then share four cores with the live loop, which
is why `VAI_MAX_JOBS: "1"` is set alongside it.

### There is no authentication

The live routes read the store `mode=ro` and import no broker, and the
only write is the halt — which blocks new **buys** while open lots keep
exiting, and which any device on the LAN can trigger. That is
acceptable on a trusted network and would not be on anything routable.

### Verifying it, end to end

    python -m pytest tests/e2e/ -q

Twenty-two checks against the **running deployment**: the Pi serves the
bundle, backtests forward to the workstation, a real sweep completes and
reaches history, every offered sizing model is submittable, and a real
browser renders the page and drives a run through the form.

They **skip** rather than fail when the Pi or the engine host is not
reachable, so `cli.py test` stays green on a machine without the
hardware. Point them elsewhere with `VAI_E2E_BASE`.

They never call `/api/live/halt` — a test suite able to halt a live
deployment is a worse problem than no suite, and an AST check in the
file enforces it.
