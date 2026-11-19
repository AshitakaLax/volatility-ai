package io.github.ashitakalax.bridgenotifier

import android.content.res.ColorStateList
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.LinearLayout
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.Funds

/**
 * Every account on one page, with more than one: today's totals and what
 * the accounts are worth and have free to trade -- real money and paper
 * apart, never added together -- then a card each with its state, how fresh
 * that is, its day so far and its funds. Tapping a card opens that account's
 * Home.
 */
class OverviewScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val open: (Account) -> Unit,
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
                            addView(ui.title(ui.string(R.string.overview_title)))
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
        eyebrow.text = ui.context.resources.getQuantityString(R.plurals.overview_count, snapshot.accounts.size, snapshot.accounts.size)
        content.removeAllViews()
        // Paper first only when there is no real money: real money leads.
        val groups = snapshot.accounts.groupBy { it.paper == true }.toSortedMap()
        content.addView(totals(snapshot, groups))
        for (account in snapshot.accounts) content.addView(card(snapshot, account))
    }

    /** Today's realised and open figures and the funds, summed within real money and within paper. */
    private fun totals(snapshot: MonitorState.Snapshot, groups: Map<Boolean, List<Account>>): View = ui.card(padding = 16, gap = 10).apply {
        addView(ui.label(ui.string(R.string.overview_today)))
        for ((paper, accounts) in groups) {
            val books = accounts.mapNotNull { snapshot.stateOf(it.id).status.book }
            val realized = books.sumOf { it.realizedToday }
            val unrealized = books.mapNotNull { it.unrealized }.takeIf { it.isNotEmpty() }?.sum()
            addView(
                ui.row(gap = 12).apply {
                    gravity = Gravity.BOTTOM
                    addView(
                        ui.grow(
                            ui.column(gap = 2).apply {
                                addView(ui.text(ui.string(if (paper) R.string.overview_paper else R.string.overview_real), size = 12f, color = R.color.muted))
                                addView(ui.text(if (books.isEmpty()) "—" else Format.signedMoney(realized), size = 24f, color = gainColor(realized), mono = true))
                                addView(
                                    ui.text(
                                        ui.string(R.string.overview_counts, books.sumOf { it.buysToday }, books.sumOf { it.salesToday }),
                                        size = 12f,
                                        color = R.color.muted,
                                    ),
                                )
                                Funds.total(books.mapNotNull { it.funds })?.let { funds ->
                                    val value = funds.value
                                    val share = funds.availableShare
                                    addView(
                                        ui.text(
                                            if (value != null && share != null) {
                                                ui.string(R.string.overview_funds, Format.wholeMoney(value), Format.wholeMoney(funds.available), Format.share(share), Format.wholeMoney(funds.unsettled))
                                            } else {
                                                ui.string(R.string.overview_funds_unknown, Format.wholeMoney(funds.available), Format.wholeMoney(funds.unsettled))
                                            },
                                            size = 12f,
                                            color = R.color.ink_soft,
                                        ),
                                    )
                                }
                            },
                        ),
                    )
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
        }
        if (snapshot.accounts.any { snapshot.stateOf(it.id).link !is BridgeClient.Link.Connected }) {
            addView(ui.text(ui.string(R.string.overview_partial), size = 12f, color = R.color.muted))
        }
    }

    private fun card(snapshot: MonitorState.Snapshot, account: Account): View {
        val look = BrokerLook.of(account.broker)
        val state = snapshot.stateOf(account.id)
        val verdict = Verdict.of(ui, prefs, account, state)
        val (fresh, freshColor) = Verdict.freshness(ui, state, prefs.heardAt(account.id))
        val book = state.status.book
        val now = System.currentTimeMillis()
        return ui.card(padding = 14, gap = 8).apply {
            background = ui.rounded(R.color.card, radius = 14, stroke = look.strong)
            addView(
                ui.row(gap = 10).apply {
                    addView(ui.badge(account.broker.label, look))
                    addView(ui.grow(ui.text(account.name, bold = true)))
                    if (account.mutedAt(now)) {
                        addView(
                            ui.text(ui.string(R.string.account_muted_short), size = 12f, color = R.color.muted),
                            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                        )
                    }
                },
            )
            addView(
                ui.row(gap = 10).apply {
                    gravity = Gravity.TOP
                    addView(
                        View(ui.context).apply { background = ui.rounded(verdict.fill, radius = 5) },
                        LinearLayout.LayoutParams(ui.dp(10), ui.dp(10)).apply { topMargin = ui.dp(5) },
                    )
                    addView(
                        ui.grow(
                            ui.column(gap = 2).apply {
                                addView(ui.text(listOf(verdict.tag, verdict.title).distinct().joinToString(" · "), bold = true, size = 13f))
                                if (verdict.detail.isNotEmpty()) addView(ui.text(verdict.detail, size = 12f, color = R.color.ink_soft))
                                addView(ui.text(fresh, size = 12f, color = freshColor))
                            },
                        ),
                    )
                },
            )
            addView(
                ui.row(gap = 8).apply {
                    addView(figure(ui.string(R.string.profit_today), book?.realizedToday?.let(Format::signedMoney), book?.realizedToday))
                    addView(figure(ui.string(R.string.unrealized_short), book?.unrealized?.let(Format::signedMoney), book?.unrealized))
                    addView(figure(ui.string(R.string.overview_trades), book?.let { ui.string(R.string.overview_trades_value, it.buysToday, it.salesToday) }, null))
                },
            )
            val funds = book?.funds
            if (funds != null) {
                addView(
                    ui.row(gap = 8).apply {
                        addView(figure(ui.string(R.string.funds_value_short), funds.value?.let(Format::wholeMoney), null))
                        addView(figure(ui.string(R.string.funds_available_short), Format.wholeMoney(funds.available), null))
                        addView(figure(ui.string(R.string.funds_unsettled), Format.wholeMoney(funds.unsettled), null))
                        addView(figure(ui.string(R.string.funds_share_short), funds.availableShare?.let(Format::share), null))
                    },
                )
            }
            contentDescription = ui.string(R.string.overview_open, account.name)
            ui.tappable(this) { open(account) }
        }
    }

    private fun figure(label: String, value: String?, sign: Double?): View = ui.column(gap = 0).apply {
        addView(ui.text(label, size = 11f, color = R.color.muted))
        addView(ui.text(value ?: "—", size = 15f, color = sign?.let(::gainColor) ?: R.color.ink, mono = true))
        layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
    }

    private fun gainColor(value: Double): Int = when {
        value > 0 -> R.color.status_ok
        value < 0 -> R.color.status_bad
        else -> R.color.ink
    }
}
