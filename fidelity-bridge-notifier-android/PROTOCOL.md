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
  `{"type": "hello", "protocol": "…", "stream": "<random per bridge run>", "events": ["buy", …], "status": {…}}`
- **notification**:
  `{"type": "notification", "notification": {"id", "stream", "kind", "severity", "title", "body", "at", "data"}, "replay": true?}`
  - `id` counts from 1 within `stream`. A test notification has id `0`, and
    the bridge never keeps it.
  - `kind`: `buy`, `sell`, `order_update`, `order_problem`, `engine`,
    `session`, `readiness`, `fidelity_signin`, `account_check`, `connected`,
    `disconnected`, `trading_switch`, `refused`, `bridge`, or `test`. The
    vectors' `eventKinds` is the list both sides check. Unknown kinds may
    come later: show them.
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
