package io.github.ashitakalax.bridgenotifier.core

/**
 * Decides when losing the bridge is worth a notification of the app's own.
 *
 * The bridge cannot say it died, and the phone cannot tell a dead bridge
 * from its own lost network: either way, a connection that drops and is not
 * back within [graceMillis] raises [Alert.LOST] once, and coming back after
 * that raises [Alert.BACK]. A drop that heals inside the grace -- Wi-Fi
 * handing over, the bridge restarting -- raises nothing. A deliberate stop
 * (the bridge said goodbye: the engine runs a session at a time and stops
 * every evening) never alarms.
 *
 * Times are whatever clock the caller uses; nothing here reads one.
 */
class LinkAlarm(private val graceMillis: Long) {
    enum class Alert { LOST, BACK }

    private var lostAt: Long? = null
    private var alerted = false

    /** Connected (again). BACK if the loss had been announced. */
    fun connected(): Alert? {
        val announced = alerted
        lostAt = null
        alerted = false
        return if (announced) Alert.BACK else null
    }

    /** The connection dropped without a goodbye. */
    fun lost(now: Long) {
        if (lostAt == null) lostAt = now
    }

    /** The bridge said goodbye, or the user stopped watching. */
    fun stoppedDeliberately() {
        lostAt = null
        alerted = false
    }

    /** LOST once, when the grace has run out. */
    fun check(now: Long): Alert? {
        val since = lostAt ?: return null
        if (alerted || now - since < graceMillis) return null
        alerted = true
        return Alert.LOST
    }

    /** When [check] next has something to say, or null. */
    fun dueAt(): Long? = lostAt?.takeUnless { alerted }?.plus(graceMillis)
}
