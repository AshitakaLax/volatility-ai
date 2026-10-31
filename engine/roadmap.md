# Engine roadmap

What the engine still needs before some algorithms in the ranked list
(`docs/algorithm_ledger.md` §8C) can trade. Each item gives the gap, the
algorithms it blocks, the work, and how to know it is done. None of this
is started, so nothing here changes how anything trades today.

The single-symbol signals of the partly implemented algorithms are
already tradeable on `hf_signal_gated` (`research/strategies/signal_gated_sizing.py`).
The portfolio allocators run as backtests only, through `research/strategies/portfolio_book.py`
and `tools/portfolio_book.py`. Four algorithms are deferred until the
items below exist.

| # | Item | Unblocks |
|---|---|---|
| 1 | [A multi-asset live book](#1-a-multi-asset-live-book) | RK7, RK10, RK18, RK19, RK52, RK61, RK99, RK117, RK129, RK132, RK144, RK215, RK269 (live), X2, X3, A5 |
| 2 | [Adaptive order execution](#2-adaptive-order-execution) | RK244, RK250 |
| 3 | [Level 1 quotes and Level 2 depth from Fidelity](#3-level-1-quotes-and-level-2-depth-from-fidelity) | RK252, RK276, and the bar-level stand-ins of RK247 and RK253 |
| 4 | [Daily data feeds for the new gates and allocators](#4-daily-data-feeds-for-the-new-gates-and-allocators) | RK168 (live), RK52 |

## 1. A multi-asset live book

**Gap.** A deployment trades one symbol. Its config has one
`backtest.symbol`, the live loop asks one feed for bars, and the ledger
holds the lots of one instrument. The supervisor runs one process per
deployment. A book that rebalances across several ETFs has nowhere to
run.

**Blocks.** Every allocator in `research/strategies/allocators.py`:
- momentum and rotation: cross-sectional (RK7), state-filtered (RK10), sector rotation (RK19);
- weighting rules: low volatility (RK18), dividend yield (RK52), risk parity (RK61), equal weight (RK117), inverse volatility (RK129);
- conformal and forecast-driven: conformal risk parity (RK99), conformal allocation (RK132), alpha stacking (RK144);
- reversal and contagion: residual reversal (RK215), the Betti-0 contagion guard (RK269).

It also blocks the rotation books of `tools/rotation.py` (X2, X3, HRP/A5).

**Work.**
1. **Config.**
   - A `live.book: portfolio` section names the instruments, the allocator and its parameters, the rebalance schedule, and an optional cash instrument.
   - `BacktestConfig` validates it up front, as for every other section.
   - A portfolio config has no `grid` section, and a grid config has no `book` section.
2. **Feeds.**
   - One daily-close feed per instrument, through the existing feed abstraction.
   - The book decides on the PREVIOUS session's closes, exactly as `portfolio_book.run_portfolio` does. Live and backtest must make the same decision from the same data.
3. **Ledger.** Positions per instrument with a per-share cost basis that folds in buy costs, the way a lot does now. This should be a new table, so the grid ledger's schema is untouched.
4. **Order planner.**
   - Turn target weights into orders: sells first, then buys with the cash the sells free.
   - Every sale goes through `engine/trading/no_loss_guard.validate_sell`, and a sale that would realise a loss is skipped. This is the default and the owner's rule.
   - The only exception is a config that sets `execution.allow_signal_exit` for a declared regime exit. Such a sale is a `SIGNAL_EXIT` and is journaled with its realised loss.
5. **Supervisor and control.**
   - The supervisor needs a process kind for a portfolio deployment.
   - The operator controls need versions that make sense for a book:
     - pause rebalancing, the equivalent of pausing buys;
     - wind down, which stops rebalancing and keeps the holdings;
     - disable.
6. **Server and UI.**
   - `server/live.py` reads the new ledger table, read-only as now.
   - The Live page shows holdings, target versus actual weights, blocked sales, and the next rebalance.
   - The wire contract changes in both `server/contract.py` and `web/src/types/*.ts`.
7. **Promotion.** A paper trial for a portfolio deployment, judged by `engine/promotion.py`'s criteria on the book's equity, before real money.

**Done when:**
- A paper deployment runs `inverse_volatility` over three ETFs for a month.
- Its decisions match a `portfolio_book.run_portfolio` replay of the same sessions exactly.
- Every sale it made, or declined to make, appears in its journal.

## 2. Adaptive order execution

**Gap.** `engine/execution/limit_pricing.py` prices orders by purpose:
- a grid buy at its trigger;
- a must-fill order across the quote, within a premium cap.

Live buys skip while the spread exceeds `live.orders.max_spread`. There is no slicing and no arrival-price benchmark, and the engine never chooses between a limit and a market order by urgency.

**Blocks:**
- RK244, liquidity-aware adaptive execution;
- RK250, arrival-price adaptive limit-versus-market execution.

**Work.**
1. **Journal.** Log each order's arrival price (the mid when the decision is made), its fill, and the spread, so slippage is measured before anything changes.
2. **Policy.** An `execution.adaptive` block, off by default, which:
   - posts at the near touch;
   - escalates toward the far touch as the order ages or the price moves away;
   - slices orders above a set fraction of the bar's volume (Almgren-Chriss with the risk-aversion term set from config).
   - Research code for the pieces exists in `research/catalog/execution.py`.
3. **Safety.** A sale's limit price is still checked by the no-loss guard before it is submitted. Escalating a sale can never cross below cost.
4. **Measurement.** Compare journaled slippage with the policy on and off over a paper period.

**Done when** the slippage journal shows a measured difference, with the policy off reproducing today's orders exactly.

## 3. Level 1 quotes and Level 2 depth from Fidelity

**Gap.**
- The warehouse holds minute OHLCV bars only. There are no bid/ask quotes (Level 1) and no order-book depth (Level 2).
- `fidelity_gateway/quotes.py` reads Fidelity's real-time quote (`getquote`), but its time fields are not captured yet, so no quote is used.
- Nothing reads depth.

**Blocks:**
- RK252, order-flow imbalance, which needs Level 1;
- RK276, queue-reactive market making, which needs Level 2.

Today the bar-level stand-ins, VPIN (RK247) and the volume-clock imbalance gate (RK253), approximate flow from bars. Real quotes would replace them.

**Work, sourcing the data from Fidelity:**
1. **Discover the endpoints.**
   - Use `fidelity_gateway/recon.py --cdp-url` and `capture.py` while the Level 2 / depth view is open in the signed-in browser, to find the JSON endpoints behind it. Fidelity's quote pages and Active Trader Pro both show depth.
   - Add the read-only paths to BOTH allowlists:
     - `fidelity_gateway/session.py`;
     - the extension's `src/lib/endpoints.js`, a submodule and separate repository.
   - `test_bridge_extension.py` keeps the two in step.
   - Check Fidelity's terms of use and rate limits before polling.
2. **Finish Level 1.** Capture the bid, ask and last-trade time fields that `quotes.py` is missing, so a quote is usable.
3. **Capture depth.** A `FidelityDepth` reader in `fidelity_gateway/`:
   - top N price levels with sizes per side, polled at a fixed rate the bridge can sustain;
   - each snapshot journaled with its receive time.
4. **Store.** A quotes table and a depth table in the warehouse (`engine/warehouse/schema.py`), point-in-time by receive timestamp, so a backtest can replay only what was known.
5. **Use.**
   - RK252: compute OFI from consecutive Level 1 snapshots (`research/strategies/microstructure.ofi` already implements it) and make it a gate on `hf_signal_gated`.
   - RK276: drive `research/strategies/microstructure.QueuePositionEstimator` from depth snapshots.
   - Queue-reactive quoting also needs resting limit orders managed tick by tick. That is a market-making engine, a separate decision for the owner, and its quotes would still have to respect the no-loss guard on every sale.

**Done when:**
- A week of Level 1 and depth snapshots for TQQQ is in the warehouse.
- OFI computed from them agrees with a hand check on a sample.

## 4. Daily data feeds for the new gates and allocators

**Gap:**
- `hf_signal_gated`'s `term_gate` (RK168) reads a CSV of `date, vix, vix3m` from `term_path`. Live, someone has to keep that file current.
- The `dividend_yield` allocator (RK52) needs ex-dates and amounts. The warehouse's `market_events` table can hold them, but nothing ingests them.

**Work:**
1. **Term-structure file.** A daily job (beside the backup job in `docker-compose`) that appends the previous session's VIX and VIX3M closes to the term-structure CSV. `tools/fetch_market_inputs.py` already fetches CBOE series.
2. **Dividends.** Ingest ex-dates and amounts into `market_events` (`event_type = 'dividend'`, `event_timestamp` = ex-date). Add a reader that `tools/portfolio_book.py --dividends` can use in place of a CSV.

**Done when:**
- A paper deployment with `term_gate` on runs a week without a stale-file warning.
- `dividend_yield` runs from the warehouse alone.

## Deferred algorithms

| ID | Algorithm | Has now | Waits on |
|---|---|---|---|
| RK244 | Liquidity-Aware Adaptive Execution | Spread-gated grid buys, capped must-fill premium (`engine/execution/limit_pricing.py`) | Item 2 |
| RK250 | Arrival-Price Adaptive Limit-vs-Market Execution | Purpose-based order pricing | Item 2 |
| RK252 | Order-Flow Imbalance Cross-Sectional Alpha Predictor | Single-instrument OFI (`research/strategies/microstructure.ofi`) | Item 3 (Level 1); a cross-section also needs item 1 |
| RK276 | Queue-Reactive Market Making | Queue-position fill model (`microstructure.QueuePositionEstimator`) | Item 3 (Level 2), and an owner decision on market making |
