# fidelity-bridge-notify/v1

How an app hears the Fidelity Bridge's notifications. The bridge's half is
`fidelity_gateway/bridge/notify_server.py` and `notify_protocol.py` in
[volatility-ai](https://github.com/AshitakaLax/volatility-ai); this app's is
`core/src/main/kotlin/.../core/Protocol.kt` and `BridgeClient.kt`. Both
reproduce the values in `core/src/test/resources/vectors/notify-protocol-v1.json`,
which is what keeps them in agreement. Change either side, and both test
suites must still pass against those vectors.

It is the design of the extension's `fidelity-bridge/v1`, with its own labels,
so nothing proved on one connection counts on the other.

## Where

A WebSocket at `ws://<host>:<port>/notifications`, 8766 by default, separate
from the extension's socket on 8765. The bridge host -- volatility-ai's
always-on `fidelity-bridge` service -- runs it whenever
`live.fidelity.bridge.notifications` is enabled, between trading sessions
too. `python -m fidelity_gateway.bridge serve --notify` runs one beside a
bare bridge, to try it out. The bridge refuses, before any handshake:

- a client address outside its allowed list, or on its blocked list (HTTP 403);
- a request with a web page's `Origin` (`http://…`, `https://…` or `null`) (HTTP 403);
- any other path (HTTP 404).

**The trader notifier** speaks the same protocol for deployments no bridge
sees -- volatility-ai's Alpaca deployments
(`fidelity_gateway/bridge/trader_notifier.py`, the `trader-notifier`
service). It reads each trader's status, fill and order journals and ledger,
and serves one stream per deployment from one port, 8767 by default:
`/notifications/<deployment>` for each, and `/notifications` for the first.
Its key is `VAI_NOTIFIER_KEY` (`keygen --notifier`). An app keeps one
connection per account: each address and key is an account of its own.

## The key

`FIDELITY_BRIDGE_NOTIFY_KEY`: 32 to 256 characters of `A-Z a-z 0-9 . _ ~ + / = -`.
`python -m fidelity_gateway.bridge keygen --notify` writes it to the bridge's
`.env` and prints it once. It must not be the extension's key, and the bridge
refuses to start if it is: that key lets whoever holds it pose as the
extension. **The key never crosses the wire.**

## Handshake

`HMAC(k, m)` is HMAC-SHA256 of the UTF-8 bytes of `m` under the UTF-8 bytes
of `k`; `hex` is lower-case. Nonces are 32 random bytes as 64 lower-case hex
characters.

1. Bridge → app, plain JSON:
   ```json
   {"type": "challenge", "protocol": "fidelity-bridge-notify/v1", "nonce": "<N_b>"}
   ```
2. App → bridge, plain JSON:
   ```json
   {"type": "auth", "protocol": "fidelity-bridge-notify/v1", "nonce": "<N_a>",
    "proof": "hex(HMAC(key, 'fidelity-bridge-notify/v1|app-proof|<N_b>|<N_a>'))",
    "since": {"stream": "<stream>", "id": 41},
    "client": {"name": "Notifier on Pixel 8", "version": "0.1.0"}}
   ```
   `since` is the last notification the app saw, or `null`. `client` is only
   for the bridge's log.
3. Bridge → app, plain JSON, one of:
   ```json
   {"type": "welcome", "proof": "hex(HMAC(key, 'fidelity-bridge-notify/v1|bridge-proof|<N_b>|<N_a>'))"}
   {"type": "denied", "reason": "bad_proof" | "too_many_apps" | "stopping"}
   ```
   The app checks the bridge's proof too, in constant time. A bridge that
   cannot prove the key is not believed. `bad_proof` means the key is wrong,
   so the app stops trying until its settings change. The other refusals
   clear on their own.

Both sides then derive this connection's sealing key:
`session = HMAC(key, 'fidelity-bridge-notify/v1|session|<N_b>|<N_a>')` (raw bytes).

## Sealed messages

Every later frame, in both directions, is an envelope:

```json
{"seq": 1, "payload": "<a JSON object, as text>", "mac": "hex(HMAC(session, '<sender>|<seq>|<payload>'))"}
```

`sender` is `bridge` or `app`. Sequence numbers start at 1 in each direction
and must arrive exactly in order. The MAC covers the payload *text*, so the
two sides never have to agree on how to serialise JSON. A frame that fails
any check closes the connection. Over a plain `ws://`, this is what stops
anyone else on the network from forging a "Sold" notification. They can
still read the messages: use a VPN to reach the bridge from outside your own
network.

## Bridge → app

- **hello**, always first:
  `{"type": "hello", "protocol": "…", "stream": "<random per bridge run>", "events": ["buy", …], "status": {…}, "backlog": 3, "account": {…}}`
  - `backlog` is how many `replay: true` notifications follow, so an app
    knows where catching up ends: the app announces only the latest of them
    (of the kinds it shows) with a count of the rest, and lists them all. A
    bridge older than this sends none; the app then takes catching up to end
    at the first message that is not a replay, or a second after the last.
  - `account` says what this stream is about, each field optional:
    ```json
    {"id": "paper-ultimate", "label": "Ultimate (paper)", "broker": "alpaca",
     "paper": true, "symbol": "TQQQ"}
    ```
    `broker` is `fidelity` or `alpaca` (others may come: show them). A
    bridge older than this sends no `account`: it is Fidelity. The app
    colours an account by it, yellow for Alpaca and green for Fidelity.
- **notification**:
  `{"type": "notification", "notification": {"id", "stream", "kind", "severity", "title", "body", "at", "data"}, "replay": true?}`
  - `id` counts from 1 within `stream`. A test notification has id `0`, and
    the bridge never keeps it.
  - `kind`: `buy`, `sell`, `order_update`, `order_problem`, `engine`,
    `session`, `readiness`, `fidelity_signin`, `account_check`, `connected`,
    `disconnected`, `trading_switch`, `refused`, `bridge`, `window`, or
    `test`. The vectors' `eventKinds` is the list both sides check. Unknown
    kinds may come later: show them.
  - `severity`: `info`, `warning` or `critical`. `at` is ISO-8601 UTC.
    `data` carries the details (an order's `confNum`, `symbol`, `side`,
    `qty`, `filledQty`, `avgPrice`, …).
  - `replay: true` marks one the app missed, sent right after `hello`. With
    `since` from the same stream, those are the ones after it. From another
    stream (the bridge restarted), or with no `since`, they are everything
    it kept (up to 200). An app that sent no `since` should treat replays as
    history rather than news.
- **status**, whenever it changes:
  ```json
  {"type": "status", "status": {
    "extension": {"connected": true, "since": "…", "disconnectedAt": null, "disconnectCode": null,
                  "version": "0.7.0", "advice": null, "trading": true, "previews": true,
                  "fidelity": "signed_in"},
    "engine": {"mode": "live", "state": "running", "detail": "trading", "symbol": "TQQQ",
               "lastTickAt": "…", "updatedAt": "…", …},
    "bridge": {"ready": false, "blocking": "fidelity",
               "summary": "Fidelity tab: Fidelity signed you out",
               "fix": "sign in to Fidelity again in that browser",
               "items": [{"id": "bridge", "label": "Bridge", "state": "ok", "detail": "…", "fix": null}, …],
               "listening": true, "listenError": null, "mode": "live", "deployment": "fidelity",
               "symbol": "TQQQ", "attached": {"process": "loop", "since": "…"},
               "lastCheck": {"at": "…", "ok": true, "detail": "…", "by": "10 min before the open"},
               "sessionOpen": true, "nextOpen": "…"} }}
  ```
  - `engine` is a trading session's own status, `null` between sessions.
  - `bridge` is the bridge host's readiness: the verdict, the first failing
    link and its fix, and the whole chain (`bridge`, `extension`, `version`,
    `fidelity`, `trading`, `account`, each `ok`, `warn`, `fail` or
    `unknown`). It is `null` from a bridge without its host (`serve`). It is
    sent when its meaning changes; its wording ("last heard 4 s ago") is
    refreshed at most once a minute.
  - `trading`, `previews` and `fidelity` (`signed_in`, `signed_out`,
    `no_tab`, `elsewhere`) are `null` until the extension has said.
  - `book` is the trading book, read-only from the trader's ledger and fill
    journal (the bridge's `book.py`), refreshed every 30 s and sent when it
    changes; absent from a bridge older than this or one with no trader to
    read:
    ```json
    "book": {"symbol": "RSP", "asOf": "…", "lastPrice": 219.42,
             "open": [{"id": "…", "qty": 1, "buyPrice": 219.98, "targetPrice": 222.18,
                       "boughtAt": "…"}],
             "openCost": 5037.80, "unrealized": -4.21,
             "closed": [{"id": "…", "qty": 1, "buyPrice": 218.10, "sellPrice": 220.28,
                         "pnl": 2.18, "reason": "profit_target", "boughtAt": "…", "soldAt": "…"}],
             "today": {"realized": 8.72, "sales": 4, "buys": 7},
             "days": [{"date": "2026-11-03", "realized": 8.72, "sales": 4, "buys": 7},
                      {"date": "2026-11-02", "realized": -1.25, "sales": 2, "buys": 3}],
             "funds": {"value": 25012.40, "cash": 19970.39, "unsettled": 220.28,
                       "available": 19750.11}}
    ```
    `open` is newest first; `closed` is the last 20 sales, newest first, `pnl`
    after costs. `unrealized` is the open lots at `lastPrice`, before costs.
    `today` is the market's calendar day (New York). `days` is each market
    day the fill journal still has with a fill (the trader keeps 10
    sessions; at most 30 are sent), newest first, today's included: what an
    app keeps as its profit history, so it reaches back further than the
    journal. A bridge older than this sends no `days`. `boughtAt` is `null` when
    the journal no longer reaches back to the buy. `funds` is the
    deployment's money as its ledger keeps it: `cash` (sales still settling
    included), `unsettled` (those sales, T+1 at Fidelity), `available` (what
    the trader can spend now: `cash` less `unsettled`, never below 0) and
    `value` (`cash` and the open lots at `lastPrice`; `null` with lots open and
    no price, never the cash alone). It is the money the trader manages, not
    the whole brokerage account. `null` when the ledger has not recorded its
    cash; absent from a listener older than this.
  - `trader` is the trader's own report, from the trader notifier only (a
    Fidelity bridge's readiness says the same and more):
    ```json
    "trader": {"state": "trading", "detail": null, "process": "loop",
               "stale": false, "running": true, "nextOpen": null,
               "lastTickAt": "…", "updatedAt": "…", "openLots": 3, "openOrders": 0}
    ```
    `state` is its own word (`trading`, `buys_paused`, `winding_down`,
    `stopped`, `recovery_required`; between sessions the supervisor's
    `waiting_for_open`, `closed`, `disabled`, …). `stale`: it has stopped
    reporting, so what it last said is no longer true. `running`: a trading
    loop, reporting, not ended. `null` before any trader has reported. The
    trader notifier's `engine` is the loop's state in the bridge's words
    (`running`, `paused`, `stopped`, …), `null` between sessions; it sends no
    `extension` and no `bridge`.
- **goodbye**, `{"type": "goodbye", "reason": "…"}`: the bridge is
  stopping on purpose. The host runs all the time, so this is a restart (a
  deploy, a config change) and it is back within seconds. The connection
  then closes; reconnect shortly, and only alarm if it stays away (the app
  allows 10 minutes).

Ignore any `type` you do not know.

## App → bridge

- **test**, `{"type": "test"}`: the bridge answers with a test
  notification to this app alone, at most one every 2 seconds.

That is all an app can ask. The bridge ignores anything else, and nothing an
app sends reaches the extension, the engine or Fidelity.

## Liveness

The bridge pings every 20 s at the WebSocket level. An app that falls too far
behind is disconnected (close code 1013). It reconnects with `since` and
catches up from what the bridge kept.
