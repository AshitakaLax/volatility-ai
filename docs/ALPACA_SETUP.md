# Connecting to Alpaca's API

How to get Alpaca credentials and hand them to the deployment
(`docker-compose.yml`, [DEPLOY.md](DEPLOY.md)) without them ever entering
the repository or an image.

## Prerequisites

- An Alpaca account (free; https://app.alpaca.markets)
- `docker` with the compose plugin
- A terminal in the `volatility-ai` checkout

## 1. Create API keys, one pair per account

Each trading service trades its own account, and each account has its
own keys:

| service | account | env file |
|---|---|---|
| `paper` | paper, the champion grid | `.env` |
| `paper-ultimate` | a **second** paper account, the Ultimate algorithm | `.env.ultimate` |
| `live` | the live account, **real money** | `.env.production` |

In the Alpaca dashboard, open the account (paper accounts are listed
separately), then **API Keys** → generate. Copy the key ID and secret into
a password manager. A key pair is as good as the account's password.

Paper and live keys authenticate against different hosts, and live keys
under a paper config **trade real money**. Preflight checks the account
number the venue reports, so it catches this.

## 2. Write the env files

In the repo root, one per account, same format:

```bash
cat > .env <<'EOF'
APCA_API_KEY_ID=<paper key id>
APCA_API_SECRET_KEY=<paper secret>
EOF
chmod 600 .env
```

All of `.env*` is git-ignored and docker-ignored: credentials reach a
container only at runtime, through `env_file`. Never put them in a
config file.

## 3. Verify

```bash
docker compose run --rm preflight      # every line ok: keys, account kind, clock, data feed, history
docker compose run --rm check          # cli.py live --check-only: connect, reconcile, reach READY, exit
```

Expected from `check`:

```
READY -- broker connected and local state reconciles with the broker.
```

`RECOVERY_REQUIRED` with `unauthorized` means the keys are wrong or for
the other kind of account. Check them in the dashboard; never paste them
anywhere that logs.

For the other accounts, run the same checks in their own containers, so
they read their own keys:

```bash
docker compose --profile ultimate run --rm --entrypoint python paper-ultimate tools/preflight.py
docker compose --profile production run --rm --entrypoint python live tools/preflight.py
```

## 4. Start

```bash
docker compose up -d paper                       # champion, paper
docker compose --profile ultimate up -d paper-ultimate
docker compose logs -f paper
docker compose stop paper                        # finishes its tick, settles, exits
```

Each session the supervisor waits for the open, replays the strategy's
history, and ticks every `poll_interval_seconds` (60). Each tick it
applies confirmed fills, harvests lots at their targets, and evaluates
the grid. Watch the book in the UI's Live tab (`http://127.0.0.1:8000`).

### Real capital

Only after a paper run has produced `engine/promotion.py`'s evidence, and
after [PRE_PRODUCTION_CHECKLIST.md](PRE_PRODUCTION_CHECKLIST.md):

```bash
docker compose --profile production up -d live
docker compose logs -f live
docker compose stop live
```

`Mode.LIVE` will not construct without the evidence, whatever the config
says.

## Security

- Never commit, paste, or log a key. Rotate a pair you suspect was exposed.
- One key pair per deployment, so revoking one stops exactly one.
- Review Alpaca's API activity and the account's orders regularly.

## Troubleshooting

**`Missing required live-credential environment variable`.** The service's
env file is missing, or lacks one of the two variables.

**`No bar returned for symbol on the iex feed`.** IEX had no print that
minute, which is common outside regular hours. The tick is skipped. If it
happens constantly, check the market is open.

**`Could not prepare the strategy`.** The history the strategy replays
before its first tick could not be fetched. The loop refuses to start
blind; the supervisor tries again. Preflight's `start-up history` line
shows the fetch.

**A container restarts every few seconds.** Read
`docker compose logs <service> | tail -50` for the stage that failed:
credentials, the config, or reconciliation.
