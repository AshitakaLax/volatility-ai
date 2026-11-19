package io.github.ashitakalax.bridgenotifier

import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.abs
import kotlin.math.roundToInt

/** How money, shares and times read on the screens. */
object Format {
    /** The phone's own choice of 13:41 or 1:41 PM; the activity sets it as it comes forward. */
    @Volatile
    var twentyFourHour = true

    private class Clocks(time: String) {
        val clock: DateTimeFormatter = DateTimeFormatter.ofPattern(time, Locale.US)
        val dayClock: DateTimeFormatter = DateTimeFormatter.ofPattern("EEE $time", Locale.US)
        val date: DateTimeFormatter = DateTimeFormatter.ofPattern("MMM d $time", Locale.US)
    }

    private val twentyFour = Clocks("HH:mm")
    private val twelve = Clocks("h:mm a")

    fun money(value: Double): String = String.format(Locale.US, "$%,.2f", value)

    /** "4 minutes ago", "in 2 hours": a moment (epoch milliseconds) from now. */
    fun relative(millis: Long): String = android.text.format.DateUtils.getRelativeTimeSpanString(millis).toString()

    /** [relative] for an ISO-8601 moment; null when it is not one. */
    fun ago(iso: String?): String? = iso?.let(Alerts::epochMillis)?.let(::relative)

    /** +$8.72 or −$4.21 (a true minus sign). */
    fun signedMoney(value: Double): String = (if (value < 0) "−" else "+") + money(abs(value))

    /** 1, 0.5, 12.25: no trailing zeros. */
    fun shares(qty: Double): String =
        if (qty == Math.rint(qty)) qty.toLong().toString() else String.format(Locale.US, "%.4f", qty).trimEnd('0')

    fun percent(value: Double): String = String.format(Locale.US, "%.2f", value)

    /** $252,608: whole dollars, for a figure in a narrow column. */
    fun wholeMoney(value: Double): String = String.format(Locale.US, "$%,.0f", value)

    /** 82% for 0.82; "<1%" and ">99%" rather than a rounded 0% or 100% that is not true. */
    fun share(fraction: Double): String {
        val whole = (fraction * 100).roundToInt()
        return when {
            fraction > 0 && whole == 0 -> "<1%"
            fraction < 1 && whole == 100 -> ">99%"
            else -> "$whole%"
        }
    }

    /** 13:41 today, Mon 13:41 this week, Oct 30 13:41 before that (or 1:41 PM, as the phone is set). */
    fun clockTime(iso: String?, zone: ZoneId = ZoneId.systemDefault(), now: Instant = Instant.now()): String? {
        val millis = iso?.let(Alerts::epochMillis) ?: return null
        return clockAt(millis, zone, now)
    }

    fun clockAt(millis: Long, zone: ZoneId = ZoneId.systemDefault(), now: Instant = Instant.now()): String {
        val clocks = if (twentyFourHour) twentyFour else twelve
        val at = Instant.ofEpochMilli(millis).atZone(zone)
        val today: LocalDate = now.atZone(zone).toLocalDate() // LocalDate.ofInstant needs API 31
        val days = Duration.between(at.toLocalDate().atStartOfDay(zone), today.atStartOfDay(zone)).toDays()
        return when {
            days == 0L -> clocks.clock.format(at)
            days in 1..6 -> clocks.dayClock.format(at)
            else -> clocks.date.format(at)
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
