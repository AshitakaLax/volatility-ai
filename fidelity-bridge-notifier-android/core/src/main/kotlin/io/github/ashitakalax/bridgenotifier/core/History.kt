package io.github.ashitakalax.bridgenotifier.core

import java.time.Instant
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeParseException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/** The market's own clock: a trading day is New York's calendar day. */
val MARKET_ZONE: ZoneId = ZoneId.of("America/New_York")

/** One market day's totals: what its sales made after costs, and how many sales and buys. */
data class DayFigures(
    val date: LocalDate,
    val realized: Double,
    val sales: Int,
    val buys: Int,
) {
    /** Whether anything was bought or sold that day. */
    val traded: Boolean get() = sales > 0 || buys > 0

    companion object {
        fun parse(obj: JsonObject?): DayFigures? {
            if (obj == null) return null
            val date = obj.string("date")?.let { runCatching { LocalDate.parse(it) }.getOrNull() } ?: return null
            return DayFigures(
                date = date,
                realized = obj.double("realized") ?: 0.0,
                sales = obj.long("sales")?.toInt()?.coerceAtLeast(0) ?: 0,
                buys = obj.long("buys")?.toInt()?.coerceAtLeast(0) ?: 0,
            )
        }
    }
}

/**
 * Each account's profit, day by day, as the app keeps it. The listener only
 * sees as far back as the trader's fill journal (10 sessions), so the app
 * keeps every day it has heard of and lets the listener's figures replace its
 * own for the days the listener still has: those are complete, the app's may
 * have been caught mid-day.
 */
object ProfitHistory {
    /** About a year and a half of trading days. */
    const val KEPT = 400

    /**
     * [kept] with what [book] says, oldest first. A listener older than `days`
     * still says today's totals, dated by its `asOf`.
     */
    fun merge(kept: List<DayFigures>, book: Book): List<DayFigures> {
        val heard = book.days.ifEmpty {
            val day = book.asOf?.let(::marketDay) ?: return kept
            listOf(DayFigures(day, book.realizedToday, book.salesToday, book.buysToday))
        }
        val byDate = kept.associateBy { it.date }.toMutableMap()
        heard.forEach { byDate[it.date] = it }
        return byDate.values.sortedBy { it.date }.takeLast(KEPT)
    }

    /** The days from [from] on, oldest first. */
    fun since(days: List<DayFigures>, from: LocalDate): List<DayFigures> = days.filter { it.date >= from }

    fun encode(days: List<DayFigures>): String = buildJsonArray {
        for (day in days) {
            add(
                buildJsonObject {
                    put("date", day.date.toString())
                    put("realized", day.realized)
                    put("sales", day.sales)
                    put("buys", day.buys)
                },
            )
        }
    }.toString()

    /** What [encode] wrote, oldest first; anything unreadable is left out. */
    fun decode(text: String?): List<DayFigures> {
        val array = text?.let { runCatching { Json.parseToJsonElement(it) }.getOrNull() } as? JsonArray
            ?: return emptyList()
        return array.mapNotNull { DayFigures.parse(it as? JsonObject) }.distinctBy { it.date }.sortedBy { it.date }
    }

    /** The market day an ISO-8601 moment falls on, or null if it is not one. */
    fun marketDay(iso: String): LocalDate? = try {
        OffsetDateTime.parse(iso).atZoneSameInstant(MARKET_ZONE).toLocalDate()
    } catch (_: DateTimeParseException) {
        null
    }

    fun marketDay(at: Instant): LocalDate = at.atZone(MARKET_ZONE).toLocalDate()
}
