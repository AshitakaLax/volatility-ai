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

# Back up the ledger
docker compose -f docker-compose.pi.yml run --rm --entrypoint sh paper \
  -c 'cat /app/state/paper_ledger.db' > "ledger-$(date +%F).db"
```

`docker compose down` leaves the `state` volume intact. `down -v`
**deletes it**, and with it every open lot the deployment knows about.
There is no other copy unless you made one.

---

## What the Pi does and does not need on disk

**The trading loop reads no data files.** It builds its state from live
ticks, so `data/` is `.dockerignore`d and never mounted into it. That is
deliberate: hundreds of MB of history has no business inside the one
container that can place orders.

**`data/earnings_releases_derived.csv` is not required by this config,**
and the loop says so rather than failing:

    No earnings event table loaded (...); event_intensity stays 0.0.

That warning is expected here. The CSV feeds `event_intensity`, whose
only consumer is `weighted_event_boost_multiplier` -- not set in
`paper_aggressive.yaml`, so it defaults to 1.0 and the whole path is an
exact no-op. The two boosts that ARE configured read static Python
lists and need no file at all:

| config | source | file needed |
|---|---|---|
| `event_day_boost_multiplier: 2.5` | `is_fomc_day_at` | no -- static list |
| `earnings_day_boost_multiplier: 1.5` | `EARNINGS_REACTION_DATES` | no -- static list |

If you later set `weighted_event_boost_multiplier`, that changes: copy
`data/earnings_releases_derived.csv` to the Pi (about 40 KB), or
regenerate it with `tools/build_earnings_calendar.py`. Until then the
warning is not telling you anything is wrong.

**The dashboard DOES need bars,** for its price chart only. It mounts
`./data` read-only. The chart is labelled recorded history rather than a
quote, and it shows whatever CSVs the Pi happens to hold -- if those are
weeks old, the chart is weeks old. The live mark on it comes from the
loop's own tick, not from the file.

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
for months, move Docker's data root to an SSD, or take the backup above
on a schedule.
