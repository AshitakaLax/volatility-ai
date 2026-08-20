# Connecting to Alpaca's API

This guide walks through obtaining Alpaca credentials and configuring them safely for live and paper trading.

## Prerequisites

- An Alpaca account (free; sign up at https://app.alpaca.markets)
- `docker` and `docker compose` installed
- A terminal in the `volatility-ai` directory

## Step 1: Create Alpaca API Keys

### For Paper Trading (Staging)

1. Log into https://app.alpaca.markets with your credentials
2. Click your name → **Account** in the top right
3. Go to the **Apps** tab
4. Create a new app named `volatility-ai-staging` (or any name; it's for your reference)
5. Copy the generated **API Key ID** and **API Secret Key**
   - These are unique to your paper account; sharing them is equivalent to sharing your account
   - Store them somewhere safe (password manager, encrypted note) for now

### For Real Capital (Production)

Only after you have thoroughly tested on paper:

1. In the same Alpaca dashboard, create another app named `volatility-ai-production`
2. Copy its **API Key ID** and **API Secret Key**
3. **These are live credentials.** Treat them as you would a bank password.

---

## Step 2: Configure Environment Files

The system expects credentials in uncommitted `.env` files in the repo root. These files are in `.gitignore` so they will never be accidentally committed.

### Create `.env.staging`

```bash
APCA_API_KEY_ID=<your-paper-api-key-id>
APCA_API_SECRET_KEY=<your-paper-api-secret-key>
```

Example (with fake keys; use your real ones):

```bash
APCA_API_KEY_ID=PK1234567890ABCDEF
APCA_API_SECRET_KEY=abcdef1234567890secret1234567890ab
```

### Create `.env.production`

Same format, but with your **live** account credentials:

```bash
APCA_API_KEY_ID=<your-live-api-key-id>
APCA_API_SECRET_KEY=<your-live-api-secret-key>
```

---

## Step 3: Verify the Setup

### Test Staging Credentials

```bash
# Health check: connect to paper endpoint, verify auth, then exit
docker compose run --rm live --config config/staging.yaml --check-only
```

**Expected output** (if credentials are valid):

```
READY -- broker connected and local state reconciles with the broker.
```

**If credentials are wrong**, you'll see:

```
RECOVERY_REQUIRED
connection check failed: Alpaca connection failed: APIError: {"message": "unauthorized."}
```

If this happens, double-check that the keys match exactly what Alpaca showed you, with no extra spaces or copy-paste errors.

### Test Production Credentials (After Paper Success)

```bash
docker compose run --rm live --config config/production.yaml --check-only
```

This uses the same health check against the **live** Alpaca endpoint. If it passes, your production credentials are valid.

---

## Step 4: Starting the Loop

### Paper Trading (Safe to Start First)

```bash
# Start the paper-trading loop in the background
docker compose up -d live-staging

# Watch it run in real time
docker compose logs -f live-staging

# Stop it gracefully (sends SIGTERM, finishes the current tick, then exits)
docker compose stop live-staging
```

The loop will tick every `poll_interval_seconds` (default 60 seconds) and:
- Check if the market is open
- Fetch the latest bar price for the configured symbol
- Apply any confirmed fills from prior orders
- Harvest lots that have reached their profit target
- Evaluate the grid trigger and buy if needed

**Nothing trades until the grid trigger is met.** On TQQQ with the default parameters (0.01 step, 0.005 profit target), the first buy happens when TQQQ drops ~1% from your entry point. This may take days or weeks depending on market conditions.

### Real Capital (Production)

Only start this after:

1. **Staging has run for at least 1-2 weeks** and you've reviewed:
   - The audit log (in `docker compose logs live-staging`)
   - No reconciliation errors
   - Orders that actually filled (and at reasonable prices)
2. **You have promotion evidence** — a successful paper-trading run that meets `src/promotion.py`'s criteria

```bash
# Start production (real capital trading)
docker compose up -d live-production

# Watch it carefully
docker compose logs -f live-production

# Immediate stop if something goes wrong
docker compose stop live-production
```

---

## Security Best Practices

### Never

- Commit `.env.staging` or `.env.production` to git (they're `.gitignore`d, so this is hard to do by accident)
- Paste credentials in Slack, email, or any unencrypted channel
- Hardcode credentials in the config files
- Use the same credential pair for multiple machines (generate separate keys for each deployment)
- Share your Alpaca API keys with anyone

### Do

- Store credentials in a password manager or encrypted file
- Rotate credentials if you suspect they were exposed
- Review Alpaca's API key logs periodically (`Account` → **API Keys** in the dashboard)
- Keep backups of your API keys somewhere safe (not on a public cloud without encryption)
- Monitor your Alpaca account regularly — check orders, fills, and account balance

---

## Troubleshooting

### "Missing required live-credential environment variable"

The `.env` file wasn't found or is missing one of the required variables.

**Fix:**
```bash
# Verify the files exist
ls -la .env.staging .env.production

# Verify they have the right format
cat .env.staging
```

Both `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` must be present.

### "connection check failed: APIError: unauthorized"

Your API keys don't match, or they're for the wrong account (paper key used for live endpoint, etc.).

**Fix:**
1. In Alpaca's dashboard, go to **Account** → **Apps**
2. Copy the exact key and secret again (avoid copy-paste errors)
3. Update the `.env` file
4. Run the health check again: `docker compose run --rm live --config config/staging.yaml --check-only`

### "No bar returned for symbol on the iex feed"

The IEX data feed had no print for TQQQ in that time interval (common on thin symbols during pre-market or after-hours).

**Fix:**
- This is normal; the loop skips that tick and tries again at the next interval
- Watch the logs; you should see this message occasionally but not constantly
- If it happens constantly, check that the market is actually open (`market_open` flag in logs)

### Docker container keeps restarting

`restart: unless-stopped` means the container restarts indefinitely if the entrypoint exits. If `live-staging` is restarting every few seconds, it's hitting an error.

**Fix:**
```bash
# Check the logs for why it exited
docker compose logs live-staging | tail -50

# Look for RECOVERY_REQUIRED or error messages
```

Common causes: missing credentials, credential mismatch, invalid config file.

---

## Next Steps

Once staging is running successfully:

1. **Watch the audit trail** for 1-2 weeks
2. **Verify fills** — check that orders are actually executing at reasonable prices
3. **Monitor the ledger** (`docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT * FROM ledger_lots LIMIT 5;"`)
4. **Review promotion criteria** (`src/promotion.py`) to understand what constitutes a "successful" paper run
5. **Generate promotion evidence** before moving to production

---

## Alpaca Documentation

- **API Docs:** https://docs.alpaca.markets/
- **Paper Trading:** https://docs.alpaca.markets/docs/about-the-api (includes paper endpoint details)
- **Order Types:** https://docs.alpaca.markets/docs/orders (market vs limit, time-in-force, etc.)
- **Account Restrictions:** Some account types have Pattern Day Trader (PDT) restrictions or margin requirements

---

## Questions?

Check the main README's troubleshooting section, or review the examples in `Run_Instructions`.
