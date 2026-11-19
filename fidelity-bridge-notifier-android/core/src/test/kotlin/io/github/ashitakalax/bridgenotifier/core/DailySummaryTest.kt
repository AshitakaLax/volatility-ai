package io.github.ashitakalax.bridgenotifier.core

import java.time.LocalDate
import java.time.LocalDateTime
import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DailySummaryTest {
    private val ny = ZoneId.of("America/New_York")

    /** A moment in New York. */
    private fun at(text: String) = LocalDateTime.parse(text).atZone(ny).toInstant()

    private fun date(text: String) = LocalDate.parse(text)

    // Tuesday 2026-11-03 and the days around it.
    private val history = listOf(
        DayFigures(date("2026-10-30"), 4.0, 3, 2), // Friday
        DayFigures(date("2026-11-02"), 2.0, 1, 1), // Monday
        DayFigures(date("2026-11-03"), 8.72, 4, 7), // Tuesday
    )

    @Test
    fun theDayIsDueAfterTheCloseOnceTheTraderHasStopped() {
        val done = date("2026-11-02")
        assertNull(DailySummary.due(at("2026-11-03T15:59"), done, trading = false, heard = true, history))
        assertNull(DailySummary.due(at("2026-11-03T16:04"), done, trading = false, heard = true, history))
        val due = DailySummary.due(at("2026-11-03T16:05"), done, trading = false, heard = true, history)!!
        assertEquals(date("2026-11-03"), due.day!!.date)
        assertEquals(date("2026-11-03"), due.through)
        // Said once: done through today, nothing more today.
        assertNull(DailySummary.due(at("2026-11-03T18:00"), due.through, trading = false, heard = true, history))
    }

    @Test
    fun aTraderStillGoingAfterTheCloseIsWaitedForUntilExtendedHoursEnd() {
        val done = date("2026-11-02")
        assertNull(DailySummary.due(at("2026-11-03T19:59"), done, trading = true, heard = true, history))
        assertEquals(date("2026-11-03"), DailySummary.due(at("2026-11-03T20:05"), done, trading = true, heard = true, history)!!.day!!.date)
    }

    @Test
    fun outOfReachItWaitsForTheFiguresUntilExtendedHoursEnd() {
        // The morning after, just started: nothing heard yet, so yesterday is not decided...
        assertNull(DailySummary.due(at("2026-11-04T08:50"), date("2026-11-02"), trading = false, heard = false, history))
        // ...until the listener has said its book.
        assertEquals(date("2026-11-03"), DailySummary.due(at("2026-11-04T08:51"), date("2026-11-02"), trading = false, heard = true, history)!!.day!!.date)
        // Never heard all day: at 20:05 what there is is said.
        assertNull(DailySummary.due(at("2026-11-03T20:04"), date("2026-11-02"), trading = false, heard = false, history))
        assertEquals(date("2026-11-03"), DailySummary.due(at("2026-11-03T20:05"), date("2026-11-02"), trading = false, heard = false, history)!!.through)
    }

    @Test
    fun aDayWithoutTradesIsPassedOverQuietly() {
        // Saturday: nothing traded; it is marked done and nothing is posted.
        val due = DailySummary.due(at("2026-11-07T16:30"), date("2026-11-06"), trading = false, heard = true, history)!!
        assertNull(due.day)
        assertEquals(date("2026-11-07"), due.through)
    }

    @Test
    fun aPhoneAwayForDaysGetsTheLatestDayThatTradedOnce() {
        // Last summed up Thursday; back on Tuesday morning before the open.
        val due = DailySummary.due(at("2026-11-03T08:00"), date("2026-10-29"), trading = false, heard = true, history)!!
        assertEquals(date("2026-11-02"), due.day!!.date)
        assertEquals(date("2026-11-02"), due.through)
        assertNull(DailySummary.due(at("2026-11-03T09:00"), due.through, trading = false, heard = true, history))
    }

    @Test
    fun aTraderIsMidSessionWhenItSaysItIsRunning() {
        fun trader(running: Boolean, stale: Boolean) = BridgeStatus(
            null, null,
            trader = TraderStatus("trading", null, "loop", stale, running, null, null, null),
        )
        assertEquals(true, DailySummary.trading(trader(running = true, stale = false)))
        assertEquals(false, DailySummary.trading(trader(running = true, stale = true)))
        assertEquals(false, DailySummary.trading(trader(running = false, stale = false)))
        fun engine(state: String?) = BridgeStatus(null, state?.let { EngineStatus(it, null, "live", "RSP", null, null) })
        assertEquals(true, DailySummary.trading(engine("running")))
        assertEquals(true, DailySummary.trading(engine("paused")))
        assertEquals(false, DailySummary.trading(engine("stopped")))
        assertEquals(false, DailySummary.trading(engine(null)))
    }
}
