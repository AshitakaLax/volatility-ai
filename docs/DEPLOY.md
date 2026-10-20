# Deploying with Docker Compose

One host runs everything that has to stay up, from one file,
`docker-compose.yml`:

| service | what it is | where |
|---|---|---|
| `web` | the UI, its API and the backtest engine | `http://127.0.0.1:8000` |
| `paper-ultimate` | the Ultimate algorithm in paper, its own account and ledger | Alpaca paper |
| `backup` | every ledger and the warehouse catalogs, daily | `/workspace/backups` |
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
docker compose build
docker compose run --rm preflight
```

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
docker compose up -d                 # web, paper, backup
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
Warehouse. The Live tab lists both paper ledgers, mounted read-only. The
Warehouse tab shows what the warehouse holds (each fund's bars and how many
sessions behind they are, the sweeps and simulations recorded, sizes on disk)
and the machine's state (load, CPU temperatures, memory, disks, the queue's
remaining work and its ETA, the newest backup).

**There is no authentication.** The live routes show balances, positions
and cost bases, and the halt (which blocks new buys; open lots keep
exiting) is reachable by anyone who can reach the port. That is why it is
published on loopback. To reach it from another machine on a trusted LAN,
for a phone or another machine's `cli.py shard`:

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

---

## 8. Operations

```bash
docker compose logs -f paper                       # follow the loop
docker compose run --rm preflight --skip-network   # the ledger, without stopping anything
git pull && docker compose up -d --build           # update
docker compose stop paper                          # stop trading; the ledger stays
docker compose run --rm test -q                    # the suite, inside the image
docker compose run --rm fetch-data --symbol TQQQ --days 30
docker compose run --rm ingest --ingest TQQQ       # then backtests see the new bars
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
