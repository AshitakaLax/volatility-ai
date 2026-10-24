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
 * itself when the bridge has been out of reach longer than the grace.
 */
class MonitorService : Service() {
    private val main = Handler(Looper.getMainLooper())
    private lateinit var prefs: Prefs

    @Volatile
    private var client: BridgeClient? = null
    private var alarm = LinkAlarm(0)
    private var lastReason = ""
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private val checkAlarm = Runnable { checkLinkAlarm() }

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
        if (client != null) return
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
        main.removeCallbacks(checkAlarm)
        alarm.stoppedDeliberately()
        networkCallback?.let { connectivity.unregisterNetworkCallback(it) }
        networkCallback = null
    }

    private fun goForeground(text: String) {
        val notification = Alerts.monitorNotification(this, text)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(Alerts.MONITOR_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(Alerts.MONITOR_ID, notification)
        }
    }

    /** Back on a network: try the bridge now rather than at the end of the wait. */
    private fun watchNetwork() {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                client?.reconnectNow()
            }
        }
        connectivity.registerDefaultNetworkCallback(callback)
        networkCallback = callback
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

        override fun onStatus(status: BridgeStatus) = onMain { MonitorState.update { it.copy(status = status) } }
    }

    private fun onLinkChanged(link: BridgeClient.Link) {
        MonitorState.update { it.copy(link = link) }
        val host = hostOf(prefs.url)
        when (link) {
            is BridgeClient.Link.Connected -> {
                if (alarm.connected() == LinkAlarm.Alert.BACK && prefs.alertWhenUnreachable) {
                    Alerts.postLinkBack(this)
                }
                Alerts.updateMonitor(this, getString(R.string.monitor_connected, host))
            }
            is BridgeClient.Link.Waiting -> {
                lastReason = link.reason
                if (link.deliberate) {
                    alarm.stoppedDeliberately()
                    Alerts.updateMonitor(this, getString(R.string.monitor_bridge_stopped, host))
                } else {
                    alarm.lost(SystemClock.uptimeMillis())
                    scheduleAlarmCheck()
                    Alerts.updateMonitor(this, getString(R.string.monitor_waiting, host, link.reason))
                }
            }
            is BridgeClient.Link.Refused -> {
                alarm.stoppedDeliberately()
                Alerts.postRefused(this, link.reason)
                Alerts.updateMonitor(this, getString(R.string.monitor_refused))
            }
            BridgeClient.Link.Connecting -> Alerts.updateMonitor(this, getString(R.string.monitor_connecting, host))
            BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> Unit
        }
    }

    private fun onNotificationReceived(notification: Notification, fresh: Boolean) {
        MonitorState.update { it.copy(recent = (listOf(notification) + it.recent).take(MonitorState.RECENT)) }
        if (fresh && (notification.isTest || notification.kind in prefs.enabledKinds)) {
            Alerts.post(this, notification)
        }
    }

    private fun scheduleAlarmCheck() {
        val due = alarm.dueAt() ?: return
        main.removeCallbacks(checkAlarm)
        main.postDelayed(checkAlarm, maxOf(0L, due - SystemClock.uptimeMillis()))
    }

    private fun checkLinkAlarm() {
        if (alarm.check(SystemClock.uptimeMillis()) == LinkAlarm.Alert.LOST && prefs.alertWhenUnreachable) {
            Alerts.postLinkLost(this, lastReason)
        }
    }

    companion object {
        private const val ACTION_START = "io.github.ashitakalax.bridgenotifier.START"
        private const val ACTION_RESTART = "io.github.ashitakalax.bridgenotifier.RESTART"
        private const val ACTION_STOP = "io.github.ashitakalax.bridgenotifier.STOP"
        private const val ACTION_TEST = "io.github.ashitakalax.bridgenotifier.TEST"

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
