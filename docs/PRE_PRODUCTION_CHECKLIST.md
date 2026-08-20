# Pre-Production Checklist

Before starting `live-production` with real capital, work through this checklist. Nothing here is optional.

## Paper Trading (Staging) — 2–4 Weeks

Your paper account and the system's behavior must establish trust before real capital is at risk.

### Initial Validation

- [ ] Credentials test passes: `docker compose run --rm live --config config/staging.yaml --check-only`
- [ ] Loop starts without errors: `docker compose up live-staging` reaches `READY` state
- [ ] Initial tick succeeds: check logs for the first bar, first `record_tick`, first decision evaluation
- [ ] Market-open logic works: the loop skips ticks when the market is closed (check logs around 4pm ET or early morning)

### Order Execution

- [ ] First buy order submitted and filled
  - Verify in the logs: `BUY filled: X shares @ Y price`
  - Check Alpaca's UI: the order should appear in your paper account's order history
- [ ] Fill accounting is correct: cash and `open_lot_count` in the logs match Alpaca's position
- [ ] At least one profit-target sell is offered and filled
  - The lot reaches its target price and a limit sell is submitted
  - The sell fills and the lot is closed
- [ ] No-loss guard is working: if a sell somehow got below cost basis (should not happen), it's rejected and logged

### Stability

- [ ] Run for at least 1 continuous week
  - Observe at least one full market close/open cycle
  - Watch at least one instance of the loop skipping ticks (market closed, missing bar, rejected tick)
- [ ] No unhandled exceptions in the logs
- [ ] No persistent reconciliation errors (occasional "order not found yet" during startup is OK; repeated reconciliation failures are not)
- [ ] Restart the container at least once and verify state persists
  - `docker compose stop live-staging`
  - `docker compose start live-staging`
  - Check that the ledger is reloaded correctly and nothing is duplicated

### Audit Trail

- [ ] Export and review the audit log:
  ```bash
  docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT * FROM audit_log LIMIT 100;" | head -50
  ```
  Every order submission and fill should have an entry.

- [ ] Export the ledger:
  ```bash
  docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT order_id, symbol, buy_price, shares, profit_target, status FROM ledger_lots;"
  ```
  Closed lots should show realistic profit margins (matching your profit target).

- [ ] Review the circuit-breaker state:
  ```bash
  docker compose exec live-staging sqlite3 /app/state/ledger.db "SELECT * FROM ledger_meta WHERE key LIKE 'halt%';"
  ```
  Should be empty (or show only "not halted" if the key exists).

### Promotion Evidence

Run `src/promotion.py` (or the `evaluate_promotion` function) against your paper-trading ledger:

```bash
python -c "
from src.promotion import evaluate_promotion
from src.persistence import LedgerStore

store = LedgerStore('.state_staging/ledger.db')  # Point to your ledger
result = evaluate_promotion(store)
print(result)
"
```

**Must pass all criteria:**
- Minimum 5 days of trading
- At least 5 fills
- 0 accounting discrepancies
- 0 duplicate-order incidents
- 0 no-loss violations
- 0 reconciliation failures
- 0 unhandled exceptions

If any fails, fix the issue and run paper longer.

## Production Setup (Before First Start)

### Credentials and Configuration

- [ ] Production `.env.production` file exists and is gitignored
- [ ] Credentials are for your Alpaca **live** account (not paper)
- [ ] Test production credentials: `docker compose run --rm live --config config/production.yaml --check-only`
- [ ] `config/production.yaml` has `live.paper_trading: false`
- [ ] `config/production.yaml` step and profit_target are copied from your successful paper backtest (not just guessed)

### Capital and Risk

- [ ] You have funded your Alpaca live account with real capital
- [ ] You understand the amount at risk per lot:
  - Example: `initial_cash=100_000`, `allocation_pct=0.05` → ~$5,000 per triggered buy
  - Worst case with multiple open lots: `allocation_pct * num_lots * initial_cash`
- [ ] You have a plan to cover margin calls or forced liquidations (unlikely but possible)
- [ ] You understand that leveraged ETFs decay over time; this system does not protect against multi-year drawdowns

### Monitoring Setup

- [ ] You have a way to receive alerts if the container crashes (email, Slack hook, phone notification)
- [ ] You can access logs from wherever you are: `docker compose logs live-production -f` or cloud logging
- [ ] You have a plan to stop the container if something goes wrong: you know how to `docker compose stop live-production`
- [ ] Your Raspberry Pi has UPS or reliable power; extended outages will cause the container to restart once power is restored

### First 48 Hours of Live Trading

- [ ] Start with `docker compose up -d live-production`
- [ ] Watch the first full trading session in real time
  - Check that the first order is submitted correctly
  - Verify the fill price against Alpaca's live order book
- [ ] Restart the container and verify state persists correctly
- [ ] Check your Alpaca account's balance and open positions match what the logs report
- [ ] If anything looks wrong, stop immediately: `docker compose stop live-production`

## Ongoing Monitoring

After the first 48 hours:

- [ ] Weekly: review the audit log for unexpected patterns
- [ ] Monthly: verify the circuit breaker has not halted the loop (check logs for "HALTED")
- [ ] Quarterly: rerun `evaluate_promotion` to ensure you still meet criteria

## Emergency Stop

If anything is wrong or you want to exit immediately:

```bash
# Graceful stop (finishes current tick, settles orders, exits cleanly)
docker compose stop live-production

# Forceful stop if graceful times out (not recommended, but works)
docker compose kill live-production
```

The graceful stop is why the loop exists — in-flight orders are settled and the ledger is consistent even if the container is killed.

## Rollback Plan

If something breaks and you cannot fix it:

1. `docker compose stop live-production`
2. Switch back to staging: run paper until you have a new production config
3. Or, liquidate all open positions manually in Alpaca and disable `live.enabled` to pause the system

Nothing here is permanent; you can always pause or stop.
