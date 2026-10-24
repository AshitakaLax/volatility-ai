package io.github.ashitakalax.bridgenotifier

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Back to watching after a reboot or an update, if it was watching before. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED && intent.action != Intent.ACTION_MY_PACKAGE_REPLACED) {
            return
        }
        val prefs = Prefs(context)
        if (prefs.monitoring && prefs.isConfigured) MonitorService.start(context)
    }
}
