package io.github.ashitakalax.bridgenotifier.core

/**
 * Decides when losing the bridge is worth a notification of the app's own.
 *
 * The bridge cannot say it died, and the phone cannot tell a dead bridge
 * from its own lost network: either way, a connection that drops and is not
 * back within [graceMillis] raises [Alert.LOST] once, and coming back after
 * that raises [Alert.BACK]. A drop that heals inside the grace -- Wi-Fi
 * handing over -- raises nothing.
 *
 * The bridge runs as an always-on service, so it says goodbye only to
 * restart (a deploy, a config change). That is given [restartGraceMillis]:
 * a restart that comes back says nothing, one that does not is a lost
 * bridge like any other.
 *
 * Times are whatever clock the caller uses; nothing here reads one.
 */
class LinkAlarm(
    private val graceMillis: Long,
    private val restartGraceMillis: Long = 10 * 60_000L,
) {
    enum class Alert { LOST, BACK }

    private var lostAt: Long? = null
    private var allowed = graceMillis
    private var alerted = false

    /** Connected (again). BACK if the loss had been announced. */
    fun connected(): Alert? {
        val announced = alerted
        reset()
        return if (announced) Alert.BACK else null
    }

    /**
     * The connection is down: dropped, or -- [restarting] -- the bridge said
     * goodbye. Failed retries while already down keep the first allowance.
     */
    fun lost(now: Long, restarting: Boolean = false) {
        if (lostAt != null) return
        lostAt = now
        allowed = if (restarting) restartGraceMillis else graceMillis
    }

    /** The user stopped watching, or the key was refused: nothing to alarm about. */
    fun reset() {
        lostAt = null
        alerted = false
    }

    /** LOST once, when the allowance has run out. */
    fun check(now: Long): Alert? {
        val since = lostAt ?: return null
        if (alerted || now - since < allowed) return null
        alerted = true
        return Alert.LOST
    }

    /** When [check] next has something to say, or null. */
    fun dueAt(): Long? = lostAt?.takeUnless { alerted }?.plus(allowed)
}
