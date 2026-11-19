package io.github.ashitakalax.bridgenotifier

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.widget.Toast

/**
 * A notification's buttons that need no screen: "Mute 1 h" quiets its
 * account for an hour (Account.mutedUntil) -- what it says still reaches the
 * Activity page, and the Connect page can end it early.
 */
class AlertActions : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION_MUTE_HOUR) return
        val id = intent.getStringExtra(EXTRA_ACCOUNT) ?: return
        val until = System.currentTimeMillis() + HOUR_MILLIS
        val prefs = Prefs(context)
        val account = prefs.change(id) { it.copy(mutedUntil = until) } ?: return
        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
        intent.getIntExtra(EXTRA_NOTIFICATION, -1).takeIf { it >= 0 }?.let { Alerts.cancel(context, it) }
        Toast.makeText(
            context,
            context.getString(R.string.muted_until_toast, account.name, Format.clockAt(until)),
            Toast.LENGTH_SHORT,
        ).show()
    }

    companion object {
        const val ACTION_MUTE_HOUR = "io.github.ashitakalax.bridgenotifier.MUTE_HOUR"
        const val EXTRA_ACCOUNT = "account"
        const val EXTRA_NOTIFICATION = "notification"
        const val HOUR_MILLIS = 3_600_000L
    }
}
