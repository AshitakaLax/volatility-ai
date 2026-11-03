package io.github.ashitakalax.bridgenotifier

import android.content.res.ColorStateList
import android.text.format.DateUtils
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.LinearLayout
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.EventKind

/** One of the app's pages: a view, redrawn from each snapshot. */
interface Screen {
    val view: View

    fun render(snapshot: MonitorState.Snapshot)
}

/**
 * The connection at a glance: ready to trade or the one thing to fix, the
 * readiness chain, today's profit, the day's counts, the trading session and
 * the latest trade.
 */
class HomeScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val go: (Tab) -> Unit,
) : Screen {
    private val eyebrow = ui.eyebrow("")
    private val content = ui.column(gap = 12)
    override val view: View

    init {
        val (scroll, page) = ui.page()
        val settings = ImageButton(ui.context).apply {
            setImageResource(R.drawable.ic_settings)
            imageTintList = ColorStateList.valueOf(ui.color(R.color.ink_soft))
            background = ui.rounded(R.color.card, radius = 12, stroke = R.color.line)
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
                        },
                    ),
                )
                addView(settings, LinearLayout.LayoutParams(ui.dp(48), ui.dp(48)))
            },
        )
        page.addView(content)
        view = scroll
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        val status = snapshot.status
        val host = status.bridge
        val book = status.book
        eyebrow.text = listOfNotNull("Fidelity", host?.symbol ?: book?.symbol).joinToString(" · ")
        content.removeAllViews()
        content.addView(hero(snapshot))

        val connected = snapshot.link is BridgeClient.Link.Connected
        if (host != null && host.items.isNotEmpty()) {
            content.addView(
                ui.card(padding = 12, gap = 0).apply {
                    setPadding(ui.dp(16), ui.dp(4), ui.dp(16), ui.dp(4))
                    host.items.forEachIndexed { index, item ->
                        val (mark, fill) = if (!connected) {
                            "?" to R.color.status_idle
                        } else {
                            when (item.state) {
                                "ok" -> "✓" to R.color.status_ok
                                "warn" -> "!" to R.color.status_warn
                                "fail" -> "✗" to R.color.status_bad
                                else -> "?" to R.color.status_idle
                            }
                        }
                        addView(
                            ui.row(gap = 12).apply {
                                minimumHeight = ui.dp(48)
                                setPadding(0, ui.dp(6), 0, ui.dp(6))
                                addView(ui.mark(mark, fill))
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
        content.addView(session(snapshot))
        latestTrade(snapshot)?.let(content::addView)
    }

    private fun hero(snapshot: MonitorState.Snapshot): View {
        val host = snapshot.status.bridge
        val link = snapshot.link
        data class Hero(val fill: Int, val tag: String, val title: String, val detail: String)
        val hero = when {
            link is BridgeClient.Link.Refused -> Hero(R.color.status_bad, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_refused_title), link.reason)
            link is BridgeClient.Link.Waiting && link.deliberate -> Hero(R.color.status_offline, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_restarting_title), link.reason)
            link is BridgeClient.Link.Waiting -> Hero(R.color.status_offline, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_offline_title), link.reason)
            link == BridgeClient.Link.Connecting -> Hero(R.color.status_offline, ui.string(R.string.hero_connecting_tag), ui.string(R.string.hero_connecting_title, MonitorService.hostOf(prefs.url)), "")
            link !is BridgeClient.Link.Connected -> Hero(R.color.status_offline, ui.string(R.string.hero_idle_tag), ui.string(R.string.hero_idle_title), ui.string(R.string.hero_idle_detail))
            host == null -> Hero(R.color.status_offline, ui.string(R.string.hero_unknown_tag), ui.string(R.string.hero_unknown_title), ui.string(R.string.hero_unknown_detail))
            host.ready -> Hero(R.color.status_ok, ui.string(R.string.hero_ready_tag), ui.string(R.string.hero_ready_title), ui.string(R.string.hero_ready_detail))
            else -> Hero(R.color.status_bad, ui.string(R.string.hero_blocked_tag), host.summary, host.fix?.let { ui.string(R.string.hero_fix, it) }.orEmpty())
        }
        return ui.column(gap = 6).apply {
            background = ui.rounded(hero.fill, radius = 16)
            setPadding(ui.dp(18), ui.dp(18), ui.dp(18), ui.dp(18))
            addView(ui.text(hero.tag, size = 13f, color = R.color.card, bold = true).apply { isAllCaps = true; letterSpacing = 0.04f })
            addView(ui.text(hero.title, size = 22f, color = R.color.card, bold = true))
            if (hero.detail.isNotEmpty()) addView(ui.text(hero.detail, color = R.color.card))
            if (link == BridgeClient.Link.Idle || link == BridgeClient.Link.Stopped) setOnClickListener { go(Tab.CONNECT) }
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
            setOnClickListener { go(Tab.LOTS) }
        }
    }

    private fun tile(label: String, value: Int?, target: Tab): View = ui.card(padding = 12, gap = 2).apply {
        addView(ui.text(label, size = 12f, color = R.color.muted))
        addView(ui.text(value?.toString() ?: "—", size = 22f, mono = true))
        layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        isClickable = true
        setOnClickListener { go(target) }
    }

    private fun session(snapshot: MonitorState.Snapshot): View {
        val engine = snapshot.status.engine
        val host = snapshot.status.bridge
        val (state, fill, soft) = when (engine?.state) {
            "running" -> Triple("Running", R.color.status_ok, R.color.status_ok_soft)
            "paused" -> Triple("Paused", R.color.status_warn, R.color.status_warn_soft)
            "halted" -> Triple("Halted", R.color.status_bad, R.color.status_bad_soft)
            null -> Triple("Idle", R.color.status_offline, R.color.line)
            else -> Triple(engine?.state.orEmpty().replaceFirstChar(Char::uppercase), R.color.status_offline, R.color.line)
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
            val line = when {
                engine != null -> listOfNotNull(engine.mode, engine.symbol, engine.detail).joinToString(" · ")
                host != null && !host.sessionOpen -> ui.string(R.string.session_closed, ago(host.nextOpen))
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
                        ui.text(if (buy) "↑" else "↓", size = 16f, color = if (buy) R.color.primary_dark else R.color.status_ok, bold = true).apply {
                            gravity = Gravity.CENTER
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
            setOnClickListener { go(Tab.ACTIVITY) }
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

    private fun ago(iso: String?): String {
        val millis = iso?.let(Alerts::epochMillis) ?: return ui.string(R.string.unknown)
        return DateUtils.getRelativeTimeSpanString(millis).toString()
    }
}
