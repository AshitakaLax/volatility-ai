# Engine roadmap

Everything the engine still needs so that every algorithm in the ranked
list (`docs/algorithm_ledger.md` §8C, and the catalog entries beside it) can
trade. Each item gives the gap, the algorithms it blocks, the work, and how
to know it is done. None of this is started, so nothing here changes how
anything trades today.

Where things stand:

- **Tradeable now.** The single-symbol algorithms trade on the champion
  grid:
  - each has its own strategy id (`rk<N>_<signal>`, `research/strategies/library_sizing.py`);
  - `hf_signal_gated` also carries them as entry gates.
- **Backtest only.** The 53 portfolio allocators run only as backtests,
  through `research/strategies/portfolio_book.py` and `tools/portfolio_book.py`.
- **Not tradeable.** Everything else in the list is research code in
  `research/catalog/`. Its algorithms need one or more of the items below.

The items fall into three groups:

- **Within today's rules (items 1 to 9).** These stay within the owner's
  instrument rules: long-only stocks and ETFs, and losses only through the
  regime exit.
- **Outside today's rules (items 10 to 15).** These need instruments or
  exits the owner's rules exclude today. Each is an owner decision before it
  is engineering work, and each must keep the no-loss guard as the single
  place a sale is checked against cost.
- **Capacity (item 16).** Compute and operations, needed by the heavy
  research methods whichever rules apply.

| # | Item | Unblocks |
|---|---|---|
| 1 | [A multi-asset live book](#1-a-multi-asset-live-book) | the 53 portfolio-book allocators live; X2, X3, A5; every rotation and allocation entry |
| 2 | [Adaptive order execution](#2-adaptive-order-execution) | RK244, RK250, RK363, RK366, and the execution research (RK249, RK251, RK364, RK370, RK371, RK410, RK421, RK424) |
| 3 | [Level 1 quotes and Level 2 depth from Fidelity](#3-level-1-quotes-and-level-2-depth-from-fidelity) | RK252, RK276, RK306, RK322; real-flow versions of RK247, RK253 and the point-process microstructure entries |
| 4 | [Data the warehouse doesn't hold](#4-data-the-warehouse-doesnt-hold) | the 21 fundamentals, event and deal allocators, the 7 file-reading strategy ids, RK52 and RK41 |
| 5 | [A stock universe](#5-a-stock-universe) | every cross-sectional stock factor (RK5-RK58, RK207, RK209, RK214 and the rest) on real stocks |
| 6 | [News, filings and text, in time](#6-news-filings-and-text-in-time) | RK47, RK211, RK293, RK311 and the NLP entries fed from live text |
| 7 | [Learned models: training, persistence and live warm-up](#7-learned-models-training-persistence-and-live-warm-up) | the ML, RL and generative strategy ids and allocators, live |
| 8 | [Live readiness of the library strategy ids](#8-live-readiness-of-the-library-strategy-ids) | the 50 `rk<N>_<signal>` ids on a paper or live deployment |
| 9 | [Sub-minute bars and an intraday event loop](#9-sub-minute-bars-and-an-intraday-event-loop) | high-frequency, Hawkes and order-flow entries |
| 10 | [Exits that realise a loss](#10-exits-that-realise-a-loss) (owner decision) | stops and trailing exits (RK38 and others), rotation exits, signal exits beyond the regime |
| 11 | [Short selling and margin](#11-short-selling-and-margin) (owner decision) | pairs, stat arb and market-neutral baskets, long/short factors (about 40 entries) |
| 12 | [Options](#12-options) (owner decision) | options income, hedging, volatility and pricing entries (about 25) |
| 13 | [Futures, rates, FX and commodities](#13-futures-rates-fx-and-commodities) (owner decision) | carry, basis, futures trend and rates entries (RK4, RK8, RK20, RK26, RK28, RK30, RK32, RK34, RK42, RK86 and others) |
| 14 | [Market making](#14-market-making) (owner decision) | two-sided quoting and RL market makers (about 15 entries) |
| 15 | [Crypto and DeFi venues](#15-crypto-and-defi-venues) (owner decision) | RK84, RK85, RK278, RK279, RK298, RK299 |
| 16 | [Compute for heavy research methods](#16-compute-for-heavy-research-methods) | quantum, Koopman, TDA, neural-operator, generative and physics-informed entries at production cadence |

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

## 4. Data the warehouse doesn't hold

**Gap.** Today these algorithms read data the warehouse does not hold.
Fundamentals, filings, buybacks, deals, NAVs and CPI come in as CSVs
through `tools/portfolio_book.py --data name=file.csv`. They are read
point-in-time, and each table's columns are documented in
`research/strategies/allocator_library.py`. The library strategy ids read
their daily series from CSV paths in `signal_params`. Nothing fetches,
stores or refreshes any of it, so these algorithms cannot run unattended,
and a live deployment of them would read stale files.

| Table | Columns | Read by |
|---|---|---|
| fundamentals | date (published), ticker, field, value | 16 allocators: value-momentum (RK5), operating and gross profitability (RK12, RK13), investment and asset growth (RK15, RK51), shareholder yield (RK27), price-earnings momentum (RK29), intangibles value (RK31), net issuance (RK35), estimate revisions (RK40), book-to-market (RK48), accruals (RK50), low P/E (RK57), small-cap quality (RK58), SUE (RK207), PEAD (RK45); industry reversal (RK90) optionally |
| events | date, ticker, value, text | 13D filings (RK47), buybacks (RK209) |
| deals | announce, close, ticker, offer, fallback | merger arbitrage (RK39) |
| navs | date, ticker, nav | closed-end-fund discounts (RK82) |
| macro | date, value | inflation rotation (RK41, year-on-year CPI) |
| dividends | ticker, ex_date, amount | dividend yield (RK52) |
| VIX term structure | date, vix, vix3m | `rk168_vix_term`, `hf_signal_gated` `term_gate` |
| leader closes | date, close | `rk204_lead_lag`, `rk221_transfer_entropy` |
| breadth | date, advances, declines | `rk212_breadth_thrust` |
| events + control | date, value; date, close | `rk217_causal_impact` |
| pessimism | date, pessimism | `rk293_sentiment` |
| news scores | date, score | `rk311_event_sentiment` |

**Work.**
1. **Point-in-time tables.**
   - Add `fundamentals`, `corporate_events`, `deals`, `fund_nav` and `daily_series` tables to `engine/warehouse/schema.py`.
   - Key every row by when the market LEARNED it, as `market_events` already is. A restatement is a new row with a later publish date, never an overwrite.
   - Store macro series in the existing external lake with their publication `lag_days`.
2. **Sources.**
   - Choose a provider per table:
     - fundamentals and estimates, from a vendor with point-in-time history;
     - filings, from SEC EDGAR (13D, 10-Q/10-K XBRL);
     - buybacks and deals, from filings or press releases;
     - fund NAVs, from the fund sponsors or a vendor;
     - CPI, from FRED;
     - VIX and VIX3M, from CBOE (`tools/fetch_market_inputs.py`);
     - breadth, from the exchange or a vendor.
   - Record each source's licence and refresh time in `data/external/manifest.json`.
3. **Ingest.**
   - One `tools/fetch_*` and `--ingest` path per table, idempotent on the natural key like `upsert_market_events`.
   - A scheduled job (beside the backup job in `docker-compose`) refreshes each table after its publication time.
4. **Readers.**
   - Point-in-time readers in `engine/warehouse/queries.py` return exactly the frame each consumer reads today:
     - the allocators' `field_snapshot`;
     - `signal_library._Series`.
   - `tools/portfolio_book.py --data` and `signal_params` paths then become optional. The warehouse is the default, and a CSV overrides it for research.
   - The warehouse stays an optional dependency: the live loop reads through `bars.py`-style readers, never duckdb directly.
5. **Staleness.** Each reader reports the newest row's date. A live deployment refuses to start (and pauses buys mid-run) when a table it reads is older than its expected refresh, rather than trading on stale data.

**Done when:**
- Each allocator in the table and each file-reading strategy id runs a backtest from the warehouse alone, with no `--data` or `path=`.
- A paper deployment of `rk168_vix_term` runs a week with the series refreshed daily and no staleness pause.

## 5. A stock universe

**Gap.** The warehouse holds bars for a few ETFs. The cross-sectional stock
factors in `research/strategies/allocator_library.py` and the catalog need
hundreds of stocks with survivorship-free history: delisted names, index
membership by date, and corporate actions.

**Work:**
- Ingest daily, and where needed minute, bars for a universe (for example the S&P 500 or Russell 1000 by historical membership), adjusted for splits and dividends.
- Keep the membership by date in a table, so a backtest only ranks names that were in the index then.
- Record delistings, with their final prices, so dead companies stay in the history.
- Make the portfolio book scale to the universe size: vectorised weights, and rebalancing in batches.
- Item 1 must then handle hundreds of positions, with lot sizes and order counts the broker accepts.

**Done when** `momentum_12_1` and `gross_profitability` backtest over ten years of the historical S&P 500 membership.

## 6. News, filings and text, in time

**Gap.** The sentiment and event strategies read daily CSVs of scores.
Nothing collects news or filings as they are published, and nothing scores
them in time to act.

**Work:**
- Feeds:
  - SEC EDGAR's real-time filing feed (13D, 8-K, buyback announcements);
  - a licensed news feed with publish timestamps.
- Scoring:
  - the lexicon and naive-Bayes scorers in `research/catalog/technical_ml.py`, or a FinBERT-class model (item 16);
  - each scored item stored with its publish time and score time.
- Daily aggregates: pessimism and the news-score series that `rk293_sentiment` and `rk311_event_sentiment` read.
- Events: written to item 4's event table.

**Done when** a filing published at 10:00 reaches the events table, scored, within minutes, and a backtest of the same day sees it only from that time on.

## 7. Learned models: training, persistence and live warm-up

**Gap.** The learned strategy ids refit inside the strategy from replayed
bars:
- the HMMs, random forests, the triple-barrier classifier, GARCH and EVT;
- the RL exposure policies and the EMV agent;
- conformal stacking.

The generative allocators train at every rebalance. That is correct for a
backtest, but live it means:
- every session starts by replaying up to 750 sessions of minute bars to retrain;
- a model can change without anyone seeing it;
- nothing records which model made which decision.

**Work:**
1. **Model registry.**
   - Fitted models are versioned artefacts (`output/models/<strategy>/<version>`) holding their training window, data fingerprint and parameters.
   - The trader journals the model version with each decision.
2. **Scheduled refits.**
   - Refits move to a scheduled job after the close, so the live loop loads the latest version instead of refitting.
   - In a backtest the in-strategy refit stays, and it must give the same model the job would.
3. **Warm-up.**
   - `live_history_sessions()` already tells the loop how much to replay.
   - For long windows, replay daily bars, not minute bars, where the component only reads completed sessions.
4. **Determinism.** Every learner is seeded. Two runs on the same data give the same model, and the test suite pins it.
5. **Drift checks.** A refit whose out-of-sample metric falls below the last version's is held for review instead of promoted.

**Done when** `rk290_random_forest` trades on paper from a registry model, with every decision in its journal carrying the model version.

## 8. Live readiness of the library strategy ids

**Gap.** The 50 `rk<N>_<signal>` ids are registered strategies, but none
has a live profile or a measured backtest:
- `research/strategies/live_algorithm.py` has not been checked against each component's warm-up and data needs;
- the promotion gate has never seen one.

**Work:**
- **Backtests.** Run each id on TQQQ, through the sweep and walk-forward machinery, against the champion. Record the results, as `plan.md` does, before any profile exists.
- **Live checks.** `live_algorithm.build_strategy` refuses an id when:
  - its data file (item 4) is missing or stale;
  - its warm-up exceeds what the live loop can replay;
  - its model (item 7) is unregistered.
- **Promotion.** A committed profile (`config/live_profiles/`) only for ids that beat the champion out of sample, then a paper trial judged by `engine/promotion.py`.

**Done when** at least one library id that beat the champion has passed a paper trial.

## 9. Sub-minute bars and an intraday event loop

**Gap.** The engine decides once per minute bar. These need finer data or
an event-driven loop:
- Hawkes and point-process entries (RK248, RK277, RK304, RK338, RK353, RK355, RK357);
- neural point processes (RK280);
- deep microstructure models (RK275);
- intraday order-flow strategies.

**Work:**
- Ingest trade ticks or one-second bars.
- Run the decision cycle on events (a trade, a quote change) as well as on bar closes, with the same canonical order of steps.
- Keep each strategy's per-event work cheap enough to stay real-time.
- Replay the same event stream in backtests, so live and backtest stay identical.
- Item 3's quotes are part of the same stream.

**Done when** a backtest on recorded ticks and a paper run on the live stream make the same decisions on the same day.

## 10. Exits that realise a loss

**Owner decision.** Today a lot may be sold below cost only through the
regime exit (`lots_to_liquidate` with `execution.allow_signal_exit`).

**Blocks:**
- price stops and trailing stops (Chandelier exit, RK38; the stop leg of breakouts, RK43, RK68, RK77);
- rotation exits that sell a held asset to buy another;
- the portfolio book's rebalancing sales at a loss (`--allow-loss`);
- time stops.

**Work, if allowed:**
- One new `SellReason` per exit type in `engine/trading/no_loss_guard.py`. The guard stays the single place a sale is checked, and it logs each realised loss.
- A config flag per exit type, off by default, refused for live unless the strategy was researched with it.
- Journaled losses on the Live page.

## 11. Short selling and margin

**Owner decision.** The rules are long-only.

**Blocks about 40 entries:**
- pairs and cointegration (RK37, RK72-RK74, RK94);
- stat-arb baskets (RK33, RK36, RK93, RK89 and the fractional, quantum and TDA variants);
- long/short factor portfolios;
- market-neutral relative value (RK80, RK81, RK83);
- the inverse and short legs of rotation strategies.

**Work, if allowed:**
1. **Account.** A margin account with short permission at the broker. Fidelity's gateway and the extension's allowlist would both need the short-sale order types.
2. **Positions.** Negative positions in the ledger, with borrow availability and fee per name, and locate checks before an order.
3. **Risk.** Margin requirements and buying power, short-squeeze and recall handling, and a maximum gross exposure.
4. **No-loss guard.** A short's cost basis is its sale proceeds and a buy-to-cover is its exit, so the guard needs the mirror comparison, still in one place.
5. **Data.** Borrow fees and availability history for honest backtests.

## 12. Options

**Owner decision.** Options are excluded.

**Blocks about 25 entries:**
- income: covered calls, the wheel, iron condors, butterflies, calendars (RK281-RK286 and others);
- hedging: protective puts, tail hedges, dispersion (RK87, RK101, RK133, RK242, RK283);
- volatility: variance risk premium, event volatility (RK114, RK166-RK174);
- pricing and calibration: Heston, rough volatility, neural SDEs, DGM/PINN (RK240, RK303, RK377, RK379);
- deep hedging (RK324, RK329, RK352, RK391).

**Work, if allowed:**
1. **Data.** Historical option chains (bid, ask, IV, open interest by strike and expiry) and a live chain feed. Fidelity shows chains, and item 3's capture path would apply.
2. **Instruments and orders.** Option contracts in the config, multi-leg orders, and assignment and exercise handling.
3. **Accounting.** Premium, expiry, early assignment, and margin for short options.
4. **Risk.** Greeks per position and per book, with limits.
5. **No-loss guard.** Defined for option positions: a spread's basis is its net premium.

## 13. Futures, rates, FX and commodities

**Owner decision.** The rules allow stocks and ETFs only.

**Blocks:**
- carry: equity, commodity, FX and fixed income (RK4, RK28, RK30, RK32, RK42);
- futures trend (RK8, RK20);
- basis and futures relative value (RK26, RK34);
- rates curve trades (RK86, RK177, RK224);
- money markets (RK92).

**Work, if allowed:**
- A futures-capable broker.
- Contract specifications, roll schedules and continuous back-adjusted series in the warehouse.
- Margin and daily variation settlement.
- FX conversion for non-USD instruments.

## 14. Market making

**Owner decision.** Two-sided quoting needs both short inventory (item 11)
and resting orders on both sides.

**Blocks:**
- RK245, RK276, RK307;
- the RL and game-theoretic market makers (RK313, RK335, RK339, RK341, RK344, RK345, RK354, RK356, RK359, RK361).

The bid-side forms already trade on the grid (`rk246_inventory_skew`, `rk274_avellaneda_stoikov`).

**Work, if allowed:**
- Resting limit orders managed tick by tick (item 9).
- Level 2 data (item 3).
- Inventory limits, adverse-selection guards, and a fill model calibrated on the queue estimator.

## 15. Crypto and DeFi venues

**Owner decision.** Crypto is excluded.

**Blocks:**
- cross-exchange and triangular arbitrage (RK278, RK279);
- funding carry and basis (RK84, RK85);
- DEX arbitrage and liquidity provision (RK298, RK299).

**Work, if allowed:**
- Exchange connectors with custody and key management.
- For DeFi, a wallet and on-chain transaction signing, gas accounting, and smart-contract risk limits.
- 24/7 sessions in place of the NYSE calendar.

## 16. Compute for heavy research methods

**Gap.** Several method families are research code that runs on a CPU at
toy scale:
- quantum optimisation and quantum machine learning (statevector simulation, at most 14 qubits);
- Koopman and MPC;
- persistent homology;
- neural operators;
- generative scenario models;
- physics-informed networks;
- RL agents.

At production cadence and universe sizes they need more compute, and
quantum hardware is not available at all.

**Work:**
- An offline batch tier (a workstation job or the shard machines) that precomputes heavy features and models after the close and writes them to item 7's registry, so the live loop only reads them.
- An optional GPU path for the autodiff, generative and neural models. torch is not installed today.
- Quantum entries stay on simulators unless the owner chooses a cloud quantum provider. None has shown an advantage on a financial problem, so this is the last item to fund.

## Deferred algorithms (fit the rules today)

These fit the owner's rules but have no way to trade until an item above
lands. Every other entry that is not tradeable maps to items 10 to 16
through the index table at the top.

| ID | Algorithm | Has now | Waits on |
|---|---|---|---|
| RK244 | Liquidity-Aware Adaptive Execution | Spread-gated grid buys, capped must-fill premium (`engine/execution/limit_pricing.py`) | Item 2 |
| RK250 | Arrival-Price Adaptive Limit-vs-Market Execution | Purpose-based order pricing | Item 2 |
| RK252 | Order-Flow Imbalance Cross-Sectional Alpha Predictor | Single-instrument OFI (`research/strategies/microstructure.ofi`) | Item 3 (Level 1); a cross-section also needs item 1 |
| RK276 | Queue-Reactive Market Making | Queue-position fill model (`microstructure.QueuePositionEstimator`) | Item 3 (Level 2), and an owner decision on market making |
| RK306 | Micro-price / queue-imbalance signal | `microstructure.micro_price`, `depth_imbalance` | Item 3 (Level 1 bid/ask sizes) |
| RK322 | Order-book imbalance signal | `microstructure.depth_imbalance` | Item 3 (Level 2 depth) |
| RK363 | TWAP execution | Almgren-Chriss schedule research code (`research/catalog/leads.almgren_chriss`, risk aversion 0) | Item 2 |
| RK366 | Implementation shortfall / Almgren-Chriss | The same schedule; no shortfall journal | Item 2 (the arrival-price journal is its measurement) |
