package io.github.ashitakalax.bridgenotifier.core

import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime

/**
 * When an account's end-of-day note is due, for an account whose trades are
 * summed up rather than said one by one (Account.summary).
 *
 * A market day is over at 16:05 New York once its trader has stopped
 * trading, and at 20:05 whatever it says (the end of extended hours): a
 * trader still mid-session at 16:05 is trading after hours. Until a day is
 * over, the day before is the latest one that is. A phone that was away
 * for days gets the latest day that traded, once, not one note per day.
 * While the account's listener is out of reach (or has not yet sent its
 * book) nothing is decided until 20:05: its figures may be incomplete.
 */
object DailySummary {
    val AFTER_CLOSE: LocalTime = LocalTime.of(16, 5)
    val LATEST: LocalTime = LocalTime.of(20, 5)

    /** The latest market day that is over at [now]. */
    fun lastOver(now: Instant, trading: Boolean): LocalDate {
        val here = now.atZone(MARKET_ZONE)
        val time = here.toLocalTime()
        val over = time >= LATEST || (time >= AFTER_CLOSE && !trading)
        return if (over) here.toLocalDate() else here.toLocalDate().minusDays(1)
    }

    /**
     * What to do at [now], having summed up every day to [done]: [Due.day]
     * is the day to post (null: none traded), and [Due.through] is the day
     * to remember as done. Null when nothing is due. [heard]: the listener is
     * connected and has sent its book.
     */
    fun due(now: Instant, done: LocalDate, trading: Boolean, heard: Boolean, history: List<DayFigures>): Due? {
        if (!heard && now.atZone(MARKET_ZONE).toLocalTime() < LATEST) return null
        val through = lastOver(now, trading)
        if (through <= done) return null
        val day = history.lastOrNull { it.date > done && it.date <= through && it.traded }
        return Due(day, through)
    }

    data class Due(val day: DayFigures?, val through: LocalDate)

    /**
     * Whether [status] says its trader is mid-session: an Alpaca trader that
     * is reporting and running, or a Fidelity engine in a session.
     */
    fun trading(status: BridgeStatus): Boolean {
        status.trader?.let { return it.running && !it.stale }
        return status.engine?.state in setOf("starting", "running", "paused")
    }
}
