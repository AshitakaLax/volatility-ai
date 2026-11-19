package io.github.ashitakalax.bridgenotifier

import android.content.res.ColorStateList
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.LinearLayout
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.Book
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.DayFigures
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.ProfitHistory
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.util.Locale

/** One of the app's pages: a view, redrawn from each snapshot. */
interface Screen {
    val view: View

    fun render(snapshot: MonitorState.Snapshot)

    /** What the page was showing, for when the activity is rebuilt (turned, the phone gone dark). */
    fun save(state: Bundle) {}

    fun restore(state: Bundle) {}
}

/**
 * The account shown, at a glance: for Fidelity, ready to trade or the one
 * thing to fix and the readiness chain; for Alpaca, what its trader says it is
 * doing -- and whether that is live or when it was last heard. Then today's
 * profit, the day's counts, what the account is worth and has free to trade,
 * the profit history day by day, the trading session and the latest trade.
 */
class HomeScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val go: (Tab) -> Unit,
) : Screen {
    /** The history's span: two weeks, a month, three months, a year. */
    private enum class Span(val days: Long, val label: Int) {
        TWO_WEEKS(14, R.string.span_2w),
        MONTH(31, R.string.span_1m),
        QUARTER(92, R.string.span_3m),
        YEAR(366, R.string.span_1y),
    }

    private val eyebrow = ui.eyebrow("")
    private val freshness = ui.text(size = 12f, bold = true)
    private val content = ui.column(gap = 12)
    private var span = Span.MONTH
    private var last: MonitorState.Snapshot? = null
    private val chart = HistoryChart(ui)
    private val picked = ui.text(size = 12f, color = R.color.ink_soft, mono = true)
    private val dayFormat = DateTimeFormatter.ofPattern("EEE MMM d", Locale.US)
    override val view: View

    init {
        val (scroll, page) = ui.page()
        val settings = ImageButton(ui.context).apply {
            setImageResource(R.drawable.ic_settings)
            imageTintList = ColorStateList.valueOf(ui.color(R.color.ink_soft))
            background = ui.pressable(ui.rounded(R.color.card, radius = 12, stroke = R.color.line))
            contentDescription = ui.string(R.string.settings)
            setOnClickListener { go(Tab.CONNECT) }
        }
        page.addView(
            ui.row(gap = 12).apply {
                addView(
                    ui.grow(
                        ui.column().apply {
                            addView(eyebrow)
                            addView(ui.title(ui.string(R.string.home_title)))
                            addView(freshness)
                        },
                    ),
                )
                addView(settings, LinearLayout.LayoutParams(ui.dp(48), ui.dp(48)))
            },
        )
        page.addView(content)
        view = scroll
        chart.onPick = { day -> picked.text = pickedLine(day) }
    }

    override fun save(state: Bundle) {
        state.putString(SPAN, span.name)
    }

    override fun restore(state: Bundle) {
        span = Span.entries.firstOrNull { it.name == state.getString(SPAN) } ?: span
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        val status = snapshot.status
        val host = status.bridge
        val book = status.book
        last = snapshot
        eyebrow.text = eyebrowLine(snapshot.account, host?.symbol ?: book?.symbol)
        val state = snapshot.stateOf(snapshot.account?.id)
        val (fresh, freshColor) = Verdict.freshness(ui, state, snapshot.account?.id?.let(prefs::heardAt))
        freshness.text = ui.string(R.string.fresh_dot, fresh)
        freshness.setTextColor(ui.color(freshColor))
        freshness.visibility = if (snapshot.account == null) View.GONE else View.VISIBLE
        content.removeAllViews()
        content.addView(hero(snapshot))

        val connected = snapshot.link is BridgeClient.Link.Connected
        if (host != null && host.items.isNotEmpty()) {
            content.addView(
                ui.card(padding = 12, gap = 0).apply {
                    setPadding(ui.dp(16), ui.dp(4), ui.dp(16), ui.dp(4))
                    host.items.forEachIndexed { index, item ->
                        val (mark, fill, said) = when (if (connected) item.state else "unknown") {
                            "ok" -> Triple("✓", R.color.status_ok_fill, R.string.mark_ok)
                            "warn" -> Triple("!", R.color.status_warn_fill, R.string.mark_warn)
                            "fail" -> Triple("✗", R.color.status_bad_fill, R.string.mark_fail)
                            else -> Triple("?", R.color.status_idle_fill, R.string.mark_unknown)
                        }
                        addView(
                            ui.row(gap = 12).apply {
                                minimumHeight = ui.dp(48)
                                setPadding(0, ui.dp(6), 0, ui.dp(6))
                                addView(ui.mark(mark, fill, ui.string(said)))
                                addView(
                                    ui.grow(
                                        ui.column().apply {
                                            addView(ui.text(item.label, bold = true))
                                            addView(ui.text(item.detail, size = 12f, color = R.color.muted))
                                        },
                                    ),
                                )
                            },
                        )
                        if (index < host.items.size - 1) addView(rule())
                    }
                },
            )
        }

        content.addView(profit(snapshot))
        content.addView(
            ui.row(gap = 8).apply {
                addView(tile(ui.string(R.string.tile_open), book?.open?.size, Tab.LOTS))
                addView(tile(ui.string(R.string.tile_buys), book?.buysToday, Tab.ACTIVITY))
                addView(tile(ui.string(R.string.tile_sells), book?.salesToday, Tab.ACTIVITY))
            },
        )
        if (snapshot.account != null) content.addView(funds(book))
        snapshot.account?.let { content.addView(history(it.id)) }
        content.addView(session(snapshot))
        latestTrade(snapshot)?.let(content::addView)
    }

    /**
     * The profit history: each trading day's realised profit over the span
     * picked, its total and best and worst days, and the day touched.
     */
    private fun history(id: String): View {
        val today = ProfitHistory.marketDay(Instant.now())
        val days = ProfitHistory.since(prefs.history(id), today.minusDays(span.days - 1))
        return ui.card(padding = 16, gap = 8).apply {
            addView(ui.label(ui.string(R.string.history_header)))
            addView(
                ui.row(gap = 6).apply {
                    for (each in Span.entries) {
                        addView(
                            ui.chip(ui.string(each.label), selected = each == span) {
                                span = each
                                last?.let(::render)
                            },
                            LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f),
                        )
                    }
                },
            )
            if (days.isEmpty()) {
                addView(ui.text(ui.string(R.string.history_empty), size = 13f, color = R.color.muted))
                addView(ui.text(ui.string(R.string.history_kept), size = 12f, color = R.color.muted))
                return@apply
            }
            val total = days.sumOf { it.realized }
            addView(
                ui.row(gap = 8).apply {
                    gravity = Gravity.BOTTOM
                    addView(ui.text(Format.signedMoney(total), size = 22f, color = gainColor(total), mono = true))
                    addView(
                        ui.grow(
                            ui.text(
                                ui.context.resources.getQuantityString(R.plurals.history_over, days.size, days.size),
                                size = 12f,
                                color = R.color.muted,
                            ),
                        ),
                    )
                },
            )
            val best = days.maxBy { it.realized }
            val worst = days.minBy { it.realized }
            addView(
                ui.text(
                    ui.string(R.string.history_best_worst, Format.signedMoney(best.realized), dayFormat.format(best.date), Format.signedMoney(worst.realized), dayFormat.format(worst.date)),
                    size = 12f,
                    color = R.color.muted,
                ),
            )
            (chart.parent as? ViewGroup)?.removeView(chart)
            (picked.parent as? ViewGroup)?.removeView(picked)
            chart.days = days
            picked.text = pickedLine(chart.pickedDay)
            addView(chart)
            addView(picked)
            addView(ui.text(ui.string(R.string.history_kept), size = 12f, color = R.color.muted))
        }
    }

    /** "Tue Nov 3: +$8.72 · 4 sales, 7 buys". */
    private fun pickedLine(day: DayFigures?): String = day?.let {
        ui.string(
            R.string.history_picked,
            dayFormat.format(it.date),
            Format.signedMoney(it.realized),
            ui.context.resources.getQuantityString(R.plurals.summary_sales, it.sales, it.sales),
            ui.context.resources.getQuantityString(R.plurals.summary_buys, it.buys, it.buys),
        )
    }.orEmpty()

    /** "Alpaca · Ultimate (paper) · TQQQ", "Fidelity · RSP". */
    private fun eyebrowLine(account: Account?, symbol: String?): String {
        val label = account?.label?.takeIf { it.isNotBlank() && it != account.broker.label }
        val broker = account?.let { if (label == null) it.brokerLine else it.broker.label }
        return listOfNotNull(broker, label, symbol).joinToString(" · ")
    }

    private fun hero(snapshot: MonitorState.Snapshot): View {
        val hero = Verdict.of(ui, prefs, snapshot.account, snapshot.stateOf(snapshot.account?.id))
        return ui.column(gap = 6).apply {
            background = ui.rounded(hero.fill, radius = 16)
            setPadding(ui.dp(18), ui.dp(18), ui.dp(18), ui.dp(18))
            addView(ui.text(hero.tag, size = 13f, color = R.color.on_fill, bold = true).apply { isAllCaps = true; letterSpacing = 0.04f })
            addView(ui.text(hero.title, size = 22f, color = R.color.on_fill, bold = true))
            if (hero.detail.isNotEmpty()) addView(ui.text(hero.detail, color = R.color.on_fill))
            when (hero.action) {
                Verdict.Action.CONNECT -> ui.tappable(this) { go(Tab.CONNECT) }
                Verdict.Action.RETRY -> ui.tappable(this) { MonitorService.retry(ui.context) }
                Verdict.Action.WATCH -> ui.tappable(this) {
                    prefs.monitoring = true
                    MonitorService.start(ui.context)
                }
                null -> Unit
            }
        }
    }

    private fun profit(snapshot: MonitorState.Snapshot): View {
        val book = snapshot.status.book
        return ui.card(padding = 16, gap = 2).apply {
            addView(
                ui.row(gap = 12).apply {
                    gravity = Gravity.BOTTOM
                    addView(
                        ui.grow(
                            ui.column(gap = 2).apply {
                                addView(ui.label(ui.string(R.string.profit_today)))
                                if (book == null) {
                                    addView(ui.text("—", size = 30f, mono = true))
                                    addView(ui.text(ui.string(R.string.profit_none), size = 12f, color = R.color.muted))
                                } else {
                                    addView(ui.text(Format.signedMoney(book.realizedToday), size = 30f, color = gainColor(book.realizedToday), mono = true))
                                    addView(ui.text(ui.string(R.string.profit_detail, book.salesToday), size = 12f, color = R.color.muted))
                                }
                            },
                        ),
                    )
                    val unrealized = book?.unrealized
                    if (unrealized != null) {
                        addView(
                            ui.column(gap = 2).apply {
                                gravity = Gravity.END
                                addView(ui.text(ui.string(R.string.unrealized_label), size = 12f, color = R.color.muted))
                                addView(ui.text(Format.signedMoney(unrealized), size = 15f, color = gainColor(unrealized), mono = true).apply { gravity = Gravity.END })
                            },
                            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                        )
                    }
                },
            )
            ui.tappable(this) { go(Tab.LOTS) }
        }
    }

    /**
     * The account's value, what of it is free to trade and what share that
     * is, from the trader's ledger (the book's funds): the money it manages,
     * which at a broker may be less than the whole account.
     */
    private fun funds(book: Book?): View = ui.card(padding = 16, gap = 6).apply {
        val funds = book?.funds
        val lots = book?.open?.size ?: 0
        addView(ui.label(ui.string(R.string.funds_value)))
        if (funds == null) {
            addView(ui.text("—", size = 26f, mono = true))
            addView(ui.text(ui.string(R.string.funds_none), size = 12f, color = R.color.muted))
            return@apply
        }
        addView(ui.text(funds.value?.let(Format::money) ?: "—", size = 26f, mono = true))
        // What it can spend now, and beside it the sales still settling: the
        // cash that is the account's but not yet to spend (T+1 at Fidelity).
        addView(
            ui.row(gap = 12).apply {
                gravity = Gravity.TOP
                addView(
                    ui.grow(
                        ui.column(gap = 2).apply {
                            addView(ui.text(ui.string(R.string.funds_available), size = 13f, color = R.color.ink_soft))
                            addView(ui.text(Format.money(funds.available), size = 17f, bold = true, mono = true))
                        },
                    ),
                )
                addView(
                    ui.column(gap = 2).apply {
                        gravity = Gravity.END
                        addView(ui.text(ui.string(R.string.funds_unsettled), size = 13f, color = R.color.ink_soft).apply { gravity = Gravity.END })
                        addView(ui.text(Format.money(funds.unsettled), size = 17f, mono = true).apply { gravity = Gravity.END })
                    },
                    LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                )
            },
        )
        val share = funds.availableShare
        if (share != null) {
            addView(shareBar(share))
            addView(ui.text(ui.string(R.string.funds_share, Format.share(share)), size = 12f, color = R.color.ink_soft))
        }
        val small = listOfNotNull(
            if (funds.value == null) ui.string(R.string.funds_no_price) else null,
            funds.invested?.takeIf { lots > 0 }?.let {
                ui.context.resources.getQuantityString(R.plurals.funds_invested, lots, Format.money(it), lots)
            },
        ).joinToString(" · ")
        if (small.isNotEmpty()) addView(ui.text(small, size = 12f, color = R.color.muted))
        addView(ui.text(ui.string(R.string.funds_whose), size = 12f, color = R.color.muted))
        ui.tappable(this) { go(Tab.LOTS) }
    }

    /** A bar filled to [fraction]: the share of the value free to trade. */
    private fun shareBar(fraction: Double): View = LinearLayout(ui.context).apply {
        orientation = LinearLayout.HORIZONTAL
        background = ui.rounded(R.color.track, radius = 4)
        contentDescription = ui.string(R.string.funds_share, Format.share(fraction))
        val filled = fraction.toFloat().coerceIn(0.001f, 0.999f)
        addView(View(ui.context).apply { background = ui.rounded(R.color.accent_fill, radius = 4) }, LinearLayout.LayoutParams(0, ui.dp(8), filled))
        addView(View(ui.context), LinearLayout.LayoutParams(0, ui.dp(8), 1f - filled))
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ui.dp(8))
    }

    private fun tile(label: String, value: Int?, target: Tab): View = ui.card(padding = 12, gap = 2).apply {
        addView(ui.text(label, size = 12f, color = R.color.muted))
        addView(ui.text(value?.toString() ?: "—", size = 22f, mono = true))
        layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        contentDescription = "$label: ${value ?: ui.string(R.string.unknown)}"
        ui.tappable(this) { go(target) }
    }

    private fun session(snapshot: MonitorState.Snapshot): View {
        val engine = snapshot.status.engine
        val host = snapshot.status.bridge
        val (state, fill, soft) = when (engine?.state) {
            "running" -> Triple("Running", R.color.status_ok, R.color.status_ok_soft)
            "paused" -> Triple("Paused", R.color.status_warn, R.color.status_warn_soft)
            "halted", "recovery_required" -> Triple("Halted", R.color.status_bad, R.color.status_bad_soft)
            null -> Triple("Idle", R.color.ink_soft, R.color.line)
            else -> Triple(engine?.state.orEmpty().replace('_', ' ').replaceFirstChar(Char::uppercase), R.color.ink_soft, R.color.line)
        }
        return ui.card(padding = 16, gap = 6).apply {
            addView(
                ui.row().apply {
                    addView(ui.grow(ui.label(ui.string(R.string.session_header))))
                    addView(
                        ui.text(state, size = 12f, color = fill, bold = true).apply {
                            background = ui.rounded(soft, radius = 10)
                            setPadding(ui.dp(10), ui.dp(3), ui.dp(10), ui.dp(3))
                        },
                        LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                    )
                },
            )
            val trader = snapshot.status.trader
            val line = when {
                engine != null -> listOfNotNull(engine.mode, engine.symbol, engine.detail).joinToString(" · ")
                host != null && !host.sessionOpen -> ui.string(R.string.session_closed, ago(host.nextOpen))
                trader?.nextOpen != null && !trader.running -> ui.string(R.string.session_closed, ago(trader.nextOpen))
                else -> ui.string(R.string.session_none)
            }
            addView(ui.text(line))
            val check = host?.lastCheck
            val small = listOfNotNull(
                engine?.lastTickAt?.let { ui.string(R.string.session_last_tick, Format.clockTime(it) ?: ago(it)) },
                when {
                    host == null -> null
                    check == null -> ui.string(R.string.check_never)
                    check.ok -> ui.string(R.string.check_passed, ago(check.at))
                    else -> ui.string(R.string.check_failed, ago(check.at), check.detail)
                },
            ).joinToString(" · ")
            if (small.isNotEmpty()) addView(ui.text(small, size = 12f, color = if (check != null && !check.ok) R.color.status_bad else R.color.muted))
        }
    }

    private fun latestTrade(snapshot: MonitorState.Snapshot): View? {
        val trade = snapshot.recent.firstOrNull { it.kind == EventKind.BUY || it.kind == EventKind.SELL } ?: return null
        val buy = trade.kind == EventKind.BUY
        return ui.card(padding = 14, gap = 0).apply {
            addView(
                ui.row(gap = 12).apply {
                    addView(
                        ui.text(if (buy) "↑" else "↓", size = 16f, color = if (buy) R.color.accent else R.color.status_ok, bold = true).apply {
                            gravity = Gravity.CENTER
                            contentDescription = ui.string(if (buy) R.string.glyph_buy else R.string.glyph_sell)
                            background = ui.rounded(if (buy) R.color.accent_soft else R.color.status_ok_soft, radius = 10)
                        },
                        LinearLayout.LayoutParams(ui.dp(36), ui.dp(36)),
                    )
                    addView(
                        ui.grow(
                            ui.column().apply {
                                addView(ui.text(trade.title, bold = true))
                                addView(ui.text(listOfNotNull(sellsAt(trade.body), Format.clockTime(trade.at)).joinToString(" · "), size = 12f, color = R.color.muted))
                            },
                        ),
                    )
                    addView(ui.text(ui.string(R.string.see_all), size = 13f, color = R.color.accent, bold = true), LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
                },
            )
            ui.tappable(this) { go(Tab.ACTIVITY) }
        }
    }

    /** "Sells at $222.18" out of a buy's body, when the bridge said it. */
    private fun sellsAt(body: String): String? = Regex("Sells at \\$[0-9,.]+[0-9]").find(body)?.value

    private fun gainColor(value: Double): Int = when {
        value > 0 -> R.color.status_ok
        value < 0 -> R.color.status_bad
        else -> R.color.ink
    }

    private fun rule(): View = View(ui.context).apply {
        setBackgroundColor(ui.color(R.color.line))
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ui.dp(1))
    }

    private fun ago(iso: String?): String = Format.ago(iso) ?: ui.string(R.string.unknown)

    private companion object {
        const val SPAN = "home_span"
    }
}
