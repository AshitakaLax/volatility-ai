package io.github.ashitakalax.bridgenotifier.core

import java.time.Instant
import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HistoryTest {
    private fun day(date: String, realized: Double, sales: Int = 1, buys: Int = 1) =
        DayFigures(LocalDate.parse(date), realized, sales, buys)

    private fun book(days: List<DayFigures> = emptyList(), asOf: String? = "2026-11-03T19:00:00+00:00") = Book(
        symbol = "RSP", asOf = asOf, lastPrice = null, open = emptyList(), openCost = 0.0, unrealized = null,
        closed = emptyList(), realizedToday = 5.0, salesToday = 2, buysToday = 3, days = days,
    )

    @Test
    fun theListenersDaysReplaceTheAppsAndOlderOnesAreKept() {
        val kept = listOf(day("2026-10-01", 1.0), day("2026-11-02", 0.5, sales = 1))
        // The listener has 11-02 complete now, and today so far.
        val merged = ProfitHistory.merge(kept, book(listOf(day("2026-11-03", 5.0), day("2026-11-02", 4.0, sales = 3))))
        assertEquals(listOf(day("2026-10-01", 1.0), day("2026-11-02", 4.0, sales = 3), day("2026-11-03", 5.0)), merged)
    }

    @Test
    fun aListenerWithoutDaysStillGivesToday() {
        // 19:00 UTC is 14:00 in New York, the same day; 03:00 UTC is the evening before.
        assertEquals(listOf(day("2026-11-03", 5.0, sales = 2, buys = 3)), ProfitHistory.merge(emptyList(), book()))
        assertEquals(
            LocalDate.parse("2026-11-02"),
            ProfitHistory.merge(emptyList(), book(asOf = "2026-11-03T03:00:00+00:00")).single().date,
        )
        val kept = listOf(day("2026-10-01", 1.0))
        assertEquals(kept, ProfitHistory.merge(kept, book(asOf = null)))
    }

    @Test
    fun itKeepsAboutAYearAndAHalf() {
        val start = LocalDate.parse("2025-01-01")
        val many = (0 until ProfitHistory.KEPT + 10).map { DayFigures(start.plusDays(it.toLong()), 1.0, 1, 0) }
        val merged = ProfitHistory.merge(many, book(listOf(DayFigures(start.plusDays(1000), 2.0, 1, 0))))
        assertEquals(ProfitHistory.KEPT, merged.size)
        assertEquals(start.plusDays(1000), merged.last().date)
    }

    @Test
    fun itReadsBackWhatItWrote() {
        val days = listOf(day("2026-11-02", -1.25, sales = 2, buys = 0), day("2026-11-03", 8.72, sales = 4, buys = 7))
        assertEquals(days, ProfitHistory.decode(ProfitHistory.encode(days)))
        assertEquals(emptyList<DayFigures>(), ProfitHistory.decode(null))
        assertEquals(emptyList<DayFigures>(), ProfitHistory.decode("{}"))
        assertEquals(listOf(day("2026-11-03", 1.0)), ProfitHistory.decode("""[{"date":"2026-11-03","realized":1.0,"sales":1,"buys":1},{"date":"x"}]"""))
        assertEquals(listOf(day("2026-11-03", 1.0)), ProfitHistory.since(days + day("2026-11-03", 1.0), LocalDate.parse("2026-11-03")).takeLast(1))
    }

    @Test
    fun aMarketDayIsNewYorksDate() {
        assertEquals(LocalDate.parse("2026-11-02"), ProfitHistory.marketDay(Instant.parse("2026-11-03T04:59:00Z")))
        assertEquals(LocalDate.parse("2026-11-03"), ProfitHistory.marketDay(Instant.parse("2026-11-03T05:00:00Z")))
        assertNull(ProfitHistory.marketDay("yesterday"))
        assertTrue(day("2026-11-03", 0.0, sales = 0, buys = 1).traded)
        assertFalse(day("2026-11-03", 0.0, sales = 0, buys = 0).traded)
    }
}
