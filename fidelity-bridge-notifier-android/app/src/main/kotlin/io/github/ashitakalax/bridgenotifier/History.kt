package io.github.ashitakalax.bridgenotifier

import android.content.Context
import io.github.ashitakalax.bridgenotifier.core.Notification
import java.io.File
import java.io.IOException
import java.util.concurrent.Executors

/**
 * The Activity page's list, kept between runs. The bridge replays only what
 * the app has not seen, so without this the page would be empty every time
 * Android restarted the app. One file in the app's private storage, out of
 * backups like the rest (AndroidManifest.xml).
 */
class History(context: Context) {
    private val file = File(context.filesDir, "recent.json")
    private val writer = Executors.newSingleThreadExecutor { task ->
        Thread(task, "history").apply { isDaemon = true }
    }

    /** What was kept, newest first; nothing when there is no file or it cannot be read. */
    fun load(): List<Notification> = try {
        if (file.exists()) Notification.decodeAll(file.readText()) else emptyList()
    } catch (_: IOException) {
        emptyList()
    }

    /** Keeps [recent] (but for tests, which are of the moment). Written off the main thread, whole or not at all. */
    fun save(recent: List<Notification>) {
        writer.execute {
            try {
                val next = File(file.parentFile, file.name + ".tmp")
                next.writeText(Notification.encodeAll(recent.filterNot { it.isTest }))
                if (!next.renameTo(file)) next.delete()
            } catch (_: IOException) {
                // Not kept this time: the list on screen is unaffected.
            }
        }
    }

    /** A different bridge: the old one's history is not this one's. */
    fun clear() {
        writer.execute { file.delete() }
    }
}
