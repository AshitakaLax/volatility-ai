package io.github.ashitakalax.bridgenotifier

import android.app.Notification as AndroidNotification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Notification
import io.github.ashitakalax.bridgenotifier.core.Severity
import java.time.OffsetDateTime
import java.time.format.DateTimeParseException

/**
 * The phone's notifications. Four channels, so each can be tuned in the
 * system's settings: trades, the bridge and engine, warnings, and the quiet
 * one the watching service needs.
 */
object Alerts {
    const val CHANNEL_TRADES = "trades"
    const val CHANNEL_BRIDGE = "bridge"
    const val CHANNEL_WARNINGS = "warnings"
    const val CHANNEL_MONITOR = "monitor"

    const val MONITOR_ID = 1
    private const val LINK_ID = 2
    private const val TEST_ID = 3

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
            .setContentIntent(openApp(context))
            .setOngoing(true)
            .setShowWhen(false)
            .setCategory(AndroidNotification.CATEGORY_SERVICE)
            .build()

    fun updateMonitor(context: Context, text: String) {
        context.notificationManager
            .notify(MONITOR_ID, monitorNotification(context, text))
    }

    /** One of the bridge's notifications. */
    fun post(context: Context, notification: Notification) {
        val channel = when {
            notification.severity != Severity.INFO -> CHANNEL_WARNINGS
            notification.kind in setOf(EventKind.BUY, EventKind.SELL, EventKind.ORDER_UPDATE) -> CHANNEL_TRADES
            else -> CHANNEL_BRIDGE
        }
        val id = if (notification.isTest) {
            TEST_ID
        } else {
            1_000 + ((notification.stream.hashCode() * 31L + notification.id) and 0x3fff_ffff).toInt()
        }
        show(
            context,
            id,
            channel,
            notification.title,
            notification.body,
            epochMillis(notification.at),
            color(context, notification.severity),
        )
    }

    /** The app's own: the bridge has been out of reach for a while. */
    fun postLinkLost(context: Context, reason: String) = show(
        context,
        LINK_ID,
        CHANNEL_WARNINGS,
        context.getString(R.string.link_lost_title),
        context.getString(R.string.link_lost_body, reason),
        color = context.getColor(R.color.status_bad),
    )

    /** ...and is back. Replaces the one above. */
    fun postLinkBack(context: Context) = show(
        context,
        LINK_ID,
        CHANNEL_BRIDGE,
        context.getString(R.string.link_back_title),
        context.getString(R.string.link_back_body),
        color = context.getColor(R.color.status_ok),
    )

    /** The bridge refused the key, or is not a bridge: nothing more will come. */
    fun postRefused(context: Context, reason: String) = show(
        context,
        LINK_ID,
        CHANNEL_WARNINGS,
        context.getString(R.string.link_refused_title),
        reason,
        color = context.getColor(R.color.status_bad),
    )

    private fun show(
        context: Context,
        id: Int,
        channel: String,
        title: String,
        body: String,
        whenMillis: Long? = null,
        color: Int? = null,
    ) {
        val builder = AndroidNotification.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(AndroidNotification.BigTextStyle().bigText(body))
            .setContentIntent(openApp(context))
            .setAutoCancel(true)
            .setShowWhen(true)
            .setWhen(whenMillis ?: System.currentTimeMillis())
        if (color != null) builder.setColor(color)
        context.notificationManager.notify(id, builder.build())
    }

    private fun color(context: Context, severity: Severity): Int? = when (severity) {
        Severity.CRITICAL -> context.getColor(R.color.status_bad)
        Severity.WARNING -> context.getColor(R.color.status_warn)
        Severity.INFO -> null
    }

    private fun openApp(context: Context): PendingIntent = PendingIntent.getActivity(
        context,
        0,
        Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )

    private val Context.notificationManager: NotificationManager
        get() = getSystemService(NotificationManager::class.java)!!

    fun epochMillis(iso: String): Long? = try {
        OffsetDateTime.parse(iso).toInstant().toEpochMilli()
    } catch (_: DateTimeParseException) {
        null
    }
}
