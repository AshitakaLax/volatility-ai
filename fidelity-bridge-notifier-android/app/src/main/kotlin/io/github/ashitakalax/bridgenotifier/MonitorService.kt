package io.github.ashitakalax.bridgenotifier

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.ConnectivityManager
import android.net.Network
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.ClientSettings
import io.github.ashitakalax.bridgenotifier.core.DailySummary
import io.github.ashitakalax.bridgenotifier.core.LinkAlarm
import io.github.ashitakalax.bridgenotifier.core.Notification
import io.github.ashitakalax.bridgenotifier.core.ProfitHistory
import java.net.URI
import java.time.Instant

/**
 * Watches every account: a foreground service holding one BridgeClient per
 * account, so the connections outlive the screen. It turns what each says
 * into phone notifications -- those of the kinds switched on for that account,
 * none for one muted -- and says so itself when one has been out of reach
 * longer than the grace. It keeps each account's profit history from the
 * books it hears, and once a minute it sees whether an end-of-day summary is
 * due, and whether it is time to ask GitHub about a newer app.
 */
class MonitorService : Service() {
    private val main = Handler(Looper.getMainLooper())
    private lateinit var prefs: Prefs

    /** One account's connection, and what the service keeps about it. Main thread only. */
    private inner class Watch(var account: Account) {
        var client: BridgeClient? = null
        var alarm = LinkAlarm(prefs.unreachableGraceMillis)
        var lastReason = ""
        val checkAlarm = Runnable { checkLinkAlarm(this) }
    }

    private val watches = mutableMapOf<String, Watch>()
    private var networkCallback: ConnectivityManager.NetworkCallback? = null

    /** Once a minute while watching: the summaries due, and the update check. */
    private val tick = object : Runnable {
        override fun run() {
            checkSummaries()
            UpdateChecker.maybeCheck(this@MonitorService)
            main.postDelayed(this, TICK_MILLIS)
        }
    }

    override fun onCreate() {
        super.onCreate()
        prefs = Prefs(this)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private val connectivity: ConnectivityManager
        get() = getSystemService(ConnectivityManager::class.java)!!

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                stopWatching()
                return START_NOT_STICKY
            }
            ACTION_TEST -> if (watches.isEmpty()) {
                stopSelf()
                return START_NOT_STICKY
            } else {
                val id = intent?.getStringExtra(EXTRA_ACCOUNT) ?: prefs.currentId
                watches[id]?.client?.requestTest()
            }
            ACTION_RESTART -> {
                closeClients()
                startWatching()
            }
            // ACTION_START, or null: restarted by the system after it had to stop us.
            else -> startWatching()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        rememberHeard()
        closeClients()
        super.onDestroy()
    }

    private fun startWatching() {
        // First, always: a service started in the foreground must say so
        // within seconds, even one about to stop.
        goForeground(getString(R.string.monitor_starting))
        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
        if (!prefs.isConfigured) {
            stopWatching()
            return
        }
        if (watches.isNotEmpty()) return
        for (account in prefs.accounts) {
            val watch = Watch(account)
            val watcher = Watcher(account.id, watch)
            val client = BridgeClient(
                ClientSettings(
                    url = account.url,
                    apiKey = account.apiKey,
                    clientName = "Notifier on ${Build.MODEL}",
                    clientVersion = BuildConfig.VERSION_NAME,
                ),
                watcher,
                prefs.positions(account.id),
            )
            watch.client = client
            watches[account.id] = watch
            client.start()
        }
        watchNetwork()
        updateMonitor()
        main.removeCallbacks(tick)
        main.post(tick)
    }

    private fun stopWatching() {
        rememberHeard()
        closeClients()
        MonitorState.update { snapshot ->
            snapshot.copy(states = snapshot.states.mapValues { (_, state) -> state.copy(link = BridgeClient.Link.Stopped) })
        }
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun closeClients() {
        for (watch in watches.values) {
            watch.client?.stop()
            main.removeCallbacks(watch.checkAlarm)
            watch.alarm.reset()
        }
        watches.clear()
        main.removeCallbacks(tick)
        networkCallback?.let { connectivity.unregisterNetworkCallback(it) }
        networkCallback = null
    }

    /** When each account still connected was last heard: for a later start, until it is heard again. */
    private fun rememberHeard() {
        val now = System.currentTimeMillis()
        for (id in watches.keys) {
            if (MonitorState.snapshot.stateOf(id).link is BridgeClient.Link.Connected) prefs.setHeardAt(id, now)
        }
    }

    private fun goForeground(text: String) {
        val notification = Alerts.monitorNotification(this, text)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(Alerts.MONITOR_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(Alerts.MONITOR_ID, notification)
        }
    }

    /** Back on a network: try every listener now rather than at the end of its wait. */
    private fun watchNetwork() {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                main.post { watches.values.forEach { it.client?.reconnectNow() } }
            }
        }
        connectivity.registerDefaultNetworkCallback(callback)
        networkCallback = callback
    }

    /**
     * One account's listener. The client calls it on its own thread; everything
     * is handed to the main one, and dropped there if that account's watch has
     * since been replaced or stopped -- its last words must not overwrite the next's.
     */
    private inner class Watcher(private val id: String, private val watch: Watch) : BridgeClient.Listener {
        private fun onMain(block: () -> Unit) {
            main.post { if (watches[id] === watch) block() }
        }

        override fun onLink(link: BridgeClient.Link) = onMain { onLinkChanged(watch, link) }

        override fun onNotification(notification: Notification, fresh: Boolean) =
            onMain { onNotificationReceived(watch, notification, fresh) }

        override fun onMissed(notifications: List<Notification>, fresh: Boolean) =
            onMain { onMissedReceived(watch, notifications, fresh) }

        override fun onStatus(status: BridgeStatus) = onMain { onStatusReceived(watch, status) }
    }

    /** What the listener says now; its book's days go into the account's history. */
    private fun onStatusReceived(watch: Watch, status: BridgeStatus) {
        val id = watch.account.id
        status.book?.let { prefs.recordBook(id, it) }
        MonitorState.updateAccount(id) { it.copy(status = status, heardAt = System.currentTimeMillis()) }
        // A trader that just stopped for the day: its summary need not wait for the tick.
        checkSummaries()
    }

    /**
     * Each account summing up its day (Account.summary) whose day is over:
     * one note, for the latest day that traded. An account out of reach is
     * waited for until extended hours end; muted, the day passes unsaid.
     */
    private fun checkSummaries() {
        val now = Instant.now()
        for (watch in watches.values) {
            val account = current(watch)
            if (!account.summary) continue
            val state = MonitorState.snapshot.stateOf(account.id)
            // Connected and its book in: the figures are the listener's, not what was last heard.
            val heard = state.link is BridgeClient.Link.Connected && state.status.book != null
            val done = prefs.summaryDone(account.id)
                ?: ProfitHistory.marketDay(now).minusDays(1).also { prefs.setSummaryDone(account.id, it) }
            val trading = DailySummary.trading(state.status)
            val due = DailySummary.due(now, done, trading, heard, prefs.history(account.id)) ?: continue
            prefs.setSummaryDone(account.id, due.through)
            val day = due.day ?: continue
            if (account.mutedAt(now.toEpochMilli())) continue
            Alerts.postSummary(this, account, day, state.status.book, heard, now)
        }
    }

    /**
     * [watch]'s account as saved now: muting it, on the Connect page, changes
     * what is said without a reconnect.
     */
    private fun current(watch: Watch): Account =
        prefs.account(watch.account.id)?.also { watch.account = it } ?: watch.account

    private fun onLinkChanged(watch: Watch, link: BridgeClient.Link) {
        val account = current(watch)
        val now = System.currentTimeMillis()
        val wasConnected = MonitorState.snapshot.stateOf(account.id).link is BridgeClient.Link.Connected
        val connected = link is BridgeClient.Link.Connected
        // Connected, it is heard all along (the listener pings every 20 s); on
        // losing it, that is when it was last heard.
        if (wasConnected && !connected) prefs.setHeardAt(account.id, now)
        MonitorState.updateAccount(account.id) {
            it.copy(link = link, heardAt = if (connected || wasConnected) now else it.heardAt)
        }
        val sayLinks = prefs.alertWhenUnreachable && account.alertsLinks(now)
        when (link) {
            is BridgeClient.Link.Connected -> {
                // The hello says what this stream is about: keep it, so the
                // pages wear the right colour while offline too.
                val learned = account.learned(link.hello.account)
                if (learned != account) {
                    prefs.change(account.id) { it.learned(link.hello.account) }?.let { watch.account = it }
                    MonitorState.setAccounts(prefs.accounts, prefs.currentId)
                }
                if (watch.alarm.connected() == LinkAlarm.Alert.BACK && sayLinks) {
                    Alerts.postLinkBack(this, learned)
                }
            }
            is BridgeClient.Link.Waiting -> {
                watch.lastReason = link.reason
                // A goodbye is the always-on listener restarting: given longer to come back.
                watch.alarm.lost(SystemClock.uptimeMillis(), restarting = link.deliberate)
                scheduleAlarmCheck(watch)
            }
            is BridgeClient.Link.Refused -> {
                watch.alarm.reset()
                if (account.alertsLinks(now)) Alerts.postRefused(this, account, link.reason)
            }
            BridgeClient.Link.Connecting, BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> Unit
        }
        updateMonitor()
    }

    private fun onNotificationReceived(watch: Watch, notification: Notification, fresh: Boolean) {
        val account = current(watch)
        val now = System.currentTimeMillis()
        MonitorState.updateAccount(account.id) {
            it.copy(recent = (listOf(notification) + it.recent).take(MonitorState.RECENT), heardAt = now)
        }
        if (fresh && account.alerts(notification, now)) {
            Alerts.post(this, notification, account)
        }
    }

    /**
     * What was missed while away, as one: every one listed, but only the
     * latest the account would have notified about shown, with how many
     * more came -- not a stack of them on reconnecting.
     */
    private fun onMissedReceived(watch: Watch, notifications: List<Notification>, fresh: Boolean) {
        val account = current(watch)
        val now = System.currentTimeMillis()
        MonitorState.updateAccount(account.id) {
            it.copy(recent = (notifications.asReversed() + it.recent).take(MonitorState.RECENT), heardAt = now)
        }
        if (!fresh) return
        val worth = notifications.filter { account.alerts(it, now) }
        worth.lastOrNull()?.let { latest -> Alerts.post(this, latest, account, alsoMissed = worth.size - 1) }
    }

    /** The ongoing notification: each account's link in a few words. */
    private fun updateMonitor() {
        val snapshot = MonitorState.snapshot
        val text = watches.values.joinToString(" · ") { watch ->
            val host = hostOf(watch.account.url)
            val words = when (val link = snapshot.stateOf(watch.account.id).link) {
                is BridgeClient.Link.Connected -> getString(R.string.monitor_connected, host)
                is BridgeClient.Link.Waiting -> if (link.deliberate) {
                    getString(R.string.monitor_bridge_restarting, host)
                } else {
                    getString(R.string.monitor_waiting, host, link.reason)
                }
                is BridgeClient.Link.Refused -> getString(R.string.monitor_refused)
                else -> getString(R.string.monitor_connecting, host)
            }
            if (watches.size > 1) "${watch.account.name}: $words" else words
        }
        Alerts.updateMonitor(this, text.ifEmpty { getString(R.string.monitor_starting) })
    }

    private fun scheduleAlarmCheck(watch: Watch) {
        val due = watch.alarm.dueAt() ?: return
        main.removeCallbacks(watch.checkAlarm)
        main.postDelayed(watch.checkAlarm, maxOf(0L, due - SystemClock.uptimeMillis()))
    }

    private fun checkLinkAlarm(watch: Watch) {
        if (watches[watch.account.id] !== watch) return
        if (watch.alarm.check(SystemClock.uptimeMillis()) != LinkAlarm.Alert.LOST) return
        val account = current(watch)
        if (prefs.alertWhenUnreachable && account.alertsLinks(System.currentTimeMillis())) {
            Alerts.postLinkLost(this, account, watch.lastReason)
        }
    }

    companion object {
        private const val ACTION_START = "io.github.ashitakalax.bridgenotifier.START"
        private const val ACTION_RESTART = "io.github.ashitakalax.bridgenotifier.RESTART"
        private const val ACTION_STOP = "io.github.ashitakalax.bridgenotifier.STOP"
        private const val ACTION_TEST = "io.github.ashitakalax.bridgenotifier.TEST"
        private const val EXTRA_ACCOUNT = "account"
        private const val TICK_MILLIS = 60_000L

        fun start(context: Context) {
            context.startForegroundService(intent(context, ACTION_START))
        }

        /** With new settings: new connections, the same service. */
        fun restart(context: Context) {
            context.startForegroundService(intent(context, ACTION_RESTART))
        }

        fun stop(context: Context) {
            context.startService(intent(context, ACTION_STOP))
        }

        /** A test notification from one account's listener: the current one's by default. */
        fun requestTest(context: Context, accountId: String? = null) {
            context.startService(intent(context, ACTION_TEST).putExtra(EXTRA_ACCOUNT, accountId))
        }

        private fun intent(context: Context, action: String) =
            Intent(context, MonitorService::class.java).setAction(action)

        fun hostOf(url: String): String = try {
            URI(url).let { uri -> if (uri.port == -1) uri.host else "${uri.host}:${uri.port}" } ?: url
        } catch (_: Exception) {
            url
        }
    }
}
