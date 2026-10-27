# Deploying with Docker Compose

One host runs everything that has to stay up, from one file,
`docker-compose.yml`:

| service | what it is | where |
|---|---|---|
| `web` | the UI, its API and the backtest engine | `http://127.0.0.1:8000` |
| `paper-ultimate` | the Ultimate algorithm in paper, its own account and ledger | Alpaca paper |
| `backup` | every ledger and the warehouse catalogs, daily | `/workspace/backups` |
| `market-data` | every tracked fund's bars into the warehouse, daily | Alpaca market data |
| `paper` | *profile `champion`*: the champion grid, `config/paper_aggressive.yaml` | Alpaca paper, no port |
| `live` | *profile `production`*: **real money**, `config/production.yaml` | Alpaca live |
| `test`, `preflight`, `fetch-data`, `ingest`, `backtest` | *profile `tools`*: one-offs for `docker compose run --rm` | |

This replaces the Raspberry Pi deployment (`docker-compose.pi.yml`: the
paper loop and the UI on the Pi, backtests forwarded to a workstation)
and the workstation's own engine and backup jobs.

> **One loop per Alpaca account.** Nothing in the code can enforce it:
> `StateStoreLock` is a file lock and sees only its own machine. Two
> loops on one account is not a degraded mode. Both believe they are
> authoritative, and the ledger diverges from the venue. Each trading
> service here has its own env file (its account) and its own named
> volume (its ledger). **Do step 1 before step 4.**

---

## 1. Stop every other host trading these accounts

The Raspberry Pi ran the `paper` loop on the account in `.env`. On the Pi:

```bash
cd ~/workspace/volatility-ai
docker compose -f docker-compose.pi.yml stop paper
docker compose -f docker-compose.pi.yml ps          # paper: exited
```

To keep that paper book, bring its ledger with you (step 3). Keep
`down -v` away from the Pi until you have. `-v` deletes the volume, and
the volume is the ledger.

On any machine that ran it from a checkout instead:

```bash
pgrep -af 'market_hours_supervisor|cli.py live'      # expect nothing
```

---

## 2. Configure

Docker with the compose plugin (`docker compose version`). Then, in the
checkout, write `.env` with the **paper** keys. It is git-ignored and
docker-ignored; never commit it or copy it anywhere that logs its contents:

```bash
cat > .env <<'EOF'
APCA_API_KEY_ID=your_paper_key_id
APCA_API_SECRET_KEY=your_paper_secret
EOF
chmod 600 .env
```

Live keys under `paper_trading: true` authenticate fine and then trade
real money. Preflight (step 4) checks the account number the venue
reports, not what the config claims.

**Set the starting cash to the truth.** A fresh ledger seeds its cash
from `backtest.initial_cash`, not from the broker. Put the account's real
cash in the config before the first start (after any pending
liquidation has filled). A moved ledger (step 3) already has its own.

---

## 3. Moving a ledger in (optional)

A fresh ledger against an account that already holds positions stops at
reconciliation and refuses to trade, which is the right outcome. To carry
the Pi's book over instead, copy its ledger out of its volume after
step 1, then into this host's:

```bash
# on the Pi, with `paper` stopped
docker compose -f docker-compose.pi.yml run --rm --no-deps --entrypoint sh paper \
  -c 'cat /app/state/paper_ledger.db' > paper_ledger.db

# here
scp pi-host:workspace/volatility-ai/paper_ledger.db /tmp/paper_ledger.db
docker compose run --rm --no-deps --entrypoint sh \
  -v /tmp/paper_ledger.db:/in.db:ro paper -c 'cp /in.db /app/state/paper_ledger.db'
rm /tmp/paper_ledger.db
```

---

## 4. Build, verify, start

```bash
VAI_BUILD_COMMIT=$(git rev-parse --short HEAD) docker compose build
docker compose run --rm preflight
```

`VAI_BUILD_COMMIT` is optional: it records the commit in the image, which has
no `.git`, for the Live page's Deployment card. Without it the card still
shows a fingerprint of the code and whether the trader and the web server
run the same one.

Every line must be `ok`. The ones worth reading:

| check | why it is there |
|---|---|
| `paper/live key match` | Live keys in a paper config authenticate and trade real money. |
| `strategy (live)` | The live rules: a strategy built on a regime exit needs `allow_signal_exit`, a regular-session one needs `extended_hours: false`. |
| `start-up history` | The sessions of bars replayed before the first tick, fetched exactly as the loop will. A strategy that needs them will not start without them. |
| `market data (iex)` | The data feed is a separate entitlement. `sip` without a subscription fails every bar request. |
| `no OTHER host trading` | Always a warning. It is the one thing preflight cannot check; step 1 is how you satisfy it. |

Then:

```bash
docker compose up -d                 # web, paper-ultimate, backup, market-data
docker compose ps
docker compose logs -f paper
```

Expect, depending on the hour, `EXTENDED session 04:00-20:00 ET -- ...` or
`pre-market opens 04:00 ET (...)`. Then, at each session's start,
`History: N bars replayed before the first tick`.

### How the scheduling works

There is no cron. The supervisor asks Alpaca when the market opens,
sleeps until then, trades the session and exits, so holidays, half-days
and DST need nothing. `tools/docker_session_loop.sh` runs it, waits
`VAI_IDLE_SECONDS` (900), and runs it again. `restart: unless-stopped`
covers a killed container, a daemon restart and a reboot.

`docker compose stop` is a graceful stop. The loop script passes SIGTERM
to the supervisor, which stops the trading loop the way the close does:
it finishes its tick and settles what is in flight. `stop_grace_period`
leaves room for that.

### History before the first tick

Every session is a fresh process, and a strategy's state used to start
empty each morning. The champion sized the open without its 10-session
volatility windows. Ultimate's regime carried no flag for ~250 sessions,
and it could never see its own flip to turbulent. The loop now replays
recent regular-hours minute bars through the strategy first: 15 sessions
for the champion, 400 for Ultimate. It uses the loop's own feed,
adjusted like the warehouse, and includes the session so far when restarted
mid-session. See `engine/trading/live_history.py`.

---

## 5. The UI

`http://127.0.0.1:8000`: Backtesting, Run History, Live, Model research,
Warehouse. The Warehouse tab shows what the warehouse holds (each fund's bars
and how many sessions behind they are, the sweeps and simulations recorded,
sizes on disk) and the machine's state (load, CPU temperatures, memory,
disks, the queue's remaining work and its ETA, the newest backup).

### The Live tab: every deployment, and its controls

The deployments are `config/deployments.yaml`'s (ids, configs, ledgers,
control directories as `web` sees them). Each shows the state its trader
reports -- Trading, Buys paused, Winding down, Waiting for open, Waiting
for the broker (with why), Disabled, Not running -- and offers:

| Control | What happens | The deployment's config must grant |
|---|---|---|
| Pause buys | no new buys from the next tick; open lots keep exiting | (always allowed) |
| Resume buys | clears a halt, optionally re-basing the drawdown | `live.control.resume_buys` |
| Wind down | pauses buys; trading stops by itself once nothing is open | `live.control.enable_disable` |
| Disable / Enable | no session starts until enabled (open lots get NO exits meanwhile) | `live.control.enable_disable` |
| Switch / Revert / Re-warm | the algorithm, from a committed profile (`config/live_profiles/`) or, on paper, validated parameters; at the next tick, the next session, or once flat | `live.control.algorithm_changes` |
| Fresh paper ledger | archives the ledger, starts a new one with the account's cash -- disabled, paper, and a flat Alpaca account only | `live.control.ledger_reset` |
| Check connection (Fidelity) | the bridge reads the account through the extension, read-only; the result shows in its Fidelity section | (always allowed) |

**Nothing on the page changes a deployment directly.** It queues a command
in the deployment's control volume (`control_ultimate`, `control_champion`,
`control_production`); the trader applies it -- between ticks while
trading, within 15 seconds between sessions -- and the command log says when
and what came of it. The trader stays the only writer of its ledger. Real
money takes only promoted profiles, needs the deployment's id typed back for
everything but a pause, switches at most once a day, and never resets its
ledger. There is no liquidation command.

The page cannot start a stopped container (that would need the Docker
socket, which is root on the host); a deployment whose trader is not
running says so and names its service.

**There is no authentication**, by the operator's choice for a trusted LAN.
The live routes show balances, positions and cost bases, and anyone who can
reach the port can use the controls above. A page on another site, open in
your browser, cannot (cross-site requests are refused), and every command
records the name typed with it and the address it came from. That is why
it is published on loopback by default. To reach it from another machine on
a trusted LAN, for a phone or another machine's `cli.py shard`:

```bash
VAI_WEB_BIND=0.0.0.0 docker compose up -d web
```

Never port-forward it. Shards connect with
`python cli.py shard --name NAME --main THIS_HOST:8000` from a checkout of
the same commit (README, "Running sweeps on more than one machine").

---

## 6. The Ultimate algorithm in paper

`paper-ultimate` trades `config/ultimate_paper.yaml`: the research
configuration of `config/ultimate_tqqq.yaml`, regular hours only, with
its regime exit on. It needs **its own paper account**, because it is a
different book from the champion's. Create one in Alpaca's dashboard, put
its keys in `.env.ultimate` (same format as `.env`, `chmod 600`), then:

```bash
# preflight in paper-ultimate's own container: its keys, its config, its ledger
docker compose --profile ultimate run --rm --entrypoint python paper-ultimate tools/preflight.py
docker compose --profile ultimate up -d paper-ultimate
docker compose logs -f paper-ultimate
```

Its weeks in paper are the record `engine/promotion.py` needs before any
real capital. Read `config/ultimate_paper.yaml`'s header first, which
lists how live differs from the backtest.

---

## 7. Backups

`backup` runs `tools/backup_databases.py` daily at `VAI_BACKUP_AT`
(03:30 Eastern). It takes every `*.db` in the trading volumes and the two
warehouse catalogs, writes one timestamped archive to `VAI_BACKUP_DIR`
(default `/workspace/backups`, a separate disk), and keeps
`VAI_BACKUP_KEEP` (14) of them. The directory must exist and belong to
your user before the service starts, or Docker creates it owned by root
and no archive can be written:

```bash
sudo mkdir -p /workspace/backups && sudo chown "$USER:$USER" /workspace/backups
```

`cli.py backup` writes to the same place by default. `web` mounts the
directory read-only, so the Warehouse tab can flag the newest archive once
it is more than 26 hours old. SQLite is copied online, so the
loop keeps trading. A DuckDB file held open by a running sweep is skipped
and reported, never torn.

To also copy each archive off the machine (the Pi still makes a good
target), set `VAI_BACKUP_REMOTE=user@host` in the shell or in `.env`.
Then give the container an ssh key it can use non-interactively, in a
`docker-compose.override.yml`, which compose merges on its own:

```yaml
services:
  backup:
    volumes:
      - ~/.ssh:/home/runner/.ssh:ro
```

Restore, from an archive here or on the remote:

```bash
.venv/bin/python cli.py restore /workspace/backups/volatility-ai-db_....tar.gz --yes
```

`restore` verifies every sha256 against the archive's manifest before
writing, and renames what it replaces rather than deleting it.

`docker compose down` keeps the volumes. **`down -v` deletes them**, and
with them every open lot. There is no other copy except these backups.

### Market data, daily

`market-data` keeps every fund the Warehouse tab lists current
(`tools/refresh_warehouse.py`). It runs once at start and then daily at
`VAI_REFRESH_AT` (20:30 Eastern, after the extended session and SIP's
15-minute delay). A run that failed is tried again hourly. For each fund:

- **The oldest stored session is asked for again.** Adjusted prices are
  rescaled backwards by every dividend and split, so that session moves when
  one has happened. The fund's whole history is then downloaded again and
  swapped in at once; appending would leave a fake step where the old bars
  meet the new. It refuses if the download lacks a session the warehouse
  holds, and keeps the previous copy in `warehouse/staging/previous/`.
- **Otherwise the new sessions are added.** The last three stored ones are
  fetched again with them, to catch the tape's late corrections.
- **A fund the warehouse lacks** is downloaded from its start.

It writes the Parquet files directly and never opens the catalogs, so a
running sweep is never in its way, and each fund's year is replaced in one
rename, so a backtest never reads half of one. It uses `.env`'s keys for
market data only, about one request a second: the traders share that key.

```bash
docker compose logs market-data                         # what each run did
docker compose run --rm market-data --dry-run           # what it would do now
docker compose run --rm market-data --fund SPY          # one fund, now
docker compose run --rm market-data --redownload RSP    # a fund's whole history again
docker compose run --rm market-data --list              # the funds, and how each is kept
```

A new fund is added in two places: `FUNDS` in `tools/refresh_warehouse.py`
and `KNOWN_DATA` in `tools/export_ui_data.py` (a test holds them equal).

---

## 8. Operations

```bash
docker compose logs -f paper                       # follow the loop
docker compose run --rm preflight --skip-network   # the ledger, without stopping anything
git pull && VAI_BUILD_COMMIT=$(git rev-parse --short HEAD) docker compose up -d --build   # update
docker compose stop paper                          # stop trading; the ledger stays
docker compose run --rm test -q                    # the suite, inside the image
docker compose run --rm market-data --fund TQQQ    # bars through the last session, now
```

The warehouse is shared with the host. Its views store relative paths,
so `.venv/bin/python cli.py backtest ...` on the host and the `web`
container read the same files without either rewriting them.

---

## Real money

`live` (profile `production`) trades `config/production.yaml` with the
keys in `.env.production`. `Mode.LIVE` will not construct without
`engine/promotion.py`'s evidence from a passing paper run, and
`config/production.yaml` is still a placeholder (`fixed`, 5% lots). Write
the real deployment config from the paper config that earned its
promotion, then read `docs/PRE_PRODUCTION_CHECKLIST.md`.

### Fidelity

Two services (profile `fidelity`) trade a Fidelity account through the
Fidelity Bridge browser extension (`fidelity_gateway/`): every order goes
from this server over the extension into the signed-in Fidelity tab.

- **`fidelity-bridge`** is the bridge the extension connects to, up for as
  long as the deployment is (`python -m fidelity_gateway.bridge host`). The
  extension connects once and stays connected between sessions, so whether
  the connection works is known before the open, not at it. It runs on the
  host's network, so it listens on this server's address and checks the
  browser's real address against its allow list.
- **`fidelity`** is the trader: one session at a time, as the Alpaca
  traders. Each session's trading loop attaches to the bridge over a socket
  in the `bridge_fidelity` volume (`VAI_BRIDGE_SOCKET`), which only these two
  services mount -- `web` never can, so the UI cannot reach Fidelity.

Setting up:

1. `python -m fidelity_gateway.bridge keygen` -- writes
   `FIDELITY_BRIDGE_API_KEY` to `.env` and prints it once.
2. Copy `config/fidelity_live.yaml.example` to `config/fidelity_live.yaml`
   (git-ignored, and kept out of the image: it names the account). Fill in
   the account fields, set `live.fidelity.bridge.host: 0.0.0.0`, and put
   the browser's machine in `allowed_clients`.
3. In that browser: load the extension, paste the key, add this server to
   its allowed engines, sign into Fidelity. Leave "Allow trading" off.
4. `docker compose --profile fidelity up -d fidelity-bridge fidelity`.
   The Live page's Fidelity section shows the extension connecting at once.
5. Once it reads ready -- connected, signed in -- turn "Allow trading" on.
   Off again pauses every order without stopping the engine.
6. Optionally, notifications on your phone, from `fidelity-bridge`: fills
   and order problems, whether the connection is ready (and the one thing
   to fix when it is not, with a warning 15 minutes before an open), a
   Fidelity sign-out, failed account checks, sessions starting and stopping,
   the extension coming and going, refused connections.
   - `python -m fidelity_gateway.bridge keygen --notify` writes
     `FIDELITY_BRIDGE_NOTIFY_KEY` to `.env`: a key of its own, never the
     extension's.
   - In `config/fidelity_live.yaml`, set `live.fidelity.bridge.notifications`
     to `enabled: true`, `host: 0.0.0.0`, and your network's range in its
     `allowed_clients`. The bridge picks it up within 30 seconds, without
     dropping the extension.
   - Install the app from `fidelity-bridge-notifier-android/` and give it this
     server's address and that key.

   Like the bridge, the listener is up between sessions, on port 8766 of
   this server (host networking). Do not forward that port from your router;
   away from home, reach it over a VPN.

**Ready, or the one thing to fix.** The bridge checks, every second: it is
listening; the extension is connected and was heard from in the last
minute; its version; the Fidelity tab is signed in; "Allow trading" is on;
and the last read-only account check passed. The Live page shows that
chain, with the first broken link and what to do about it, and the
extension's popup says the same ("Standing by: ready" / "not ready").
The trader starts a session only once it is ready, and starts it the moment
it is -- it no longer launches a loop that can only fail. During a session,
or within 30 minutes of the open, an extension that has just connected
counts as ready only once the bridge has read the account through it: a
tab's address says "signed in" even after Fidelity's session has expired.
A read that fails is tried again every 2 minutes, so fixing the tab is
enough. A start that still cannot reach Fidelity or read the account (the
extension dropped meanwhile) is retried every minute until the session
ends, never counted as a crash and never leaving a halt, and the page says
why.

A halt in the ledger -- a pause from the page, a book that disagrees with
the account -- needs **Resume buys** on the Live page, which a Fidelity
config grants with `live.control.resume_buys: true` (you type the
deployment's id to confirm). Without it, nothing on the page can clear one.

**Check connection** on the Live page, and the bridge by itself 30 and 10
minutes before each open, reads the account through the extension --
orders, positions, settled cash -- read-only: no preview, no order.

**When something disconnects**, the section's timeline (the last 48 hours,
from `bridge/events/` in the control volume) says when, with the
WebSocket's close code, how long it stayed gone, and whether an address or
key was turned away. `docker compose logs fidelity-bridge` has the same.

**One browser at a time.** The extension connected keeps the connection.
Another browser with the extension is turned away while it answers, and
the Live page warns, naming its address -- turn the extension off there.
It takes over only if the connected one goes silent for a minute, or has
no signed-in Fidelity tab, so the browser that can trade is the one used.

**Pre-market and after-hours (`live.sessions`).** Fidelity takes limit
orders from 07:00 to 09:28 ET (05:00 Mountain) and from the close until
20:00 ET. A deployment that names its windows trades on them:

```yaml
live:
  sessions: [pre_market, regular]   # and after_hours; the day's order
  engine_lead_minutes: 30           # the engine starts 06:30 ET for the 07:00 window
  orders:                           # outside the regular session (defaults shown)
    ttl_seconds: 300                # an unfilled buy is cancelled after this
    session_close_margin_seconds: 120   # every order is cancelled this long before its window ends
    max_spread: 0.01                # a grid buy is skipped while the spread is wider
    max_premium: 0.01               # a rebalance crosses to the ask, but no further than this
  secondary_feed:                   # Fidelity's real-time quote behind Alpaca's bars
    enabled: false
```

- **Two readiness answers.** The supervisor starts the engine
  `engine_lead_minutes` before the first window. It builds the strategy and
  replays its history from Alpaca, and the Live page says *Engine ready*
  before Fidelity is asked anything. Then the engine waits for the bridge's
  "ready" in its own process -- watching the market, answering the page --
  and trades as soon as Fidelity is ready. Fidelity's own readiness is the
  connection chain below it, as before; the bridge checks the account 30 and
  10 minutes before the first *window*, not the regular open.
- **Limit orders only, and proof each one filled.** Every Fidelity ticket is
  a limit order. A buy left resting `ttl_seconds` outside the regular session
  is cancelled and decided again; every order of a window is cancelled
  before the window ends and is done only when Fidelity reports it gone. A
  resting buy holds back its cash. **Orders today** on the Live page lists
  each order's window, limit, what filled and at what price, and how it
  ended. When a window ends the trader audits it: every order gone at the
  venue and Fidelity's position equal to the ledger's, or new buys halt for
  reconciliation, naming what disagrees.
- **A regular-session strategy** (`ultimate_rsp`) may start early: it sees
  and trades the regular session alone, so `sessions: [pre_market, regular]`
  only moves its readiness to before 07:00.
- **Not yet traded on Fidelity outside the regular session.** Its pre-market
  and after-hours tickets carry fields of their own that have not been
  captured yet (`docs/research/fidelity-extended-hours.md`). Until they are,
  the engine says "Fidelity's pre_market order ticket is not known yet" and
  places nothing in those windows; nothing is guessed.
- **`secondary_feed`** reads Fidelity's quote through the extension: its bid
  and ask price the limit orders, its last trade cross-checks Alpaca (a
  minute where they disagree is skipped), and in a traded window outside the
  regular session it stands in for a minute Alpaca's free feed has no bar
  for. A quote is used only when it says when it is from; that field is not
  captured yet either, so for now it is read and journaled (`quotes/`) but
  not used. `python tools/probe_feed_coverage.py --symbol RSP --compare sip`
  says how many minutes the free feed misses.

**One process at a time.** The bridge lets one process attach: the
session's loop, or a connection check. A loop or `bridge serve` started by
hand on this server cannot take the port while `fidelity-bridge` runs, and
fails at once saying so -- running by hand means stopping both services
first (`docker compose stop fidelity fidelity-bridge`), or a second ledger
starts drifting from the account. Inside the container, a read-only check
attaches to the running bridge:

```bash
docker compose exec fidelity-bridge python -m fidelity_gateway.bridge check \
  --account <number> --account-name "<name>"
```

Started before its config exists, each service waits for the file and says
so once in its log. The bridge picks up an edited `live.fidelity.bridge`
(an address added to `allowed_clients`, say) within 30 seconds, restarting
itself with it; the trader reads the config at each session.

The Alpaca keys in `.env` give the trader prices and the market clock only;
that connection is never handed an order. Its ledger and control folder are
the `state_fidelity` and `control_fidelity` volumes, and the backup service
archives the ledger with the others.

---

## Known constraints

**Extended hours need whole shares.** Orders outside the regular session
cannot be fractional. `paper_aggressive.yaml`'s `per_lot_pct` gives about
$82 a lot, so once TQQQ trades above that, extended-hours buys are
refused. Ultimate trades regular hours only.

**The feed is `iex`; the sweeps used `sip`.** History and live ticks both
come from the live feed, so they agree with each other, but not with the
backtest's tape.

**Ultimate's regime exit is one order for the whole calm book**, a limit
`live.exit_limit_buffer` (0.5%) through the market that fills at the
market's price. One still resting a minute later is cancelled and the rest
re-offered at the new price. A backtest fills it at the bar's close.

**Lot size follows equity.** The champion's lot is `per_lot_pct` of the
equity at each session's first tick. The backtest fixes it from the
starting capital.

**No extended-hours session has ever been backtested.**
