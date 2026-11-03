package io.github.ashitakalax.bridgenotifier

import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import io.github.ashitakalax.bridgenotifier.core.Book
import io.github.ashitakalax.bridgenotifier.core.ClosedLot
import io.github.ashitakalax.bridgenotifier.core.OpenLot

/**
 * The lots, from the bridge's book: the open ones with where each sells and
 * how far it has to go, or the last 20 sales with what each made.
 */
class LotsScreen(private val ui: Ui) : Screen {
    private enum class Show { OPEN, CLOSED }

    private var show = Show.OPEN
    private var last: MonitorState.Snapshot? = null
    private val eyebrow = ui.eyebrow("")
    private val filters = ui.row(gap = 6)
    private val summary = ui.row()
    private val list = ui.column(gap = 8)
    override val view: View

    init {
        val (scroll, page) = ui.page()
        page.addView(eyebrow)
        page.addView(ui.title(ui.string(R.string.lots_title)))
        filters.background = ui.rounded(R.color.line, radius = 12)
        filters.setPadding(ui.dp(4), ui.dp(4), ui.dp(4), ui.dp(4))
        page.addView(filters)
        page.addView(summary)
        page.addView(list)
        view = scroll
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        last = snapshot
        val book = snapshot.status.book
        eyebrow.text = listOfNotNull(
            "Fidelity",
            book?.symbol,
            book?.lastPrice?.let { "last ${Format.money(it)}" },
        ).joinToString(" · ")
        filters.removeAllViews()
        filters.addView(segment(ui.string(R.string.lots_open, book?.open?.size ?: 0), Show.OPEN))
        filters.addView(segment(ui.string(R.string.lots_closed, book?.closed?.size ?: 0), Show.CLOSED))
        summary.removeAllViews()
        list.removeAllViews()
        if (book == null) {
            list.addView(ui.text(ui.string(R.string.lots_no_book), color = R.color.muted))
            return
        }
        when (show) {
            Show.OPEN -> showOpen(book)
            Show.CLOSED -> showClosed(book)
        }
    }

    private fun segment(label: String, which: Show): View {
        val on = show == which
        return ui.text(label, color = if (on) R.color.ink else R.color.ink_soft, bold = on).apply {
            gravity = Gravity.CENTER
            minHeight = ui.dp(40)
            background = if (on) ui.rounded(R.color.card, radius = 9) else null
            isClickable = true
            isFocusable = true
            isSelected = on
            setOnClickListener {
                show = which
                last?.let(::render)
            }
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
    }

    private fun summaryLine(left: String, right: String?, value: Double?) {
        summary.addView(ui.grow(ui.text(left, size = 13f, color = R.color.ink_soft)))
        if (right != null) {
            summary.addView(
                ui.text(right, size = 13f, color = gainColor(value ?: 0.0), mono = true),
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
            )
        }
    }

    private fun showOpen(book: Book) {
        summaryLine(
            ui.string(R.string.lots_summary_open, book.open.size, Format.money(book.openCost)),
            book.unrealized?.let { ui.string(R.string.lots_unrealised, Format.signedMoney(it)) },
            book.unrealized,
        )
        if (book.open.isEmpty()) list.addView(ui.text(ui.string(R.string.lots_empty_open), color = R.color.muted))
        for (lot in book.open) list.addView(openCard(lot, book.lastPrice))
    }

    private fun showClosed(book: Book) {
        val realized = book.closed.mapNotNull { it.pnl }.sum()
        summaryLine(
            ui.string(R.string.lots_summary_closed, book.closed.size),
            ui.string(R.string.lots_realised, Format.signedMoney(realized)),
            realized,
        )
        if (book.closed.isEmpty()) list.addView(ui.text(ui.string(R.string.lots_empty_closed), color = R.color.muted))
        for (lot in book.closed) list.addView(closedCard(lot))
    }

    private fun openCard(lot: OpenLot, last: Double?): View = ui.card(padding = 14, gap = 8).apply {
        addView(
            between(
                ui.text(ui.string(R.string.lot_open_line, Format.shares(lot.qty), Format.money(lot.buyPrice)), bold = true),
                ui.text(Format.clockTime(lot.boughtAt).orEmpty(), size = 12f, color = R.color.muted),
            ),
        )
        val progress = progress(lot, last)
        addView(
            between(
                ui.text(ui.string(R.string.sells_at, Format.money(lot.targetPrice)), size = 13f, color = R.color.ink_soft),
                ui.text(
                    when {
                        last == null -> ""
                        last >= lot.targetPrice -> ui.string(R.string.at_target)
                        else -> ui.string(R.string.to_go, Format.percent((lot.targetPrice / last - 1) * 100))
                    },
                    size = 12f,
                    color = R.color.muted,
                ),
            ),
        )
        if (progress != null) addView(bar(progress))
    }

    /** How far from its buy price to its target the last price has come, 0 to 1. */
    private fun progress(lot: OpenLot, last: Double?): Float? {
        if (last == null || lot.targetPrice <= lot.buyPrice) return null
        return ((last - lot.buyPrice) / (lot.targetPrice - lot.buyPrice)).coerceIn(0.0, 1.0).toFloat()
    }

    private fun bar(fraction: Float): View = LinearLayout(ui.context).apply {
        orientation = LinearLayout.HORIZONTAL
        background = ui.rounded(R.color.track, radius = 3)
        contentDescription = "${(fraction * 100).toInt()}% of the way to its target"
        addView(
            View(ui.context).apply { background = ui.rounded(if (fraction > 0f) R.color.status_ok else R.color.status_idle, radius = 3) },
            LinearLayout.LayoutParams(0, ui.dp(6), fraction.coerceAtLeast(0.001f)),
        )
        addView(View(ui.context), LinearLayout.LayoutParams(0, ui.dp(6), (1f - fraction).coerceAtLeast(0.001f)))
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ui.dp(6))
    }

    private fun closedCard(lot: ClosedLot): View = ui.card(padding = 14, gap = 6).apply {
        val bought = lot.buyPrice?.let(Format::money) ?: "?"
        addView(
            between(
                ui.text(ui.string(R.string.lot_closed_line, Format.shares(lot.qty), bought, Format.money(lot.sellPrice)), bold = true),
                ui.text(lot.pnl?.let(Format::signedMoney) ?: "", color = gainColor(lot.pnl ?: 0.0), bold = true, mono = true),
            ),
        )
        val why = ui.string(if (lot.reason == "signal_exit") R.string.reason_signal else R.string.reason_target)
        val held = Format.duration(lot.boughtAt, lot.soldAt)?.let { ui.string(R.string.held, it) }
        addView(
            between(
                ui.text(listOfNotNull(why, held).joinToString(" · "), size = 12f, color = R.color.muted),
                ui.text(Format.clockTime(lot.soldAt).orEmpty(), size = 12f, color = R.color.muted),
            ),
        )
    }

    /** Two texts on one line, the first taking the room. */
    private fun between(start: View, end: View): View = ui.row(gap = 8).apply {
        addView(ui.grow(start))
        addView(end, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    private fun gainColor(value: Double): Int = when {
        value > 0 -> R.color.status_ok
        value < 0 -> R.color.status_bad
        else -> R.color.ink
    }
}
