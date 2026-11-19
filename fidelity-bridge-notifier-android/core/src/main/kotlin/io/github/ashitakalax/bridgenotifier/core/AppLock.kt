package io.github.ashitakalax.bridgenotifier.core

/**
 * When the app asks for its owner again: as it opens, and as it comes back
 * after [awayMillis] out of sight. A glance at another app, or the screen
 * turning, does not count. One per process, so a process the system ended
 * asks again. Times are the caller's clock, never read here (on Android,
 * elapsedRealtime: time asleep counts as away).
 */
class AppLock(private val awayMillis: Long = AWAY_MILLIS) {
    private var unlocked = false
    private var leftAt: Long? = null

    /** The app comes into sight at [now]: whether to ask for the owner first. */
    fun cameBack(now: Long): Boolean {
        val left = leftAt
        leftAt = null
        if (unlocked && left != null && now - left >= awayMillis) unlocked = false
        return !unlocked
    }

    /** The owner proved it -- or there is nothing to lock: carry on. */
    fun unlocked() {
        unlocked = true
        leftAt = null
    }

    /** The app went out of sight at [now]. */
    fun left(now: Long) {
        if (unlocked) leftAt = now
    }

    companion object {
        const val AWAY_MILLIS = 60_000L
    }
}
