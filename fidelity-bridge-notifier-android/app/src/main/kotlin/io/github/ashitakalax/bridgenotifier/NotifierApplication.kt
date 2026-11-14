package io.github.ashitakalax.bridgenotifier

import android.app.Application
import android.content.Context
import android.text.format.DateFormat

class NotifierApplication : Application() {
    /** The Activity page's list on disk; one for the process. */
    lateinit var history: History
        private set

    override fun onCreate() {
        super.onCreate()
        Alerts.createChannels(this)
        Format.twentyFourHour = DateFormat.is24HourFormat(this)
        history = History(this)
        // What was on the Activity page last time, before anything new arrives.
        val kept = history.load()
        if (kept.isNotEmpty()) MonitorState.update { it.copy(recent = kept.take(MonitorState.RECENT)) }
    }

    companion object {
        fun history(context: Context): History = (context.applicationContext as NotifierApplication).history
    }
}
