package io.github.ashitakalax.bridgenotifier

import android.app.Notification as AndroidNotification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.drawable.Icon
import android.net.Uri
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.Book
import io.github.ashitakalax.bridgenotifier.core.Broker
import io.github.ashitakalax.bridgenotifier.core.DayFigures
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Notification
import io.github.ashitakalax.bridgenotifier.core.ProfitHistory
import io.github.ashitakalax.bridgenotifier.core.Severity
import io.github.ashitakalax.bridgenotifier.core.Updates
import java.time.Instant
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

/**
 * The phone's notifications. Six channels, so each can be tuned in the
 * system's settings: trades, the bridge and engine, warnings, the end-of-day
 * summaries, app updates, and the quiet one the watching service needs.
 *
 * Tapping one opens its account on the page it is about (a trade on Lots, a
 * problem on Activity, readiness on Home), and each of an account's has a
 * "Mute 1 h" button; a trade has a "Lots" one too.
 */
object Alerts {
    const val CHANNEL_TRADES = "trades"
    const val CHANNEL_BRIDGE = "bridge"
    const val CHANNEL_WARNINGS = "warnings"
    const val CHANNEL_SUMMARY = "summary"
    const val CHANNEL_UPDATES = "updates"
    const val CHANNEL_MONITOR = "monitor"

    const val MONITOR_ID = 1
    private const val TEST_ID = 3
    private const val UPDATE_ID = 4

    fun createChannels(context: Context) {
        val manager = context.notificationManager
        manager.createNotificationChannels(
            listOf(
                NotificationChannel(
                    CHANNEL_TRADES,
                    context.getString(R.string.channel_trades),
                    NotificationManager.IMPORTANCE_HIGH,
                ).apply { description = context.getString(R.string.channel_trades_description) },
                NotificationChannel(
                    CHANNEL_BRIDGE,
                    context.getString(R.string.channel_bridge),
                    NotificationManager.IMPORTANCE_DEFAULT,
                ).apply { description = context.getString(R.string.channel_bridge_description) },
                NotificationChannel(
                    CHANNEL_WARNINGS,
                    context.getString(R.string.channel_warnings),
                    NotificationManager.IMPORTANCE_HIGH,
                ).apply { description = context.getString(R.string.channel_warnings_description) },
                NotificationChannel(
                    CHANNEL_SUMMARY,
                    context.getString(R.string.channel_summary),
                    NotificationManager.IMPORTANCE_DEFAULT,
                ).apply { description = context.getString(R.string.channel_summary_description) },
                NotificationChannel(
                    CHANNEL_UPDATES,
                    context.getString(R.string.channel_updates),
                    NotificationManager.IMPORTANCE_LOW,
                ).apply { description = context.getString(R.string.channel_updates_description) },
                NotificationChannel(
                    CHANNEL_MONITOR,
                    context.getString(R.string.channel_monitor),
                    NotificationManager.IMPORTANCE_MIN,
                ).apply {
                    description = context.getString(R.string.channel_monitor_description)
                    setShowBadge(false)
                },
            ),
        )
    }

    fun notificationsEnabled(context: Context): Boolean =
        context.notificationManager.areNotificationsEnabled()

    /** The watching service's own, always there while it watches. */
    fun monitorNotification(context: Context, text: String): AndroidNotification =
        AndroidNotification.Builder(context, CHANNEL_MONITOR)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(context.getString(R.string.monitor_title))
            .setContentText(text)
            .setContentIntent(open(context, MONITOR_ID, null, null))
            .setOngoing(true)
            .setShowWhen(false)
            .setCategory(AndroidNotification.CATEGORY_SERVICE)
            .build()

    fun updateMonitor(context: Context, text: String) {
        context.notificationManager
            .notify(MONITOR_ID, monitorNotification(context, text))
    }

    /** Which page a notification of [kind] opens on. */
    fun pageFor(notification: Notification): Tab = when (notification.kind) {
        EventKind.TEST -> Tab.CONNECT
        EventKind.BUY, EventKind.SELL -> Tab.LOTS
        EventKind.ORDER_UPDATE, EventKind.ORDER_PROBLEM, EventKind.WINDOW, EventKind.REFUSED -> Tab.ACTIVITY
        // Readiness, the sign-in, the account check, the extension, the engine, the session.
        else -> Tab.HOME
    }

    /**
     * One of an account's notifications, headed with the account's name --
     * and, for the latest of several missed while away, how many more came
     * (tapping that one opens all of them, on Activity).
     */
    fun post(context: Context, notification: Notification, account: Account, alsoMissed: Int = 0) {
        val channel = when {
            notification.severity != Severity.INFO -> CHANNEL_WARNINGS
            notification.kind in EventKind.TRADES -> CHANNEL_TRADES
            else -> CHANNEL_BRIDGE
        }
        val id = if (notification.isTest) {
            TEST_ID
        } else {
            1_000 + ((notification.stream.hashCode() * 31L + notification.id) and 0x3fff_ffff).toInt()
        }
        val page = if (alsoMissed > 0) Tab.ACTIVITY else pageFor(notification)
        val sale = notification.kind == EventKind.SELL
        val actions = buildList {
            if (notification.isTest) return@buildList
            if (notification.kind == EventKind.BUY || sale) {
                add(action(context, R.string.action_lots, open(context, -id, account.id, Tab.LOTS, sales = sale)))
            }
            add(muteAction(context, id, account))
        }
        show(
            context,
            id,
            channel,
            notification.title,
            notification.body,
            open(context, id, account.id, page, sales = sale && alsoMissed == 0),
            epochMillis(notification.at),
            color(context, notification.severity) ?: brokerColor(context, account),
            if (alsoMissed > 0) {
                context.resources.getQuantityString(R.plurals.missed_more, alsoMissed, account.name, alsoMissed)
            } else {
                account.name
            },
            actions,
        )
    }

    /** The app's own: an account's listener has been out of reach for a while. */
    fun postLinkLost(context: Context, account: Account, reason: String) = linkNotice(
        context,
        account,
        CHANNEL_WARNINGS,
        context.getString(R.string.link_lost_title),
        context.getString(R.string.link_lost_body, reason),
        context.getColor(R.color.status_bad),
    )

    /** ...and is back. Replaces the one above. */
    fun postLinkBack(context: Context, account: Account) = linkNotice(
        context,
        account,
        CHANNEL_BRIDGE,
        context.getString(R.string.link_back_title),
        context.getString(R.string.link_back_body),
        context.getColor(R.color.status_ok),
    )

    /** The listener refused the key, or is not one: nothing more will come from it. */
    fun postRefused(context: Context, account: Account, reason: String) = linkNotice(
        context,
        account,
        CHANNEL_WARNINGS,
        context.getString(R.string.link_refused_title),
        reason,
        context.getColor(R.color.status_bad),
    )

    private fun linkNotice(context: Context, account: Account, channel: String, title: String, body: String, color: Int) {
        val id = linkId(account)
        show(
            context,
            id,
            channel,
            title,
            body,
            open(context, id, account.id, Tab.HOME),
            color = color,
            account = account.name,
            actions = listOf(muteAction(context, id, account)),
        )
    }

    /**
     * An account's end-of-day note: what [day]'s trades made, and, for today,
     * where the open lots stand ([book]). [heard] is false when the listener
     * is out of reach and the figures are what was last heard.
     */
    fun postSummary(context: Context, account: Account, day: DayFigures, book: Book?, heard: Boolean, now: Instant) {
        val today = ProfitHistory.marketDay(now) == day.date
        val title = context.getString(
            if (today) R.string.summary_title_today else R.string.summary_title_day,
            Format.signedMoney(day.realized),
            DateTimeFormatter.ofPattern("EEE MMM d", Locale.US).format(day.date),
        )
        val parts = mutableListOf(
            context.resources.getQuantityString(R.plurals.summary_buys, day.buys, day.buys) + ", " +
                context.resources.getQuantityString(R.plurals.summary_sales, day.sales, day.sales) + ".",
        )
        if (today && book != null) {
            val open = context.resources.getQuantityString(R.plurals.summary_open, book.open.size, book.open.size)
            parts += book.unrealized?.let { context.getString(R.string.summary_open_unrealised, open, Format.signedMoney(it)) }
                ?: "$open."
        }
        if (!heard) parts += context.getString(R.string.summary_not_heard)
        val id = 700 + (account.id.hashCode() and 0xff)
        show(
            context,
            id,
            CHANNEL_SUMMARY,
            title,
            parts.joinToString(" "),
            open(context, id, account.id, Tab.HOME),
            color = brokerColor(context, account),
            account = account.name,
        )
    }

    /** A newer app is out: tapping opens its release page, in the browser. */
    fun postUpdate(context: Context, release: Updates.Release) {
        val page = PendingIntent.getActivity(
            context,
            UPDATE_ID,
            Intent(Intent.ACTION_VIEW, Uri.parse(release.page)),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        show(
            context,
            UPDATE_ID,
            CHANNEL_UPDATES,
            context.getString(R.string.update_title, release.version ?: release.tag),
            UpdateChecker.howToInstall(context, release),
            page,
        )
    }

    /** Each account's link notice replaces its own, never another account's. */
    private fun linkId(account: Account): Int = 100 + (account.id.hashCode() and 0x1ff)

    /** The colour each broker wears in the app: yellow for Alpaca, green for Fidelity. */
    fun brokerColor(context: Context, account: Account?): Int = context.getColor(
        when (account?.broker) {
            Broker.ALPACA -> R.color.alpaca_strong
            Broker.FIDELITY -> R.color.fidelity_strong
            else -> R.color.accent
        },
    )

    private fun show(
        context: Context,
        id: Int,
        channel: String,
        title: String,
        body: String,
        tap: PendingIntent,
        whenMillis: Long? = null,
        color: Int? = null,
        account: String? = null,
        actions: List<AndroidNotification.Action> = emptyList(),
    ) {
        val builder = AndroidNotification.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(AndroidNotification.BigTextStyle().bigText(body))
            .setContentIntent(tap)
            .setAutoCancel(true)
            .setShowWhen(true)
            .setWhen(whenMillis ?: System.currentTimeMillis())
        if (color != null) builder.setColor(color)
        if (account != null) builder.setSubText(account)
        actions.forEach(builder::addAction)
        context.notificationManager.notify(id, builder.build())
    }

    private fun color(context: Context, severity: Severity): Int? = when (severity) {
        Severity.CRITICAL -> context.getColor(R.color.status_bad)
        Severity.WARNING -> context.getColor(R.color.status_warn)
        Severity.INFO -> null
    }

    /**
     * The app, on [page] of [accountId] (as they are when both are null).
     * [requestCode] keeps each notification's own: Android tells pending
     * intents apart by it, not by their extras. A "Lots" button's is its
     * notification's id negated.
     */
    private fun open(context: Context, requestCode: Int, accountId: String?, page: Tab?, sales: Boolean = false): PendingIntent =
        PendingIntent.getActivity(
            context,
            requestCode,
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
                .putExtra(MainActivity.EXTRA_ACCOUNT, accountId)
                .putExtra(MainActivity.EXTRA_PAGE, page?.name)
                .putExtra(MainActivity.EXTRA_SALES, sales),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )

    /** "Mute 1 h": [account] quiet for an hour, and this notification put away. */
    private fun muteAction(context: Context, id: Int, account: Account): AndroidNotification.Action = action(
        context,
        R.string.action_mute_hour,
        PendingIntent.getBroadcast(
            context,
            id,
            Intent(context, AlertActions::class.java)
                .setAction(AlertActions.ACTION_MUTE_HOUR)
                .putExtra(AlertActions.EXTRA_ACCOUNT, account.id)
                .putExtra(AlertActions.EXTRA_NOTIFICATION, id),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        ),
    )

    private fun action(context: Context, label: Int, intent: PendingIntent): AndroidNotification.Action =
        AndroidNotification.Action.Builder(Icon.createWithResource(context, R.drawable.ic_notification), context.getString(label), intent)
            .build()

    /** Put away the notification [id], once it has been acted on. */
    fun cancel(context: Context, id: Int) {
        context.notificationManager.cancel(id)
    }

    private val Context.notificationManager: NotificationManager
        get() = getSystemService(NotificationManager::class.java)!!

    fun epochMillis(iso: String): Long? = try {
        OffsetDateTime.parse(iso).toInstant().toEpochMilli()
    } catch (_: DateTimeParseException) {
        null
    }
}
