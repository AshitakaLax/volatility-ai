package io.github.ashitakalax.bridgenotifier

import android.app.Application
import android.content.Context
import android.text.format.DateFormat

class NotifierApplication : Application() {
    /** Each account's Activity list on disk; one for the process. */
    lateinit var recents: Recents
        private set

    override fun onCreate() {
        super.onCreate()
        Alerts.createChannels(this)
        Format.twentyFourHour = DateFormat.is24HourFormat(this)
        recents = Recents(this)
        // What was on each account's Activity page last time, before anything new arrives.
        val prefs = Prefs(this)
        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
        for (account in prefs.accounts) {
            val kept = recents.load(account.id)
            if (kept.isNotEmpty()) MonitorState.updateAccount(account.id) { it.copy(recent = kept.take(MonitorState.RECENT)) }
        }
    }

    companion object {
        fun recents(context: Context): Recents = (context.applicationContext as NotifierApplication).recents
    }
}
