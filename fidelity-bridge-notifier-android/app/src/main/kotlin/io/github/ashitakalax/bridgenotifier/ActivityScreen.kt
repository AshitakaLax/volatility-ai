package io.github.ashitakalax.bridgenotifier

import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Notification
import io.github.ashitakalax.bridgenotifier.core.Severity

/** What the bridge said lately, newest first, filtered by what it is about. */
class ActivityScreen(private val ui: Ui) : Screen {
    enum class Filter(val label: Int) {
        ALL(R.string.filter_all),
        TRADES(R.string.filter_trades),
        PROBLEMS(R.string.filter_problems),
        CONNECTION(R.string.filter_connection),
    }

    private var filter = Filter.ALL
    private var last: MonitorState.Snapshot? = null
    private val subtitle = ui.eyebrow("")
    private val chips = ui.row(gap = 8)
    private val list = ui.column(gap = 6)
    override val view: View

    init {
        val (scroll, page) = ui.page()
        page.addView(subtitle)
        page.addView(ui.title(ui.string(R.string.activity_title)))
        page.addView(
            HorizontalScrollView(ui.context).apply {
                isHorizontalScrollBarEnabled = false
                addView(chips)
            },
        )
        page.addView(list)
        view = scroll
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        last = snapshot
        subtitle.text = ui.string(R.string.activity_sub, MonitorState.RECENT)
        chips.removeAllViews()
        for (each in Filter.entries) {
            chips.addView(
                ui.chip(ui.string(each.label), selected = each == filter) {
                    filter = each
                    last?.let(::render)
                },
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
            )
        }
        list.removeAllViews()
        val shown = snapshot.recent.filter { groupOf(it) == filter || filter == Filter.ALL }
        if (shown.isEmpty()) {
            list.addView(ui.text(ui.string(R.string.activity_empty), color = R.color.muted).apply { gravity = Gravity.CENTER })
        }
        for (notification in shown) list.addView(item(notification))
    }

    private fun item(notification: Notification): View {
        val (glyph, ink, chip) = look(notification)
        return ui.card(padding = 12, gap = 0).apply {
            background = ui.rounded(R.color.card, radius = 12, stroke = R.color.line)
            addView(
                ui.row(gap = 12).apply {
                    gravity = Gravity.TOP
                    addView(
                        ui.text(glyph, size = 15f, color = ink, bold = true).apply {
                            gravity = Gravity.CENTER
                            background = ui.rounded(chip, radius = 10)
                        },
                        LinearLayout.LayoutParams(ui.dp(34), ui.dp(34)),
                    )
                    addView(
                        ui.grow(
                            ui.column(gap = 2).apply {
                                addView(
                                    ui.row(gap = 8).apply {
                                        addView(ui.grow(ui.text(notification.title, bold = true)))
                                        addView(
                                            ui.text(Format.clockTime(notification.at).orEmpty(), size = 12f, color = R.color.muted, mono = true),
                                            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                                        )
                                    },
                                )
                                if (notification.body.isNotEmpty()) addView(ui.text(notification.body, size = 13f, color = R.color.ink_soft))
                            },
                        ),
                    )
                },
            )
        }
    }

    private data class Look(val glyph: String, val ink: Int, val chip: Int)

    private fun look(notification: Notification): Look = when {
        notification.kind == EventKind.BUY -> Look("↑", R.color.primary_dark, R.color.accent_soft)
        notification.kind == EventKind.SELL -> Look("↓", R.color.status_ok, R.color.status_ok_soft)
        notification.severity == Severity.CRITICAL -> Look("!", R.color.status_bad, R.color.status_bad_soft)
        notification.severity == Severity.WARNING -> Look("!", R.color.status_warn, R.color.status_warn_soft)
        else -> Look("•", R.color.ink_soft, R.color.line)
    }

    companion object {
        /** Which filter a notification falls under (besides All). */
        fun groupOf(notification: Notification): Filter = when {
            notification.kind == EventKind.BUY || notification.kind == EventKind.SELL ||
                notification.kind == EventKind.ORDER_UPDATE || notification.kind == EventKind.WINDOW -> Filter.TRADES
            notification.kind == EventKind.ORDER_PROBLEM || notification.severity != Severity.INFO -> Filter.PROBLEMS
            else -> Filter.CONNECTION
        }
    }
}
