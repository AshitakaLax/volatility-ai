package io.github.ashitakalax.bridgenotifier

import android.content.Context
import io.github.ashitakalax.bridgenotifier.core.Notification
import java.io.File
import java.io.IOException
import java.util.concurrent.Executors

/**
 * Each account's Activity list, kept between runs. A listener replays only
 * what the app has not seen, so without this the page would be empty every
 * time Android restarted the app. A file per account in the app's private
 * storage, out of backups like the rest (AndroidManifest.xml).
 */
class Recents(context: Context) {
    private val dir = context.filesDir
    private val writer = Executors.newSingleThreadExecutor { task ->
        Thread(task, "recents").apply { isDaemon = true }
    }

    private fun file(id: String) = File(dir, "recent-$id.json")

    /** Before accounts, one bridge's list: it became the first account's, as its settings did (Prefs). */
    private val legacy = File(dir, "recent.json")

    /** What was kept for [id], newest first; nothing when there is no file or it cannot be read. */
    fun load(id: String): List<Notification> {
        val kept = file(id).takeIf { it.exists() } ?: legacy.takeIf { id == Prefs.FIRST_ACCOUNT && it.exists() }
        return try {
            kept?.let { Notification.decodeAll(it.readText()) }.orEmpty()
        } catch (_: IOException) {
            emptyList()
        }
    }

    /** Keeps [recent] for [id] (but for tests, which are of the moment). Written off the main thread, whole or not at all. */
    fun save(id: String, recent: List<Notification>) {
        writer.execute {
            try {
                val target = file(id)
                val next = File(dir, target.name + ".tmp")
                next.writeText(Notification.encodeAll(recent.filterNot { it.isTest }))
                if (next.renameTo(target)) {
                    if (id == Prefs.FIRST_ACCOUNT) legacy.delete()
                } else {
                    next.delete()
                }
            } catch (_: IOException) {
                // Not kept this time: the list on screen is unaffected.
            }
        }
    }

    /** A different listener for [id], or the account removed: the old list is not its. */
    fun clear(id: String) {
        writer.execute {
            file(id).delete()
            if (id == Prefs.FIRST_ACCOUNT) legacy.delete()
        }
    }
}
