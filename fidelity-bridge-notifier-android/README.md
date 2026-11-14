# Fidelity Bridge Notifier (Android)

A small Android app that tells you, as it happens, what the
[volatility-ai](https://github.com/AshitakaLax/volatility-ai) Fidelity Bridge
sees:

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

Four pages:

- **Home**, where the app opens once the bridge is set: ready to trade or the
  one thing to fix, the readiness checklist link by link, today's realised
  profit and the open lots' unrealised figure, the day's buys and sales, the
  trading session and the last account check. When the bridge cannot be
  reached, tap the top card to try again now; what is below it is marked
  "Not live" with the time the bridge last said it.
- **Lots**: the open lots, each with where it sells and how far it has to go,
  or the last 20 sales with what each made.
- **Activity**: the last 200 notifications, filtered to trades, problems or
  the connection. Kept on the phone, so it is still there after Android
  restarts the app. Tapping a notification opens this page.
- **Connect**, behind the gear on Home (and the first page until the bridge
  is set): the bridge's address and key, a three-step check that they work
  (reachable, key accepted, a test notification received), the **Watch the
  bridge** switch, whether Android will let the alerts through, and what to
  be told about. The app's version is at the bottom.

It follows the phone's light or dark theme, and its 12- or 24-hour clock.

Lots and today's profit come from the bridge's `book` (PROTOCOL.md); a bridge
older than that shows the other pages as before.

It only listens. Nothing it sends can place, cancel or change anything. The
one thing it may ask the bridge for is a test notification.

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

In the app:

1. Enter the bridge's address. `192.168.1.10` is enough: the port defaults
   to 8766 and the path to `/notifications`. Full `ws://` or `wss://` URLs
   work too.
2. Copy the key that `keygen --notify` printed and tap **Paste**. The whole
   `.env` line (`FIDELITY_BRIDGE_NOTIFY_KEY=…`) works too: the name, quotes
   and spaces around the key are dropped.
3. Tap **Save and connect**. Allow notifications when asked.
4. Tap **Send test** to check the whole path.

Under **Notify me about**, choose which kinds appear as notifications,
grouped as the Activity page filters them. Everything still shows on the
Activity page. The bridge's own `events` setting decides what is sent at all.
If notifications are off for the app, or Android may delay its connection to
save battery, the card says so with a button that opens the setting.

The app keeps a quiet ongoing notification while it watches. Android needs
one to keep the connection open with the screen off. Once connected it says
whether the bridge is ready to trade, or what is in the way. It starts again
after a reboot if it was watching before. **Watch the bridge** on the Connect
page turns watching off and on.

### What to expect

- **The bridge is always on.** Between sessions the app stays connected
  and shows "no trading session running"; the readiness card still says
  whether the next open is covered.
- **It says goodbye only to restart** (a deploy, a config change). The app
  shows "The bridge is restarting" and reconnects within seconds. It
  alarms only if the bridge is still away after 10 minutes.
- **After the phone was offline,** it catches up from what the bridge kept
  (up to 200 notifications per bridge run). Nothing is shown twice.
- **The first time it connects,** what the bridge already kept goes onto
  the Activity page but is not announced.
- **Away from home is not an alarm.** With no network, or on mobile data
  alone when the bridge is at a home-network address (`192.168.…`,
  `server.lan`), the app says the phone is off the bridge's network instead
  of warning that the bridge is out of reach. Back on its Wi-Fi or a VPN, the
  bridge has its two minutes again before that warning.

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
| `app/` | The Android app: a foreground service (`MonitorService.kt`) holding one `BridgeClient`, the phone's notifications (`Alerts.kt`), settings (`Prefs.kt`), the Activity page's history on disk (`History.kt`) and one activity (`MainActivity.kt`) over four pages (`*Screen.kt`) drawn from `Ui.kt`. Plain framework views; no AndroidX. Colours are named in `res/values/colors.xml`, with their dark counterparts in `res/values-night/`. |

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

The tag is also the app's version: `v1.2.3` builds an app that says 1.2.3 at
the bottom of its Connect page, with a version code (10203) higher than the
release before it. Tag releases as `v<major>.<minor>.<patch>`; any other
build calls itself `0.1.0-dev`.

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
