package io.github.ashitakalax.bridgenotifier

import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.ClipboardManager
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.Toast
import io.github.ashitakalax.bridgenotifier.core.ApiKeys
import io.github.ashitakalax.bridgenotifier.core.BridgeAddress
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.EventKind

/**
 * The settings and connection page: the bridge's address and key, a
 * three-step check that they work, whether Android will let the alerts
 * through, the switch that starts and stops watching, and what to be told
 * about.
 */
class ConnectScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val askToNotify: () -> Unit,
    private val onConnected: () -> Unit,
) : Screen {
    private val address = input(ui.string(R.string.address_hint), InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI)
    private val key = input(ui.string(R.string.key_hint), HIDDEN_KEY)
    private val checks = ui.column(gap = 12)
    private val plainText = ui.text(ui.string(R.string.plaintext_warning), size = 13f, color = R.color.status_warn)
    private val notificationsOff = notice(R.string.notifications_off, R.color.status_bad, R.string.notifications_turn_on, ::openNotificationSettings)
    private val batteryRestricted = notice(R.string.battery_restricted, R.color.status_warn, R.string.battery_allow, ::askForBattery)
    private val watching = Switch(ui.context).apply {
        text = ui.string(R.string.watching)
        textSize = 15f
        typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        setTextColor(ui.color(R.color.ink))
        minHeight = ui.dp(48)
    }
    private val watchingHelp = ui.text("", size = 12f, color = R.color.muted)
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
            imageTintList = ColorStateList.valueOf(ui.color(R.color.ink_soft))
            background = ui.pressable(ui.rounded(R.color.card, radius = 10, stroke = R.color.line_strong))
            contentDescription = ui.string(R.string.show_key)
            setOnClickListener { toggleKey(this) }
        }
        val paste = ui.text(ui.string(R.string.paste_key), size = 13f, color = R.color.accent, bold = true).apply {
            gravity = Gravity.CENTER
            minHeight = ui.dp(48)
            setPadding(ui.dp(12), 0, ui.dp(12), 0)
            background = ui.rounded(R.color.card, radius = 10, stroke = R.color.line_strong)
            ui.tappable(this, ::pasteKey)
        }
        val keyRow = ui.row(gap = 8).apply {
            addView(ui.grow(key))
            addView(paste, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ui.dp(48)))
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

        page.addView(
            ui.card(gap = 4).apply {
                addView(watching)
                addView(watchingHelp)
            },
        )

        page.addView(
            ui.card(gap = 4).apply {
                addView(ui.label(ui.string(R.string.header_notify_me)))
                addView(notificationsOff)
                addView(batteryRestricted)
                for ((header, kinds) in groups()) {
                    addView(spacer(6))
                    addView(ui.eyebrow(ui.string(header)))
                    for (kind in kinds) {
                        addView(
                            checkbox(EventKind.label(kind), kind !in prefs.disabledKinds) { on ->
                                prefs.disabledKinds = if (on) prefs.disabledKinds - kind else prefs.disabledKinds + kind
                            },
                        )
                    }
                }
                addView(spacer(6))
                addView(ui.eyebrow(ui.string(R.string.group_app)))
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
            ui.text(ui.string(R.string.version, BuildConfig.VERSION_NAME), size = 12f, color = R.color.muted).apply {
                gravity = Gravity.CENTER
            },
        )

        val footer = ui.row(gap = 10).apply {
            setPadding(ui.dp(16), ui.dp(12), ui.dp(16), ui.dp(16))
            setBackgroundColor(ui.color(R.color.ground))
            addView(ui.grow(ui.button(ui.string(R.string.send_test), filled = false, ::sendTest)))
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

    /** What was typed and not yet saved survives the activity being rebuilt. */
    override fun save(state: Bundle) {
        state.putString(ADDRESS, address.text.toString())
        state.putString(KEY, key.text.toString())
    }

    override fun restore(state: Bundle) {
        state.getString(ADDRESS)?.let { address.setText(it) }
        state.getString(KEY)?.let { key.setText(it) }
    }

    override fun render(snapshot: MonitorState.Snapshot) {
        plainText.visibility = if (BridgeAddress.isPlainText(prefs.url)) View.VISIBLE else View.GONE
        notificationsOff.visibility = if (Alerts.notificationsEnabled(ui.context)) View.GONE else View.VISIBLE
        batteryRestricted.visibility = if (batteryUnrestricted()) View.GONE else View.VISIBLE

        // The switch shows what is so; set without its listener hearing it.
        watching.setOnCheckedChangeListener(null)
        watching.isEnabled = prefs.isConfigured
        watching.isChecked = prefs.monitoring && prefs.isConfigured
        watching.setOnCheckedChangeListener { _, on -> watch(on) }
        watchingHelp.text = ui.string(
            when {
                !prefs.isConfigured -> R.string.watching_unset
                prefs.monitoring -> R.string.watching_on
                else -> R.string.watching_off
            },
        )

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
                Mark.OK -> ui.mark("✓", R.color.status_ok_fill, ui.string(R.string.mark_ok))
                Mark.FAIL -> ui.mark("!", R.color.status_bad_fill, ui.string(R.string.mark_fail))
                Mark.PENDING -> ui.mark(number, R.color.status_idle_fill, ui.string(R.string.mark_step, number))
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

    /** The notification kinds under the headings the Activity page filters by; a kind not placed goes last. */
    private fun groups(): List<Pair<Int, List<String>>> {
        val trades = listOf(EventKind.BUY, EventKind.SELL, EventKind.ORDER_UPDATE, EventKind.WINDOW)
        val problems = listOf(
            EventKind.ORDER_PROBLEM, EventKind.READINESS, EventKind.FIDELITY_SIGNIN, EventKind.ACCOUNT_CHECK, EventKind.SESSION,
        )
        val connection = EventKind.ALL - trades.toSet() - problems.toSet()
        return listOf(
            R.string.filter_trades to trades,
            R.string.filter_problems to problems,
            R.string.filter_connection to connection,
        )
    }

    private fun saveAndWatch() {
        val url = BridgeAddress.parse(address.text.toString())
        if (url == null) {
            address.error = ui.string(R.string.error_address)
            address.requestFocus()
            return
        }
        val typed = ApiKeys.clean(key.text.toString())
        if (!ApiKeys.looksValid(typed)) {
            key.error = ui.string(R.string.error_key)
            key.requestFocus()
            return
        }
        if (url != prefs.url) {
            // A different bridge: where the old one left off, and what it said, are not this one's.
            prefs.forgetPosition()
            NotifierApplication.history(ui.context).clear()
            MonitorState.update { it.copy(recent = emptyList()) }
        }
        prefs.url = url
        prefs.apiKey = typed
        prefs.monitoring = true
        address.setText(url)
        key.setText(typed)
        MonitorService.restart(ui.context)
        askToNotify()
        onConnected()
    }

    private fun watch(on: Boolean) {
        prefs.monitoring = on
        if (on) MonitorService.start(ui.context) else MonitorService.stop(ui.context)
        render(MonitorState.snapshot)
    }

    private fun sendTest() {
        val connected = MonitorState.snapshot.link is BridgeClient.Link.Connected
        if (connected) MonitorService.requestTest(ui.context)
        toast(if (connected) R.string.test_asked else R.string.test_not_connected)
    }

    private fun pasteKey() {
        val clipboard = ui.context.getSystemService(ClipboardManager::class.java)
        val pasted = clipboard?.primaryClip?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(ui.context)?.toString()
        val cleaned = pasted?.let(ApiKeys::clean).orEmpty()
        if (cleaned.isEmpty()) {
            toast(R.string.paste_empty)
            return
        }
        key.setText(cleaned)
        key.setSelection(key.text.length)
        key.error = if (ApiKeys.looksValid(cleaned)) null else ui.string(R.string.error_key)
    }

    private fun toggleKey(button: ImageButton) {
        keyShown = !keyShown
        key.inputType = if (keyShown) SHOWN_KEY else HIDDEN_KEY
        key.typeface = Typeface.MONOSPACE
        key.setSelection(key.text.length)
        button.contentDescription = ui.string(if (keyShown) R.string.hide_key else R.string.show_key)
    }

    private fun batteryUnrestricted(): Boolean =
        ui.context.getSystemService(PowerManager::class.java)?.isIgnoringBatteryOptimizations(ui.context.packageName) != false

    /** Android's own dialog to exempt this app; its list of apps where that dialog is not offered. */
    @SuppressLint("BatteryLife") // Sideloaded, and holding one connection open is the app's whole job.
    private fun askForBattery() {
        try {
            ui.context.startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:${ui.context.packageName}")),
            )
        } catch (_: ActivityNotFoundException) {
            open(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        }
    }

    private fun openNotificationSettings() {
        open(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, ui.context.packageName))
    }

    private fun open(intent: Intent) {
        try {
            ui.context.startActivity(intent)
        } catch (_: ActivityNotFoundException) {
            toast(R.string.settings_unavailable)
        }
    }

    private fun toast(message: Int) {
        Toast.makeText(ui.context, message, Toast.LENGTH_LONG).show()
    }

    /** A warning with the one button that deals with it. */
    private fun notice(message: Int, color: Int, action: Int, onClick: () -> Unit): View = ui.column(gap = 6).apply {
        setPadding(0, ui.dp(4), 0, ui.dp(8))
        addView(ui.text(ui.string(message), size = 13f, color = color))
        addView(ui.button(ui.string(action), filled = false, onClick))
    }

    private fun input(hint: String, type: Int): EditText = EditText(ui.context).apply {
        this.hint = hint
        inputType = type
        isSingleLine = true
        typeface = Typeface.MONOSPACE
        textSize = 14f
        // Said outright: the theme's own would be the dark theme's white on this card.
        setTextColor(ui.color(R.color.ink))
        setHintTextColor(ui.color(R.color.muted))
        minHeight = ui.dp(48)
        setPadding(ui.dp(12), 0, ui.dp(12), 0)
        background = ui.rounded(R.color.card, radius = 10, stroke = R.color.line_strong)
    }

    private fun checkbox(label: String, checked: Boolean, onChange: (Boolean) -> Unit): CheckBox =
        CheckBox(ui.context).apply {
            text = label
            textSize = 14f
            setTextColor(ui.color(R.color.ink))
            buttonTintList = ColorStateList(
                arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
                intArrayOf(ui.color(R.color.accent), ui.color(R.color.muted)),
            )
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
        const val ADDRESS = "connect_address"
        const val KEY = "connect_key"
    }
}
