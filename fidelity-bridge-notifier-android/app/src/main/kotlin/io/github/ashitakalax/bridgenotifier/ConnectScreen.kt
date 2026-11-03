package io.github.ashitakalax.bridgenotifier

import android.text.InputType
import android.view.View
import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.TextView
import io.github.ashitakalax.bridgenotifier.core.ApiKeys
import io.github.ashitakalax.bridgenotifier.core.BridgeAddress
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.EventKind

/**
 * The settings and connection page, shown at start-up: the bridge's address
 * and key, a three-step check that they work, and what to be told about.
 */
class ConnectScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val onConnected: () -> Unit,
) : Screen {
    private val address = input(ui.string(R.string.address_hint), InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI)
    private val key = input(ui.string(R.string.key_hint), HIDDEN_KEY)
    private val checks = ui.column(gap = 12)
    private val plainText = ui.text(ui.string(R.string.plaintext_warning), size = 13f, color = R.color.status_warn)
    private val notificationsOff = ui.text(ui.string(R.string.notifications_off), size = 13f, color = R.color.status_bad)
    private var keyShown = false

    override val view: View

    init {
        val (scroll, page) = ui.page()
        page.addView(ui.eyebrow(ui.string(R.string.app_name)))
        page.addView(ui.text(ui.string(R.string.connect_title), size = 26f, bold = true))
        page.addView(ui.text(ui.string(R.string.connect_intro), color = R.color.muted))

        address.setText(prefs.url)
        key.setText(prefs.apiKey)
        val showKey = ImageButton(ui.context).apply {
            setImageResource(R.drawable.ic_eye)
            imageTintList = android.content.res.ColorStateList.valueOf(ui.color(R.color.ink_soft))
            background = ui.rounded(R.color.card, radius = 10, stroke = R.color.line_strong)
            contentDescription = ui.string(R.string.show_key)
            setOnClickListener { toggleKey(this) }
        }
        val keyRow = ui.row(gap = 8).apply {
            addView(ui.grow(key))
            addView(showKey, LinearLayout.LayoutParams(ui.dp(48), ui.dp(48)))
        }
        page.addView(
            ui.card(gap = 6).apply {
                addView(ui.label(ui.string(R.string.address_label)))
                addView(address)
                addView(ui.text(ui.string(R.string.address_help), size = 12f, color = R.color.muted))
                addView(plainText)
                addView(spacer(8))
                addView(ui.label(ui.string(R.string.key_label)))
                addView(keyRow)
                addView(ui.text(ui.string(R.string.key_help), size = 12f, color = R.color.muted))
            },
        )

        page.addView(
            ui.card(gap = 12).apply {
                addView(ui.label(ui.string(R.string.check_header)))
                addView(checks)
            },
        )

        val kinds = ui.column(gap = 0)
        for (kind in EventKind.ALL) {
            kinds.addView(
                checkbox(EventKind.label(kind), kind !in prefs.disabledKinds) { on ->
                    prefs.disabledKinds = if (on) prefs.disabledKinds - kind else prefs.disabledKinds + kind
                },
            )
        }
        page.addView(
            ui.card(gap = 4).apply {
                addView(ui.label(ui.string(R.string.header_notify_me)))
                addView(notificationsOff)
                addView(kinds)
                addView(checkbox(ui.string(R.string.alert_unreachable), prefs.alertWhenUnreachable) { prefs.alertWhenUnreachable = it })
            },
        )
        page.addView(
            ui.card(gap = 2).apply {
                addView(checkbox(ui.string(R.string.open_at_start), prefs.openConnectAtStart) { prefs.openConnectAtStart = it })
                addView(ui.text(ui.string(R.string.open_at_start_help), size = 12f, color = R.color.muted))
            },
        )
        page.addView(
            TextView(ui.context).apply {
                text = ui.string(R.string.stop_watching)
                setTextColor(ui.color(R.color.muted))
                minHeight = ui.dp(48)
                gravity = android.view.Gravity.CENTER
                setOnClickListener {
                    prefs.monitoring = false
                    MonitorService.stop(ui.context)
                }
            },
        )

        val footer = ui.row(gap = 10).apply {
            setPadding(ui.dp(16), ui.dp(12), ui.dp(16), ui.dp(16))
            setBackgroundColor(ui.color(R.color.ground))
            addView(ui.grow(ui.button(ui.string(R.string.send_test), filled = false) { MonitorService.requestTest(ui.context) }))
            addView(
                ui.button(ui.string(R.string.save_and_watch), filled = true) { saveAndWatch() },
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.4f),
            )
        }
        view = LinearLayout(ui.context).apply {
            orientation = LinearLayout.VERTICAL
            addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
            addView(View(ui.context).apply { setBackgroundColor(ui.color(R.color.line)) }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ui.dp(1)))
            addView(footer)
        }
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        plainText.visibility = if (BridgeAddress.isPlainText(prefs.url)) View.VISIBLE else View.GONE
        notificationsOff.visibility = if (Alerts.notificationsEnabled(ui.context)) View.GONE else View.VISIBLE
        val host = MonitorService.hostOf(prefs.url)
        val link = snapshot.link
        val reached = link is BridgeClient.Link.Connected || link is BridgeClient.Link.Refused
        val test = snapshot.recent.firstOrNull { it.isTest }
        checks.removeAllViews()
        checks.addView(
            step(
                ui.string(R.string.check_reachable),
                when {
                    reached -> ui.string(R.string.check_reachable_yes, host)
                    link is BridgeClient.Link.Waiting -> ui.string(R.string.check_reachable_waiting, link.reason)
                    else -> ui.string(R.string.check_reachable_no)
                },
                if (reached) Mark.OK else if (link is BridgeClient.Link.Waiting) Mark.FAIL else Mark.PENDING,
                "1",
            ),
        )
        checks.addView(
            step(
                ui.string(R.string.check_key),
                when (link) {
                    is BridgeClient.Link.Connected -> ui.string(R.string.check_key_yes)
                    is BridgeClient.Link.Refused -> ui.string(R.string.check_key_refused, link.reason)
                    else -> ui.string(R.string.check_key_wait)
                },
                when (link) {
                    is BridgeClient.Link.Connected -> Mark.OK
                    is BridgeClient.Link.Refused -> Mark.FAIL
                    else -> Mark.PENDING
                },
                "2",
            ),
        )
        checks.addView(
            step(
                ui.string(R.string.check_test),
                test?.let { ui.string(R.string.check_test_yes, Format.clockTime(it.at) ?: "") } ?: ui.string(R.string.check_test_wait),
                if (test != null) Mark.OK else Mark.PENDING,
                "3",
            ),
        )
    }

    private enum class Mark { OK, FAIL, PENDING }

    private fun step(label: String, detail: String, mark: Mark, number: String): View = ui.row(gap = 10).apply {
        addView(
            when (mark) {
                Mark.OK -> ui.mark("✓", R.color.status_ok)
                Mark.FAIL -> ui.mark("!", R.color.status_bad)
                Mark.PENDING -> ui.mark(number, R.color.status_idle)
            },
        )
        addView(
            ui.grow(
                ui.column().apply {
                    addView(ui.text(label, bold = true))
                    addView(ui.text(detail, size = 12f, color = R.color.muted))
                },
            ),
        )
    }

    private fun saveAndWatch() {
        val url = BridgeAddress.parse(address.text.toString())
        if (url == null) {
            address.error = ui.string(R.string.error_address)
            return
        }
        val typed = key.text.toString().trim()
        if (!ApiKeys.looksValid(typed)) {
            key.error = ui.string(R.string.error_key)
            return
        }
        if (url != prefs.url) prefs.forgetPosition()
        prefs.url = url
        prefs.apiKey = typed
        prefs.monitoring = true
        address.setText(url)
        MonitorService.restart(ui.context)
        onConnected()
    }

    private fun toggleKey(button: ImageButton) {
        keyShown = !keyShown
        key.inputType = if (keyShown) SHOWN_KEY else HIDDEN_KEY
        key.setSelection(key.text.length)
        button.contentDescription = ui.string(if (keyShown) R.string.hide_key else R.string.show_key)
    }

    private fun input(hint: String, type: Int): EditText = EditText(ui.context).apply {
        this.hint = hint
        inputType = type
        isSingleLine = true
        typeface = android.graphics.Typeface.MONOSPACE
        textSize = 14f
        minHeight = ui.dp(48)
        setPadding(ui.dp(12), 0, ui.dp(12), 0)
        background = ui.rounded(R.color.card, radius = 10, stroke = R.color.line_strong)
    }

    private fun checkbox(label: String, checked: Boolean, onChange: (Boolean) -> Unit): CheckBox =
        CheckBox(ui.context).apply {
            text = label
            textSize = 14f
            setTextColor(ui.color(R.color.ink))
            minHeight = ui.dp(44)
            isChecked = checked
            setOnCheckedChangeListener { _, on -> onChange(on) }
        }

    private fun spacer(height: Int): View = View(ui.context).apply {
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ui.dp(height))
    }

    private companion object {
        const val HIDDEN_KEY = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
        const val SHOWN_KEY = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
    }
}
