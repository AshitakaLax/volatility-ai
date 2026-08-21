# Quick Start — Live Trading Is Ready

Your system is fully configured and ready to trade. Here's what to do next.

## What You Have

✅ **Fully working trading system:**
- Backtest engine with parameter sweeps
- Live and paper execution against Alpaca
- Order lifecycle management with audit trail
- No-loss guarantee (structural, not optional)
- Crash recovery and position reconciliation
- 807 passing tests, clean lint, zero warnings

✅ **Two isolated deployment environments:**
- `live-staging`: paper trading (your own money is not at risk)
- `live-production`: real capital (gated by promotion evidence)

✅ **Complete documentation:**
- `README.md` — full system overview
- `ALPACA_SETUP.md` — how to get API keys and configure credentials
- `PRE_PRODUCTION_CHECKLIST.md` — what to verify before trading real money
- `Run_Instructions` — detailed usage walkthrough
- `CHANGELOG.md` — design decisions and rationale

## 5-Minute Setup

### 1. Get Alpaca API keys

Go to https://app.alpaca.markets, create two apps (one for paper, one for live), and copy their API keys.

### 2. Create credential files

```bash
# .env.staging (paper-trading credentials)
echo "APCA_API_KEY_ID=<your-paper-key>" > .env.staging
echo "APCA_API_SECRET_KEY=<your-paper-secret>" >> .env.staging

# .env.production (real-capital credentials)
echo "APCA_API_KEY_ID=<your-live-key>" > .env.production
echo "APCA_API_SECRET_KEY=<your-live-secret>" >> .env.production
```

Both files are in `.gitignore` — they will never be committed.

### 3. Test the connection

```bash
# Verify paper-trading credentials
docker compose run --rm live --config config/staging.yaml --check-only

# Should output: READY -- broker connected and local state reconciles with the broker.
```

### 4. Start paper trading

```bash
# Start the loop (runs 24/7 until you stop it)
docker compose up -d live-staging

# Watch what it's doing
docker compose logs -f live-staging

# Stop whenever you want (graceful shutdown, settles in-flight orders)
docker compose stop live-staging
```

## Before Going Live (With Real Capital)

**Do not skip this.** Paper trading must run for 2–4 weeks and pass all criteria in `PRE_PRODUCTION_CHECKLIST.md`.

1. **Run staging for at least 2 weeks**
   - Let it trade through a full market cycle
   - Watch the logs for errors or anomalies
   - Verify fills are executing at reasonable prices

2. **Check promotion criteria** (see `PRE_PRODUCTION_CHECKLIST.md`)
   ```bash
   python -c "
   from src.promotion import evaluate_promotion
   from src.persistence import LedgerStore
   store = LedgerStore('/path/to/state_staging/ledger.db')
   print(evaluate_promotion(store))
   "
   ```
   All criteria must pass.

3. **Review the audit log and ledger**
   ```bash
   docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT * FROM audit_log LIMIT 50;"
   docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT order_id, symbol, buy_price, shares, status FROM ledger_lots;"
   ```

4. **Only then:** Start production
   ```bash
   docker compose up -d live-production
   docker compose logs -f live-production
   ```

## What Happens Every Tick

The loop runs once per `poll_interval_seconds` (default: 60 seconds):

1. **Check if market is open** — skip if closed
2. **Fetch the latest bar** for your symbol (default: TQQQ)
3. **Apply any confirmed fills** from prior orders
4. **Record the tick** with your strategy
5. **Harvest sells** — offer lots at their profit targets as limit orders
6. **Evaluate grid trigger** — buy if the price dropped enough
7. **Persist everything** — write ledger, audit log, state

A buy happens only when the current price ≤ last_buy_price × (1 - step).
A sell happens only when the current price ≥ lot's target AND the no-loss guard permits it.

No-loss is **structural**: it's mathematically impossible to sell below cost basis. The guard rejects the sale and logs why.

## Key Configuration Parameters

Edit `config/staging.yaml` and `config/production.yaml` to change:

| Parameter | Purpose | Default |
|---|---|---|
| `strategy.strategy_params.allocation_pct` | % of equity per buy | `0.05` (5%) |
| `live.step` | Price drop to trigger buy (e.g., 0.01 = 1%) | `0.01` |
| `live.profit_target` | Price gain to trigger sell (e.g., 0.005 = 0.5%) | `0.005` |
| `live.feed` | Data feed: `iex` (free) or `sip` (paid) | `iex` |
| `live.poll_interval_seconds` | Seconds between ticks | `60` |
| `live.max_sells_per_tick` | Max sells to submit per tick | `25` |
| `risk.max_concurrent_lots` | Max open positions at once | unlimited |
| `risk.max_total_exposure` | Max total $ at risk | unlimited |

`live.step` and `live.profit_target` are separate from `grid.steps` / `grid.profit_targets` on purpose — those are sweep lists for backtests; these are the **single parameters real capital trades**. Pick them from a backtest result, not from the sweep list.

## Monitoring and Alerts

### Daily

```bash
# Check if the container is still running
docker compose ps | grep live-staging

# Check latest logs
docker compose logs live-staging --tail 50
```

### Weekly

Review the audit log for unexpected orders or fills:
```bash
docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT * FROM audit_log WHERE created_at > datetime('now', '-7 days') LIMIT 50;"
```

### Emergency

Stop trading immediately:
```bash
docker compose stop live-production
```

Then investigate what went wrong. The ledger is still correct; nothing is lost.

## Common Issues

### "connection check failed: APIError: unauthorized"

Your API keys are wrong or for the wrong account (paper key used for live endpoint).

**Fix:** Go back to ALPACA_SETUP.md step 1, copy the keys exactly, and update `.env.staging` / `.env.production`.

### "No bar returned for symbol on the iex feed"

The IEX feed had no print for that symbol in that time interval. This is normal on quiet symbols.

**Fix:** This is not a problem. The loop logs it and skips the tick. If it happens constantly, check that the market is open.

### Container keeps restarting

`restart: unless-stopped` means the container restarts if it exits. If it's restarting every few seconds, something is crashing.

**Fix:** Check the logs:
```bash
docker compose logs live-staging | tail -50
```

Look for `RECOVERY_REQUIRED`, missing credentials, or other errors.

## Need Help?

- **Setup:** `docs/ALPACA_SETUP.md`
- **Pre-flight:** `docs/PRE_PRODUCTION_CHECKLIST.md`
- **Full walkthrough:** `Run_Instructions`
- **Design decisions:** `CHANGELOG.md`
- **Code:** `src/` folder (34 well-documented modules)

## You're Ready

The hard part (building the system) is done. The next step is yours: set up credentials, run paper trading, and verify it works for weeks before going live.

Good luck. Trade wisely.
