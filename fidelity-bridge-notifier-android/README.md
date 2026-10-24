# Fidelity Bridge Notifier (Android)

A small Android app that tells you, as it happens, what the
[volatility-ai](https://github.com/AshitakaLax/volatility-ai) Fidelity Bridge
sees:

- **Trades:** a buy or a sell filled (or partly filled), and optionally
  each order accepted, cancelled or expired.
- **Order problems:** Fidelity rejected an order, the browser extension
  refused one, or nobody can tell what became of one.
- **The extension:** it connected, reconnected, or went away, and its "Allow
  trading" switch was turned on or off.
- **The engine:** starting, running, paused, halted, stopped.
- **The bridge itself:** if the phone cannot reach it for 2 minutes, the app
  says so, and says again when it is back.

It only listens. Nothing it sends can place, cancel or change anything. The
one thing it may ask the bridge for is a test notification.

This folder is self-contained, as if it were its own repository. Inside
volatility-ai, nothing imports it, and the bridge's tests only read its
protocol vectors.

## Set up the bridge

On the computer that runs the bridge (in the volatility-ai checkout):

1. **Make the app's key.** It is a different key from the extension's, and
   the bridge refuses to start if the two are the same.
   ```bash
   python -m fidelity_gateway.bridge keygen --notify
   ```
   This appends `FIDELITY_BRIDGE_NOTIFY_KEY` to `.env` and prints the key once.
2. **Turn notifications on**, so the phone can reach them.
   - For the live loop, in the deployment's YAML:
     ```yaml
     live:
       fidelity:
         bridge:
           notifications:
             enabled: true
             host: 0.0.0.0                           # listen beyond this computer...
             port: 8766
             allowed_clients: ["192.168.1.0/24"]     # ...but only to your network
             # events: [buy, sell, order_problem, connected, disconnected, trading_switch, engine]
     ```
   - Or for the bridge alone, to try it out:
     ```bash
     python -m fidelity_gateway.bridge serve --notify \
         --notify-host 0.0.0.0 --notify-allow-client 192.168.1.0/24
     ```
   The bridge logs `[notify] apps may connect at ws://…:8766/notifications`.

Run nothing else on port 8766, and don't forward it from your router. To get
notifications away from home, put the phone and the bridge on one VPN (for
example WireGuard or Tailscale) and allow that VPN's addresses instead.

## Install the app

Build it with the Android SDK (Android Studio, or the command line with
`ANDROID_HOME` set) and JDK 17 or later:

```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Or download the `bridge-notifier-debug` artifact from this repository's CI.

In the app:

1. Enter the bridge's address. `192.168.1.10` is enough: the port defaults
   to 8766 and the path to `/notifications`. Full `ws://` or `wss://` URLs
   work too.
2. Paste the key that `keygen --notify` printed.
3. Tap **Save and start watching**. Allow notifications when asked.
4. Tap **Send a test notification** to check the whole path.

Under **Notify me about**, choose which kinds appear as notifications.
Everything still shows in the app's Recent list. The bridge's own `events`
setting decides what is sent at all.

The app keeps a quiet ongoing notification while it watches. Android needs
one to keep the connection open with the screen off. It starts again after a
reboot if it was watching before. If notifications arrive late, exempt the
app from battery optimisation (Settings → Apps → Bridge Notifier → Battery →
Unrestricted).

### What to expect

- **The engine runs one trading session at a time.** At the close, the
  bridge says goodbye and the app shows "The bridge stopped". It checks back
  every so often without alarming you. At the next open it reconnects and
  delivers anything it missed.
- **After the phone was offline,** it catches up from what the bridge kept
  (up to 200 notifications per bridge run). Nothing is shown twice.
- **The first time it connects,** what the bridge already kept goes into
  the Recent list but is not announced.

## Security

- **The key never crosses the network.** The app and the bridge each prove
  they hold it with an HMAC over fresh nonces.
- **Every message after the handshake is sealed** with a per-connection
  key, so nobody on the network can forge or replay a notification. Over
  `ws://` the messages are not encrypted, which is why it belongs on your
  own network or a VPN. For `wss://`, put the bridge behind a TLS proxy. The
  app trusts the system's certificate authorities and any you install
  yourself.
- **The key is stored in the app's private storage,** excluded from backups
  and device transfers.

[PROTOCOL.md](PROTOCOL.md) is the full wire protocol.

## Layout

| Path | What |
|---|---|
| `core/` | Plain Kotlin, no Android: the protocol (`Protocol.kt`), messages (`Messages.kt`), the connection with handshake, catch-up and reconnecting (`BridgeClient.kt`, on OkHttp), and the "out of reach" rule (`LinkAlarm.kt`). A Gradle build of its own, so it builds and tests without the Android SDK. |
| `core/src/test/resources/vectors/` | The protocol vectors the bridge's tests reproduce too. |
| `app/` | The Android app: a foreground service (`MonitorService.kt`) holding one `BridgeClient`, the phone's notifications (`Alerts.kt`), settings (`Prefs.kt`) and one screen (`MainActivity.kt`). Plain framework views; no AndroidX. |

## Develop

```bash
./gradlew -p core test        # protocol, messages, client against a fake bridge: no SDK needed
./gradlew assembleDebug       # the app: needs the Android SDK
```

To try the client against a real bridge without a phone:

```bash
BRIDGE_NOTIFY_URL=192.168.1.10 BRIDGE_NOTIFY_KEY=<key> \
    ./gradlew -p core test --tests '*LiveBridgeTest' -i
```

This connects, prints the status and everything the bridge replays, asks for
a test notification, and passes once it arrives.

Requirements: minSdk 26 (Android 8.0), targetSdk 35, Kotlin 2.0, AGP 8.7,
Gradle 8.14 (wrapper included).
