package io.github.ashitakalax.bridgenotifier

import android.content.Context
import android.os.Handler
import android.os.Looper
import io.github.ashitakalax.bridgenotifier.core.Updates

/**
 * Asks GitHub, at most twice a day, whether a newer app is out (Updates in
 * core), and says so once per new version: a notification, and a banner in
 * the app until it is closed. Called when the app comes into sight and from
 * the watching service's minute tick; nothing is downloaded or installed --
 * the release page opens in the browser.
 */
object UpdateChecker {
    private const val EVERY_MILLIS = 12 * 3_600_000L
    private const val RETRY_MILLIS = 3_600_000L

    /** One question to GitHub at a time. Main thread only. */
    var asking = false
        private set

    /** Ask, if it is time to (or [now] asked for on the Connect page). */
    fun maybeCheck(context: Context, force: Boolean = false) {
        val prefs = Prefs(context)
        val due = prefs.checkUpdates && System.currentTimeMillis() - prefs.updateCheckedAt >= EVERY_MILLIS
        if (asking || !(force || due)) return
        asking = true
        val app = context.applicationContext
        val main = Handler(Looper.getMainLooper())
        Thread {
            val result = runCatching { Updates.fetch(BuildConfig.RELEASES_REPO, BuildConfig.VERSION_NAME) }
            main.post {
                asking = false
                val saved = Prefs(app)
                val now = System.currentTimeMillis()
                result.onSuccess { release ->
                    saved.updateCheckedAt = now
                    saved.latestRelease = release
                    saved.updateError = null
                    if (release.newerThan(BuildConfig.VERSION_NAME) && saved.announcedVersion != release.version) {
                        saved.announcedVersion = release.version
                        Alerts.postUpdate(app, release)
                    }
                }.onFailure { error ->
                    // Asked again in an hour, not twelve.
                    saved.updateCheckedAt = now - EVERY_MILLIS + RETRY_MILLIS
                    saved.updateError = error.message ?: error.javaClass.simpleName
                }
                MonitorState.update { it } // the banner and the Connect page redraw
            }
        }.apply {
            isDaemon = true
            name = "update-check"
        }.start()
    }

    /** The newer release, when GitHub last said there is one. */
    fun available(prefs: Prefs): Updates.Release? =
        prefs.latestRelease?.takeIf { it.newerThan(BuildConfig.VERSION_NAME) }

    /**
     * How the newer one goes on: over this one, or -- a debug build on
     * either side, each signed with a key of its own -- only after
     * uninstalling this one, which loses its accounts and keys.
     */
    fun howToInstall(context: Context, release: Updates.Release): String = context.getString(
        if (release.debugOnly || BuildConfig.DEBUG) R.string.update_body_reinstall else R.string.update_body,
        BuildConfig.VERSION_NAME,
    )
}
