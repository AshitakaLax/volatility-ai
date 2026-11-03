package io.github.ashitakalax.bridgenotifier

import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.abs

/** How money, shares and times read on the screens. */
object Format {
    private val clock = DateTimeFormatter.ofPattern("HH:mm", Locale.US)
    private val dayClock = DateTimeFormatter.ofPattern("EEE HH:mm", Locale.US)
    private val date = DateTimeFormatter.ofPattern("MMM d HH:mm", Locale.US)

    fun money(value: Double): String = String.format(Locale.US, "$%,.2f", value)

    /** +$8.72 or −$4.21 (a true minus sign). */
    fun signedMoney(value: Double): String = (if (value < 0) "−" else "+") + money(abs(value))

    /** 1, 0.5, 12.25: no trailing zeros. */
    fun shares(qty: Double): String =
        if (qty == Math.rint(qty)) qty.toLong().toString() else String.format(Locale.US, "%.4f", qty).trimEnd('0')

    fun percent(value: Double): String = String.format(Locale.US, "%.2f", value)

    /** 13:41 today, Mon 13:41 this week, Oct 30 13:41 before that. */
    fun clockTime(iso: String?, zone: ZoneId = ZoneId.systemDefault(), now: Instant = Instant.now()): String? {
        val millis = iso?.let(Alerts::epochMillis) ?: return null
        val at = Instant.ofEpochMilli(millis).atZone(zone)
        val today: LocalDate = now.atZone(zone).toLocalDate() // LocalDate.ofInstant needs API 31
        val days = Duration.between(at.toLocalDate().atStartOfDay(zone), today.atStartOfDay(zone)).toDays()
        return when {
            days == 0L -> clock.format(at)
            days in 1..6 -> dayClock.format(at)
            else -> date.format(at)
        }
    }

    /** 42 min, 2 h 05 min, 3 d: how long between two moments. */
    fun duration(fromIso: String?, toIso: String?): String? {
        val from = fromIso?.let(Alerts::epochMillis) ?: return null
        val to = toIso?.let(Alerts::epochMillis) ?: return null
        val minutes = (to - from) / 60_000
        return when {
            minutes < 1 -> "under a minute"
            minutes < 60 -> "$minutes min"
            minutes < 24 * 60 -> String.format(Locale.US, "%d h %02d min", minutes / 60, minutes % 60)
            else -> "${minutes / (24 * 60)} d"
        }
    }
}
