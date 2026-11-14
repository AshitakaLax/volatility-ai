package io.github.ashitakalax.bridgenotifier

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import io.github.ashitakalax.bridgenotifier.core.BridgeAddress
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.ClientSettings
import io.github.ashitakalax.bridgenotifier.core.LinkAlarm
import io.github.ashitakalax.bridgenotifier.core.Notification
import java.net.URI

/**
 * Watches the bridge: a foreground service holding one BridgeClient, so the
 * connection outlives the screen. It turns what the bridge says into phone
 * notifications -- those of the kinds switched on in the app -- and says so
 * itself when the bridge has been out of reach longer than the grace -- but
 * not while the phone itself is offline or away from the bridge's network.
 */
class MonitorService : Service() {
    private val main = Handler(Looper.getMainLooper())
    private lateinit var prefs: Prefs

    @Volatile
    private var client: BridgeClient? = null
    private var alarm = LinkAlarm(0)
    private var lastReason = ""
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private var monitorText = ""
    private var historyUnsaved = false
    private val checkAlarm = Runnable { checkLinkAlarm() }
    private val saveHistory = Runnable {
        historyUnsaved = false
        NotifierApplication.history(this).save(MonitorState.snapshot.recent)
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
            ACTION_TEST -> if (client == null) {
                stopSelf()
                return START_NOT_STICKY
            } else {
                client?.requestTest()
            }
            ACTION_RESTART -> {
                closeClient()
                startWatching()
            }
            ACTION_RETRY -> {
                startWatching()
                client?.reconnectNow()
            }
            // ACTION_START, or null: restarted by the system after it had to stop us.
            else -> startWatching()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        closeClient()
        super.onDestroy()
    }

    private fun startWatching() {
        // First, always: a service started in the foreground must say so
        // within seconds, even one about to stop.
        goForeground(getString(R.string.monitor_connecting, hostOf(prefs.url)))
        if (!prefs.isConfigured) {
            stopWatching()
            return
        }
        if (client != null) {
            // Already watching: put back the line the "connecting" above replaced.
            showMonitorText()
            return
        }
        alarm = LinkAlarm(prefs.unreachableGraceMillis)
        val watcher = Watcher()
        val next = BridgeClient(
            ClientSettings(
                url = prefs.url,
                apiKey = prefs.apiKey,
                clientName = "Notifier on ${Build.MODEL}",
                clientVersion = BuildConfig.VERSION_NAME,
            ),
            watcher,
            prefs,
        )
        watcher.owner = next
        client = next
        next.start()
        phoneChanged(phoneNow())
        watchNetwork()
    }

    private fun stopWatching() {
        closeClient()
        MonitorState.update { it.copy(link = BridgeClient.Link.Stopped) }
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun closeClient() {
        client?.stop()
        client = null
        main.removeCallbacks(saveHistory)
        if (historyUnsaved) saveHistory.run()
        main.removeCallbacks(checkAlarm)
        alarm.reset()
        networkCallback?.let { connectivity.unregisterNetworkCallback(it) }
        networkCallback = null
    }

    private fun goForeground(text: String) {
        monitorText = text
        val notification = Alerts.monitorNotification(this, text)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(Alerts.MONITOR_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(Alerts.MONITOR_ID, notification)
        }
    }

    /**
     * Back on a network: try the bridge now rather than at the end of the
     * wait. And which network: none, or mobile data alone with a bridge at a
     * home address, is the phone being away rather than the bridge being down.
     */
    private fun watchNetwork() {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                client?.reconnectNow()
            }

            override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
                val phone = phoneOn(capabilities)
                main.post { phoneChanged(phone) }
            }

            override fun onLost(network: Network) {
                main.post { phoneChanged(MonitorState.Phone.OFFLINE) }
            }
        }
        connectivity.registerDefaultNetworkCallback(callback)
        networkCallback = callback
    }

    private fun phoneNow(): MonitorState.Phone =
        connectivity.getNetworkCapabilities(connectivity.activeNetwork)?.let(::phoneOn) ?: MonitorState.Phone.OFFLINE

    private fun phoneOn(capabilities: NetworkCapabilities): MonitorState.Phone {
        val mobileOnly = capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) &&
            !capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN) &&
            !capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) &&
            !capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
        return if (mobileOnly && BridgeAddress.isLocalNetwork(prefs.url)) MonitorState.Phone.AWAY else MonitorState.Phone.ONLINE
    }

    private fun phoneChanged(phone: MonitorState.Phone) {
        if (client == null || phone == MonitorState.snapshot.phone) return
        MonitorState.update { it.copy(phone = phone) }
        if (phone == MonitorState.Phone.ONLINE) {
            // Somewhere the bridge can be reached from again: it has its
            // allowance from here before being called lost.
            alarm.phoneBack(SystemClock.uptimeMillis())
            scheduleAlarmCheck()
            client?.reconnectNow()
        }
        showMonitorText()
    }

    /** The ongoing notification's line: the connection, and once connected whether it is ready to trade. */
    private fun showMonitorText() {
        val snapshot = MonitorState.snapshot
        val host = hostOf(prefs.url)
        val bridge = snapshot.status.bridge
        val text = when (val link = snapshot.link) {
            is BridgeClient.Link.Connected -> when {
                bridge == null -> getString(R.string.monitor_connected, host)
                bridge.ready -> getString(R.string.monitor_ready)
                else -> getString(R.string.monitor_not_ready, bridge.summary)
            }
            is BridgeClient.Link.Refused -> getString(R.string.monitor_refused)
            BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> return
            else -> when {
                snapshot.phone == MonitorState.Phone.OFFLINE -> getString(R.string.monitor_phone_offline)
                snapshot.phone == MonitorState.Phone.AWAY -> getString(R.string.monitor_phone_away)
                link is BridgeClient.Link.Waiting && link.deliberate -> getString(R.string.monitor_bridge_restarting, host)
                link is BridgeClient.Link.Waiting -> getString(R.string.monitor_waiting, host, link.reason)
                else -> getString(R.string.monitor_connecting, host)
            }
        }
        if (text == monitorText) return
        monitorText = text
        Alerts.updateMonitor(this, text)
    }

    /**
     * One client's listener. The client calls it on its own thread; everything
     * is handed to the main one, and dropped there if that client has since
     * been replaced or stopped -- its last words must not overwrite the next's.
     */
    private inner class Watcher : BridgeClient.Listener {
        var owner: BridgeClient? = null

        private fun onMain(block: () -> Unit) {
            main.post { if (owner != null && client === owner) block() }
        }

        override fun onLink(link: BridgeClient.Link) = onMain { onLinkChanged(link) }

        override fun onNotification(notification: Notification, fresh: Boolean) =
            onMain { onNotificationReceived(notification, fresh) }

        override fun onStatus(status: BridgeStatus) = onMain {
            MonitorState.update { it.copy(status = status, statusAt = System.currentTimeMillis()) }
            showMonitorText()
        }
    }

    private fun onLinkChanged(link: BridgeClient.Link) {
        MonitorState.update { it.copy(link = link) }
        when (link) {
            is BridgeClient.Link.Connected -> {
                if (alarm.connected() == LinkAlarm.Alert.BACK && prefs.alertWhenUnreachable) {
                    Alerts.postLinkBack(this)
                }
            }
            is BridgeClient.Link.Waiting -> {
                lastReason = link.reason
                // A goodbye is the always-on bridge restarting: given longer to come back.
                alarm.lost(SystemClock.uptimeMillis(), restarting = link.deliberate)
                scheduleAlarmCheck()
            }
            is BridgeClient.Link.Refused -> {
                alarm.reset()
                Alerts.postRefused(this, link.reason)
            }
            BridgeClient.Link.Connecting, BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> Unit
        }
        showMonitorText()
    }

    private fun onNotificationReceived(notification: Notification, fresh: Boolean) {
        MonitorState.update { it.copy(recent = (listOf(notification) + it.recent).take(MonitorState.RECENT)) }
        if (fresh && notification.kind !in prefs.disabledKinds) {
            Alerts.post(this, notification)
        }
        // Kept for the next run; a replay of many is written once, when it settles.
        historyUnsaved = true
        main.removeCallbacks(saveHistory)
        main.postDelayed(saveHistory, SAVE_HISTORY_AFTER_MILLIS)
    }

    private fun scheduleAlarmCheck() {
        val due = alarm.dueAt() ?: return
        main.removeCallbacks(checkAlarm)
        main.postDelayed(checkAlarm, maxOf(0L, due - SystemClock.uptimeMillis()))
    }

    private fun checkLinkAlarm() {
        // A phone that is offline or away has not lost the bridge; it says so quietly instead.
        val canReach = MonitorState.snapshot.phone == MonitorState.Phone.ONLINE
        if (alarm.check(SystemClock.uptimeMillis(), canReach) == LinkAlarm.Alert.LOST && prefs.alertWhenUnreachable) {
            Alerts.postLinkLost(this, lastReason)
        }
    }

    companion object {
        private const val ACTION_START = "io.github.ashitakalax.bridgenotifier.START"
        private const val ACTION_RESTART = "io.github.ashitakalax.bridgenotifier.RESTART"
        private const val ACTION_STOP = "io.github.ashitakalax.bridgenotifier.STOP"
        private const val ACTION_TEST = "io.github.ashitakalax.bridgenotifier.TEST"
        private const val ACTION_RETRY = "io.github.ashitakalax.bridgenotifier.RETRY"
        private const val SAVE_HISTORY_AFTER_MILLIS = 1_000L

        fun start(context: Context) {
            context.startForegroundService(intent(context, ACTION_START))
        }

        /** With new settings: a new connection, the same service. */
        fun restart(context: Context) {
            context.startForegroundService(intent(context, ACTION_RESTART))
        }

        fun stop(context: Context) {
            context.startService(intent(context, ACTION_STOP))
        }

        /** Try the bridge now instead of at the end of the wait. */
        fun retry(context: Context) {
            context.startForegroundService(intent(context, ACTION_RETRY))
        }

        fun requestTest(context: Context) {
            context.startService(intent(context, ACTION_TEST))
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
