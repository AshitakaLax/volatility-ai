package io.github.ashitakalax.bridgenotifier

import android.app.Application

class NotifierApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Alerts.createChannels(this)
    }
}
