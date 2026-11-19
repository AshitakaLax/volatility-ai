# Fidelity Bridge Notifier (Android)

A small Android app that tells you, as it happens, what your
[volatility-ai](https://github.com/AshitakaLax/volatility-ai) accounts are
doing: a Fidelity account through its Fidelity Bridge, and Alpaca
deployments through the trader notifier. It watches as many accounts as you
add, and each wears its broker's colour: **Alpaca yellow, Fidelity green**,
on the page behind it, on its badge and on its notifications.

From the Fidelity Bridge:

- **Trades:** a buy or a sell filled (or partly filled), and optionally
  each order accepted, cancelled or expired.
- **Order problems:** Fidelity rejected an order, the browser extension
  refused one, or nobody can tell what became of one.
- **Readiness:** the bridge is not ready to trade, and which link to fix
  (the extension, the Fidelity sign-in, "Allow trading", the account
  check). Said once a problem has lasted a minute, as a critical alert when
  it is still not ready shortly before the open, and again once it is ready.
- **The extension:** it connected, reconnected, or went away; Fidelity
  signed you out or its tab was closed; its "Allow trading" switch was
  turned on or off.
- **The trading session:** starting, running, paused, halted, stopped; a
  second trader refused; a session that ended without saying so.
- **The account check** before each open failed, or passed again after a
  failure.
- **The bridge:** its port was taken, it restarted with new settings, it
  refused a connection from an address it does not allow. And if the phone
  cannot reach it for 2 minutes, the app says so, and again when it is back.

From the trader notifier, for each Alpaca deployment: buys (and where each
lot sells), sales (and what each made), orders placed, cancelled or rejected,
the engine starting, pausing and stopping, a trading window's summary, and a
trader that stops reporting -- read from the files the trader keeps, so
nothing has to change in the trader itself.

Four pages, each for the account shown. With more than one account, a chip
per account over the page switches between them.

- **Connect**, at start-up (switch that off on the page): your accounts, each
  a listener's address and key; a three-step check that the one selected
  works (reachable, key accepted, a test notification received); and what to
  be told about.
- **Home**: for Fidelity, ready to trade or the one thing to fix and the
  readiness checklist link by link; for Alpaca, what its trader says it is
  doing (trading, buys paused, waiting for the open, not reporting). Then
  today's realised profit and the open lots' unrealised figure, the day's buys
  and sales, the trading session and, for Fidelity, the last account check.
- **Lots**: the open lots, each with where it sells and how far it has to go,
  or the last 20 sales with what each made.
- **Activity**: the last 200 notifications, filtered to trades, problems or
  the connection.

Lots and today's profit come from the listener's `book` (PROTOCOL.md); a bridge
older than that shows the other pages as before. Each notification is headed
with its account's name.

It only listens. Nothing it sends can place, cancel or change anything. The
one thing it may ask a listener for is a test notification. It holds no
broker key: Alpaca's API keys can trade, so the app never asks Alpaca
anything, and hears only what the trader notifier reads from the trader's
own files.

This folder is self-contained, as if it were its own repository. Inside
volatility-ai, nothing imports it, and the bridge's tests only read its
protocol vectors.

## Set up the bridge

In volatility-ai the bridge is the always-on `fidelity-bridge` service
(`docs/DEPLOY.md`). It stays up between trading sessions, so the app stays
connected overnight and on weekends. In the volatility-ai checkout:

1. **Make the app's key.** It is a different key from the extension's, and
   the bridge refuses to start if the two are the same.
   ```bash
   python -m fidelity_gateway.bridge keygen --notify
   ```
   This appends `FIDELITY_BRIDGE_NOTIFY_KEY` to `.env` and prints the key once.
2. **Turn notifications on**, so the phone can reach them.
   - For the deployment, in its YAML (`config/fidelity_live.yaml`). The
     bridge picks up the edit within 30 seconds, without dropping the
     extension:
     ```yaml
     live:
       fidelity:
         bridge:
           notifications:
             enabled: true
             host: 0.0.0.0                           # listen beyond this computer...
             port: 8766
             allowed_clients: ["192.168.1.0/24"]     # ...but only to your network
             # events: [buy, sell, readiness, ...]   # left out: every kind but order_update
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

## Set up the trader notifier (Alpaca)

In volatility-ai it is the `trader-notifier` service (`docs/DEPLOY.md`,
section 6). It reads every Alpaca deployment in `config/deployments.yaml`,
read-only, and serves each on port 8767.

1. **Make its key**, again a key of its own:
   ```bash
   python -m fidelity_gateway.bridge keygen --notifier
   ```
   This appends `VAI_NOTIFIER_KEY` to `.env` and prints the key once.
2. **Open it to your network** in `.env` (it listens on loopback otherwise):
   ```bash
   VAI_NOTIFIER_HOST=0.0.0.0
   VAI_NOTIFIER_ALLOW=192.168.1.0/24
   ```
3. **Start it:** `docker compose --profile notifier up -d trader-notifier`.
   Its log names each deployment's address:
   `[notifier] Ultimate (paper) (alpaca, paper): apps may connect at ws://…:8767/notifications/paper-ultimate`.
   `/notifications` alone is the first deployment.

Or by hand, to try it out:
`python -m fidelity_gateway.bridge notifier --host 0.0.0.0 --allow-client 192.168.1.0/24`.

## Install the app

Download the APK attached to the latest
[release](https://github.com/AshitakaLax/volatility-ai/releases) and open it
on the phone (allow installing from your browser or file manager when
asked). A pull request that changes the app keeps its APK as the
`bridge-notifier-apk` artifact of its "Android app" check.

Or build it with the Android SDK (Android Studio, or the command line with
`ANDROID_HOME` set) and JDK 17 or later:

```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

In the app, for each account:

1. Enter its address. For the Fidelity bridge, `192.168.1.10` is enough: the
   port defaults to 8766 and the path to `/notifications`. For the trader
   notifier, `192.168.1.10:8767` is its first deployment, and
   `192.168.1.10:8767/notifications/live` another. Full `ws://` or `wss://`
   URLs work too.
2. Paste the key that `keygen --notify` (Fidelity) or `keygen --notifier`
   (Alpaca) printed.
3. Tap **Save and connect**. Allow notifications when asked.
4. Tap **Send test** to check the whole path.
5. **Add an account** for the next one. Tap an account in the list to edit
   or remove it.

The account takes its name and broker from what its listener says when it
connects; until then, one on port 8767 is taken to be Alpaca. An app that
was set up with one bridge before keeps it, as its first account.

Under **Notify me about**, choose which kinds the account being edited
turns into notifications; each account has its own, so switching off an
Alpaca paper deployment's buys and sells leaves Fidelity's alone. **Mute**
an account to keep the phone quiet about it entirely, its link alerts
included. Everything still shows on its Activity page, and a test you send
still arrives. The listener's own `events` setting decides what is sent at
all.

The app keeps a quiet ongoing notification while it watches. Android needs
one to keep the connection open with the screen off. It starts again after a
reboot if it was watching before. If notifications arrive late, exempt the
app from battery optimisation (Settings → Apps → Bridge Notifier → Battery →
Unrestricted).

### What to expect

- **The bridge is always on.** Between sessions the app stays connected
  and shows "no trading session running"; the readiness card still says
  whether the next open is covered.
- **It says goodbye only to restart** (a deploy, a config change). The app
  shows "The bridge is restarting" and reconnects within seconds. It
  alarms only if the bridge is still away after 10 minutes.
- **After the phone was offline,** it catches up from what the bridge kept
  (up to 200 notifications per bridge run). Nothing is shown twice, and the
  phone is not buried: only the latest of what was missed (of the kinds that
  account notifies about) is shown, headed "and 4 more while away"; every
  one is on the Activity page.
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
- **The app locks itself.** It asks for your fingerprint, face or screen
  lock (PIN, pattern or password) when it opens, and when it comes back
  after a minute away; until then a lock screen covers the pages, and its
  card in Recents shows nothing (Android 13 and later). The lock guards the
  app's pages, your accounts and their keys, not the connections: the
  service keeps listening and notifications keep arriving. A phone with no
  screen lock cannot lock the app, and the Connect page says so. Switch it
  off there under **Lock with fingerprint, face or screen lock**.

[PROTOCOL.md](PROTOCOL.md) is the full wire protocol.

## Layout

| Path | What |
|---|---|
| `core/` | Plain Kotlin, no Android: the protocol (`Protocol.kt`), messages (`Messages.kt`), the connection with handshake, catch-up and reconnecting (`BridgeClient.kt`, on OkHttp), and the "out of reach" rule (`LinkAlarm.kt`). A Gradle build of its own, so it builds and tests without the Android SDK. |
| `core/src/test/resources/vectors/` | The protocol vectors the bridge's tests reproduce too. |
| `core/src/main/.../Accounts.kt` | The accounts the app keeps (address, key, and the broker and label the hello said), as one JSON list. |
| `core/src/main/.../AppLock.kt` | When the app asks for its owner again: on opening, and after a minute away. |
| `app/` | The Android app: a foreground service (`MonitorService.kt`) holding one `BridgeClient` per account, the phone's notifications (`Alerts.kt`), settings (`Prefs.kt`), each broker's colours (`BrokerLook.kt`), the lock (`LockGate.kt`: BiometricPrompt on Android 10+, the screen-lock check before) and one screen (`MainActivity.kt`) with four pages. Plain framework views; no AndroidX. |

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

## Releases

Publishing a GitHub release builds the app and attaches the APK to it,
named after the release's tag (`fidelity-bridge-notifier-v1.2.0.apk`). In
volatility-ai, `.github/workflows/android.yml` does this. In this folder as
its own repository, `.github/workflows/ci.yml` does. A release saved as a
draft gets its APK when it is published.

The APK is signed with your own key. A phone installs an update only when it
is signed with the same key as the installed app, so make the key once and
keep it:

```bash
keytool -genkeypair -keystore bridge-notifier.jks -alias bridge-notifier \
    -keyalg RSA -keysize 4096 -validity 10000
base64 -w0 bridge-notifier.jks      # macOS: base64 -i bridge-notifier.jks
```

Then add these as the repository's Actions secrets (Settings → Secrets and
variables → Actions):

| Secret | Value |
|---|---|
| `BRIDGE_NOTIFIER_KEYSTORE_BASE64` | what `base64` printed |
| `BRIDGE_NOTIFIER_KEYSTORE_PASSWORD` | the keystore's password |
| `BRIDGE_NOTIFIER_KEY_ALIAS` | `bridge-notifier` |
| `BRIDGE_NOTIFIER_KEY_PASSWORD` | only if the key's password differs from the keystore's |

Keep `bridge-notifier.jks` and its password somewhere safe, outside the
repository: without them, no later APK can update the installed app.

Without the secrets, a release gets the debug APK instead
(`…-debug.apk`), and the workflow warns about it. Each debug build is signed
with a throwaway key, so installing the next one means uninstalling the app
first, which loses its settings.

To sign a release build on your own computer, set the same names as
environment variables, with `BRIDGE_NOTIFIER_KEYSTORE` the keystore's path:

```bash
BRIDGE_NOTIFIER_KEYSTORE=$HOME/keys/bridge-notifier.jks \
BRIDGE_NOTIFIER_KEYSTORE_PASSWORD=… BRIDGE_NOTIFIER_KEY_ALIAS=bridge-notifier \
    ./gradlew assembleRelease     # app/build/outputs/apk/release/app-release.apk
```
