# Fidelity outside the regular session: what is known, and what to capture

The engine can now run on a venue's own trading windows (`live.sessions`,
`engine/core/venue_sessions.py`). For Fidelity those are:

| Window | Eastern | Mountain |
|---|---|---|
| `pre_market` | 07:00–09:28 | 05:00–07:28 |
| `regular` | 09:30–16:00 | 07:30–14:00 |
| `after_hours` | 16:00–20:00 (close + 4 h on a half day) | 14:00–18:00 |

Every order outside the regular session is a limit order: Fidelity refuses
a market order there, and the engine never sends one in any window
(`fidelity_gateway/broker.py build_ticket` always sends `priceTypeCode: "L"`).

Each fact is read from the site's own traffic, as every other field of the
integration was, never guessed. Until each is captured, the part that
depends on it stays off.

**2026-10-27 capture** (Trader+, 08:25-08:30 ET, made with a browser
recorder that keeps only JSON replies and removes logins and account
numbers): it answers section 2, and part of section 3. It has no
`previewSrvc` or `placeSrvc` request, so section 1 is still open, and no
`getquote` reply, because Trader+ reads its quotes from
`traderplus-api/api/quotes/v1`.

## 1. The pre-market and after-hours order ticket

**What depends on it:** placing any order outside the regular session.
Until then `FidelityBroker.session_support` refuses those windows, and the
Live page says "Fidelity's pre_market order ticket is not known yet".

**How to capture it** (nothing is placed):

1. In Trader+, open DevTools → Network, and tick "Preserve log".
2. Before 09:28 ET, start a **limit** buy of 1 share of RSP far below the
   market. Choose the pre-market or extended-hours session in the ticket,
   and press **Preview** only, not Place.
3. Do the same after 16:00 ET for after-hours.
4. Export the HAR, then write a copy without the authenticating headers
   before it goes anywhere else. Bodies can still name the account, so keep
   the copy out of git:

   ```bash
   python -m fidelity_gateway.analyze_har --input capture.har --redact redacted.har
   ```

5. Compare each `trade-equity/previewSrvc` request's `orderDetails` with
   `build_ticket`'s regular one (`tifCode: "D"`). The fields that differ go
   in `fidelity_gateway/broker.py EXTENDED_TICKET_FIELDS["pre_market"]` and
   `["after_hours"]`, with a test pinning them -- transcribed by hand with a
   placeholder account, never the capture itself (the repository is
   public).

Also note what Fidelity answers to a **market** order outside the regular
session. The engine never sends one, but the answer belongs in the record.

**From the 2026-10-27 capture, and still to confirm:** Fidelity's own record
of an order names its window as `marketSessionCode`. It reads `"P"` for a
pre-market order and `"S"` for a regular one in `trade-equity/orderStatus` and
in the cancel and replace parameters, and `"Premarket"` and `"Standard"` in
`transactions/pending`. `tifCode` is `"D"` in both. So the pre-market ticket
most likely carries `marketSessionCode: "P"` beside `tifCode: "D"`, the same
flat shape `build_ticket` sends. A capture of the Preview request itself
confirms it. Trader+'s order ticket did not record one, so use the
classic trade ticket (Trade → Stocks/ETFs) with the recorder on. The
after-hours code is not known at all.

## 2. What happens to an order at the end of its window

**What depends on it:** nothing yet. The engine already cancels every order
`live.orders.session_close_margin_seconds` before its window ends, and
counts it done only when Fidelity reports it gone. It also audits each
window when it ends. Knowing Fidelity's own rule says whether an order the
engine could not cancel would still be working in the next window.

**Answered by the 2026-10-27 capture.** A pre-market Day order expires at
the end of the pre-market: its `expirationDate` (`transactions/pending`,
epoch ms) and `gtcExpDatetime` (`orderStatus`, epoch s) both read 09:28:00
ET. A regular-session Day order's reads 16:00:00 ET. So an order the engine
failed to cancel does not carry from the pre-market into the regular
session. `transactions/pending` lists the day's orders in every state, each
with its `marketSessionCode`. The engine's reader (`derive_order_state`)
reads the pre-market ones as it does the rest: open is ACCEPTED, "Filled at
$x" is FILLED with `qtyExec` and `avgExecPrice`, and "Verified Canceled" is
CANCELED. A marketable pre-market limit filled within seconds.

## 3. When a quote is from, before the open

**What depends on it:** the second data source (`live.secondary_feed`):
Fidelity's quote pricing limit orders, cross-checking Alpaca, and filling a
minute Alpaca's free IEX feed has no bar for. Until then
`fidelity_gateway/quotes.py TIME_FIELDS` is empty, so every quote's `at` is
None and the feed uses none of them. Quotes are still journaled (`quotes/`).

**What Trader+'s own quote showed (2026-10-27, `traderplus-api/api/quotes/v1`,
a GET with `?symbol=`):** in the pre-market, `bidPrice`/`askPrice` moved
with this morning's `bidTime`/`askTime` (`"8:24:45AM"`, Eastern, beside
`quoteDate` `"10/27/2026"`). Meanwhile `lastPrice` stayed at yesterday's
close, with `lastDate` yesterday and `lastTime` `"4:10:00pm"`, even after
pre-market trades had printed. `volume` did count the pre-market. So a
quote's time and its last trade's time are separate questions, and the
engine now treats them so (`Quote.at` and `Quote.last_at`): a last trade is
used only when the reply dates it. That endpoint is on both allowlists, but
the extension's fetch is POST-only, so reading it would need a GET in the
extension first.

**How to capture getquote:** at about 08:00 ET, with the recorder on, open
RSP in the classic trade ticket, then export the `trade-equity/getquote`
reply. Three questions:

- Which field gives the bid and ask's time, and in what form? It goes in
  `TIME_FIELDS` as `(field, "epoch_ms" | "epoch" | "iso")`, and the last
  trade's in `LAST_TIME_FIELDS`.
- Is `LAST_PRICE` the pre-market's last trade, or yesterday's close with
  the extended price in another field? If it is the close, the extended
  field replaces it in `FidelityQuotes.quote`.
- Is there a time for the last trade apart from the time of the bid and
  ask? RSP trades in about one pre-market minute in seven (section 4), so a
  quote can be seconds old while its last trade is ten minutes old. A gap
  bar is a trade, so it should carry the trade's time.

## 4. How often Alpaca's free feed has a bar in each window

This needs no capture:

```bash
python tools/probe_feed_coverage.py --symbol RSP --sessions 10 --compare sip
```

It needs `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` in the environment. It
prints, per session, the minutes with a bar in each window on IEX (and SIP
in brackets). SIP's bars are the warehouse's, so they are what every
backtest ran on.

**Measured 2026-10-27, the ten sessions 2026-10-13 to 2026-10-26** (minutes
with a bar, of the minutes in Fidelity's windows):

| Fund | IEX pre-market | IEX after-hours | SIP pre-market | SIP after-hours |
|---|---|---|---|---|
| RSP | 0 of 1,480 (0%) | 3 of 2,400 (0.1%) | 224 of 1,480 (15%) | 237 of 2,400 (10%) |
| SPY | 4.7% | 1.0% | 98% | 89% |
| TQQQ | 4.2% | 1.6% | 100% | 98% |

What it means:

- **Alpaca's free IEX feed has, in practice, no bars outside the regular
  session**, for any of the three. On it, a deployment trading the
  extended windows would get every extended-hours price from the second
  source; Alpaca would be first only in name. Keeping Alpaca first there
  needs its real-time SIP feed, a paid market-data plan.
- **RSP itself barely trades outside the regular session.** On SIP, per
  day: 07:00-08:30 has about 11 minutes with a trade and 12,500 shares;
  08:30-09:28, after the releases, about 11 minutes and 11,800 shares. That
  compares with 8.2 million shares in the regular session. 17:00-20:00
  adds about 13 minutes and 6,600 shares. 16:00-17:00 shows about 400,000,
  but that is mostly closing-auction prints reported after the bell.
- SPY and TQQQ trade in almost every extended minute: TQQQ about 2.8
  million shares in the pre-market each day, 0.8 million of them in
  08:30-09:00.

So a researched RSP strategy for these windows would see a bar in one
pre-market minute in seven, and its limit orders would meet little volume
and a spread nothing in the warehouse records.
