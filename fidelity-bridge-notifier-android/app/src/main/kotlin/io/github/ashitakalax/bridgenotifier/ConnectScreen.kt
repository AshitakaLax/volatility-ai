package io.github.ashitakalax.bridgenotifier

import android.annotation.SuppressLint
import android.app.AlertDialog
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
import android.widget.TextView
import android.widget.Toast
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.Accounts
import io.github.ashitakalax.bridgenotifier.core.ApiKeys
import io.github.ashitakalax.bridgenotifier.core.BridgeAddress
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.ProfitHistory
import java.time.Instant

/**
 * The settings and connection page, shown at start-up: the accounts the app
 * watches -- each a listener's address and key, a Fidelity bridge or the
 * trader notifier's Alpaca deployments -- the one being edited, a three-step
 * check that it works, the switch that starts and stops watching, whether
 * Android will let the alerts through, and what that account is to notify
 * the phone about (its trades one by one or in one note after the close,
 * muted, or muted for an hour from a notification). Then the app's own
 * settings, and its version against the latest release.
 */
class ConnectScreen(
    private val ui: Ui,
    private val prefs: Prefs,
    private val askToNotify: () -> Unit,
    private val onConnected: () -> Unit,
) : Screen {
    private val accountList = ui.column(gap = 8)
    private val formHeader = ui.row(gap = 8)
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
    private val lockUnavailable = ui.text(ui.string(R.string.lock_unavailable), size = 12f, color = R.color.status_warn)
    private val remove = TextView(ui.context).apply {
        text = ui.string(R.string.account_remove)
        setTextColor(ui.color(R.color.status_bad))
        minHeight = ui.dp(44)
        gravity = Gravity.CENTER_VERTICAL
        setOnClickListener { confirmRemove() }
    }
    private var keyShown = false

    // What the account being edited notifies about: rebuilt when it changes.
    private val notifyHeader = ui.row(gap = 8)
    private val mutes = ui.column(gap = 0)
    private val kindBoxes = mutableMapOf<String, CheckBox>()
    private var mutesFor: String? = null
    private val mutedFor = ui.text(size = 12f, color = R.color.accent, bold = true).apply {
        minHeight = ui.dp(36)
        gravity = Gravity.CENTER_VERTICAL
    }

    // The app's version, and the latest release's.
    private val updateLine = ui.text(size = 12f, color = R.color.muted)
    private val updateGet = ui.button("", filled = true) {
        prefs.latestRelease?.page?.let { page ->
            try {
                ui.context.startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(page)))
            } catch (_: android.content.ActivityNotFoundException) {
                updateLine.text = page
            }
        }
    }

    /** Adding a new account rather than editing the one shown. */
    private var adding = false

    /** The account whose address and key the fields hold, so a redraw keeps what is typed. */
    private var filledFor: String? = null
    private var last: MonitorState.Snapshot? = null

    override val view: View

    init {
        val (scroll, page) = ui.page()
        page.addView(ui.eyebrow(ui.string(R.string.app_name)))
        page.addView(ui.text(ui.string(R.string.connect_title), size = 26f, bold = true))
        page.addView(ui.text(ui.string(R.string.connect_intro), color = R.color.muted))

        page.addView(
            ui.card(gap = 8).apply {
                addView(ui.label(ui.string(R.string.accounts_header)))
                addView(accountList)
                addView(
                    ui.button(ui.string(R.string.account_add), filled = false) {
                        adding = true
                        filledFor = null
                        address.setText("")
                        key.setText("")
                        last?.let(::render)
                    },
                )
            },
        )

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
                addView(formHeader)
                addView(spacer(4))
                addView(ui.label(ui.string(R.string.address_label)))
                addView(address)
                addView(ui.text(ui.string(R.string.address_help), size = 12f, color = R.color.muted))
                addView(plainText)
                addView(spacer(8))
                addView(ui.label(ui.string(R.string.key_label)))
                addView(keyRow)
                addView(ui.text(ui.string(R.string.key_help), size = 12f, color = R.color.muted))
                addView(remove)
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
                addView(notifyHeader)
                addView(notificationsOff)
                addView(batteryRestricted)
                addView(mutes)
            },
        )
        page.addView(
            ui.card(gap = 2).apply {
                addView(checkbox(ui.string(R.string.alert_unreachable), prefs.alertWhenUnreachable) { prefs.alertWhenUnreachable = it })
                addView(ui.text(ui.string(R.string.alert_unreachable_help), size = 12f, color = R.color.muted))
            },
        )
        page.addView(
            ui.card(gap = 2).apply {
                addView(checkbox(ui.string(R.string.lock_setting), prefs.lockApp) { prefs.lockApp = it })
                addView(ui.text(ui.string(R.string.lock_setting_help), size = 12f, color = R.color.muted))
                addView(lockUnavailable)
            },
        )
        page.addView(
            ui.card(gap = 2).apply {
                addView(checkbox(ui.string(R.string.open_at_start), prefs.openConnectAtStart) { prefs.openConnectAtStart = it })
                addView(ui.text(ui.string(R.string.open_at_start_help), size = 12f, color = R.color.muted))
            },
        )
        page.addView(
            ui.card(gap = 6).apply {
                addView(checkbox(ui.string(R.string.update_setting), prefs.checkUpdates) { prefs.checkUpdates = it })
                addView(ui.text(ui.string(R.string.update_setting_help), size = 12f, color = R.color.muted))
                addView(updateLine)
                addView(
                    ui.row(gap = 8).apply {
                        addView(
                            ui.grow(
                                ui.button(ui.string(R.string.update_check_now), filled = false) {
                                    UpdateChecker.maybeCheck(ui.context, force = true)
                                    last?.let(::render)
                                },
                            ),
                        )
                        addView(updateGet, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                    },
                )
            },
        )

        val footer = ui.row(gap = 10).apply {
            setPadding(ui.dp(16), ui.dp(12), ui.dp(16), ui.dp(16))
            addView(
                ui.grow(
                    ui.button(ui.string(R.string.send_test), filled = false, ::sendTest),
                ),
            )
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

    /** The account the form edits: none while adding one, or before there is any. */
    private fun editing(snapshot: MonitorState.Snapshot): Account? = if (adding) null else snapshot.account

    override fun render(snapshot: MonitorState.Snapshot) {
        last = snapshot
        val account = editing(snapshot)
        if (account != null && account.id != filledFor) {
            filledFor = account.id
            address.setText(account.url)
            key.setText(account.apiKey)
        }
        renderAccounts(snapshot, account)
        renderHeader(account)
        remove.visibility = if (account != null) View.VISIBLE else View.GONE
        plainText.visibility = if (BridgeAddress.isPlainText(account?.url ?: address.text.toString())) View.VISIBLE else View.GONE
        notificationsOff.visibility = if (Alerts.notificationsEnabled(ui.context)) View.GONE else View.VISIBLE
        batteryRestricted.visibility = if (batteryUnrestricted()) View.GONE else View.VISIBLE
        renderWatching()
        lockUnavailable.visibility = if (LockGate.available(ui.context)) View.GONE else View.VISIBLE
        renderChecks(snapshot, account)
        renderMutes(account)
        renderUpdates()
    }

    /** The switch shows what is so; set without its listener hearing it. */
    private fun renderWatching() {
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
    }

    /** What was typed and not yet saved survives the activity being rebuilt. */
    override fun save(state: Bundle) {
        state.putString(ADDRESS, address.text.toString())
        state.putString(KEY, key.text.toString())
        state.putBoolean(ADDING, adding)
    }

    override fun restore(state: Bundle) {
        adding = state.getBoolean(ADDING, false)
        state.getString(ADDRESS)?.let { address.setText(it) }
        state.getString(KEY)?.let { key.setText(it) }
        // What was typed is for the account being edited: the next render keeps it.
        filledFor = if (adding) null else prefs.currentId
    }

    /** This app's version, what GitHub last said is the latest, and when. */
    private fun renderUpdates() {
        val release = prefs.latestRelease
        val checked = prefs.updateCheckedAt.takeIf { it > 0 }
        val error = prefs.updateError
        updateLine.text = listOfNotNull(
            ui.string(R.string.update_installed, BuildConfig.VERSION_NAME + if (BuildConfig.DEBUG) " (debug)" else ""),
            when {
                UpdateChecker.asking -> ui.string(R.string.update_checking)
                error != null -> ui.string(R.string.update_failed, error)
                release != null && checked != null -> ui.string(
                    R.string.update_latest,
                    release.version ?: ui.string(R.string.update_no_version),
                    release.tag,
                    Format.relative(checked),
                )
                else -> ui.string(R.string.update_never)
            },
        ).joinToString(" ")
        val available = UpdateChecker.available(prefs)
        updateGet.visibility = if (available != null) View.VISIBLE else View.INVISIBLE
        if (available != null) updateGet.text = ui.string(R.string.update_get_version, available.version ?: available.tag)
    }

    /**
     * The account's own switches. Read from what is saved, not the snapshot,
     * and saved at once: the service reads them for each notification.
     */
    private fun renderMutes(account: Account?) {
        val key = account?.let { "${it.id}\u0000${it.name}" }
        if (key != mutesFor) {
            mutesFor = key
            notifyHeader.removeAllViews()
            mutes.removeAllViews()
            kindBoxes.clear()
            notifyHeader.addView(ui.grow(ui.label(ui.string(R.string.header_notify_me))))
            val saved = account?.let { prefs.account(it.id) }
            if (account == null || saved == null) {
                mutes.addView(ui.text(ui.string(R.string.notify_save_first), size = 13f, color = R.color.muted))
            } else {
                notifyHeader.addView(ui.badge(account.name, BrokerLook.of(account.broker)))
                mutes.addView(
                    checkbox(ui.string(R.string.account_mute, account.name), saved.muted) { on ->
                        prefs.change(account.id) { it.copy(muted = on) }
                        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
                    },
                )
                mutes.addView(ui.text(ui.string(R.string.account_mute_help), size = 12f, color = R.color.muted))
                (mutedFor.parent as? ViewGroup)?.removeView(mutedFor)
                mutedFor.setOnClickListener {
                    prefs.change(account.id) { it.copy(mutedUntil = null) }
                    MonitorState.setAccounts(prefs.accounts, prefs.currentId)
                }
                mutes.addView(mutedFor)
                mutes.addView(
                    checkbox(ui.string(R.string.account_summary), saved.summary) { on ->
                        prefs.change(account.id) { it.copy(summary = on) }
                        // From today on: a note for the days before would be old news.
                        if (on) prefs.setSummaryDone(account.id, ProfitHistory.marketDay(Instant.now()).minusDays(1))
                        last?.let(::render)
                    },
                )
                mutes.addView(ui.text(ui.string(R.string.account_summary_help), size = 12f, color = R.color.muted))
                for ((header, kinds) in groups()) {
                    mutes.addView(spacer(6))
                    mutes.addView(ui.eyebrow(ui.string(header)))
                    for (kind in kinds) {
                        val box = checkbox(EventKind.label(kind), kind !in saved.mutedKinds) { on ->
                            prefs.change(account.id) {
                                it.copy(mutedKinds = if (on) it.mutedKinds - kind else it.mutedKinds + kind)
                            }
                        }
                        kindBoxes[kind] = box
                        mutes.addView(box)
                    }
                }
            }
        }
        val saved = account?.let { prefs.account(it.id) }
        val now = System.currentTimeMillis()
        val until = saved?.mutedUntil?.takeIf { saved.mutedFor(now) && !saved.muted }
        mutedFor.visibility = if (until != null) View.VISIBLE else View.GONE
        if (until != null) mutedFor.text = ui.string(R.string.account_muted_until, Format.clockAt(until))
        // Muted, none of them buzz; summing up the day, the trades fold into its note.
        kindBoxes.forEach { (kind, box) ->
            box.isEnabled = saved?.muted != true && !(saved?.summary == true && kind in EventKind.TRADES)
        }
    }

    private fun renderAccounts(snapshot: MonitorState.Snapshot, editing: Account?) {
        accountList.removeAllViews()
        if (snapshot.accounts.isEmpty()) {
            accountList.addView(ui.text(ui.string(R.string.accounts_none), size = 13f, color = R.color.muted))
        }
        for (account in snapshot.accounts) {
            val look = BrokerLook.of(account.broker)
            val on = account.id == editing?.id
            accountList.addView(
                ui.row(gap = 10).apply {
                    minimumHeight = ui.dp(56)
                    setPadding(ui.dp(12), ui.dp(8), ui.dp(12), ui.dp(8))
                    background = ui.rounded(if (on) look.ground else R.color.card, radius = 12, stroke = if (on) look.strong else R.color.line)
                    addView(ui.badge(account.broker.label, look))
                    addView(
                        ui.grow(
                            ui.column().apply {
                                addView(ui.text(account.name, bold = true))
                                addView(
                                    ui.text(
                                        listOfNotNull(
                                            MonitorService.hostOf(account.url),
                                            linkWords(snapshot.stateOf(account.id).link),
                                            ui.string(R.string.account_muted_short).takeIf { account.mutedAt(System.currentTimeMillis()) },
                                        ).joinToString(" · "),
                                        size = 12f,
                                        color = R.color.muted,
                                    ),
                                )
                            },
                        ),
                    )
                    isSelected = on
                    contentDescription = ui.string(R.string.account_edit, account.name)
                    ui.tappable(this) {
                        adding = false
                        prefs.currentId = account.id
                        MonitorState.setAccounts(prefs.accounts, account.id)
                    }
                },
            )
        }
    }

    private fun renderHeader(account: Account?) {
        formHeader.removeAllViews()
        if (account == null) {
            formHeader.addView(ui.label(ui.string(R.string.account_new_header)))
            return
        }
        formHeader.addView(ui.badge(account.brokerLine, BrokerLook.of(account.broker)))
        formHeader.addView(ui.grow(ui.label(account.name)))
    }

    private fun linkWords(link: BridgeClient.Link): String = when (link) {
        is BridgeClient.Link.Connected -> ui.string(R.string.link_connected)
        is BridgeClient.Link.Waiting -> ui.string(R.string.link_waiting, link.reason)
        is BridgeClient.Link.Refused -> ui.string(R.string.link_refused)
        BridgeClient.Link.Connecting -> ui.string(R.string.link_connecting)
        BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> ui.string(R.string.link_idle)
    }

    private fun renderChecks(snapshot: MonitorState.Snapshot, account: Account?) {
        val host = MonitorService.hostOf(account?.url ?: "")
        val link = if (account != null) snapshot.link else BridgeClient.Link.Idle
        val reached = link is BridgeClient.Link.Connected || link is BridgeClient.Link.Refused
        val test = if (account != null) snapshot.recent.firstOrNull { it.isTest } else null
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

    private fun saveAndWatch() {
        val url = BridgeAddress.parse(address.text.toString())
        if (url == null) {
            address.error = ui.string(R.string.error_address)
            address.requestFocus()
            return
        }
        // The whole .env line pasted in is the key too.
        val typed = ApiKeys.clean(key.text.toString())
        if (!ApiKeys.looksValid(typed)) {
            key.error = ui.string(R.string.error_key)
            key.requestFocus()
            return
        }
        val existing = if (adding) null else prefs.account(prefs.currentId)
        val account = when {
            existing == null -> Account(Accounts.newId(prefs.accounts), url, typed, broker = Accounts.guessBroker(url))
            existing.url != url -> {
                // A different listener: what the old one kept is not news, and
                // what it said it was about is for the new one's hello to say.
                prefs.forgetPosition(existing.id)
                NotifierApplication.recents(ui.context).clear(existing.id)
                MonitorState.updateAccount(existing.id) { it.copy(recent = emptyList()) }
                existing.copy(url = url, apiKey = typed, label = "", broker = Accounts.guessBroker(url), paper = null)
            }
            else -> existing.copy(apiKey = typed)
        }
        prefs.save(account)
        prefs.currentId = account.id
        prefs.monitoring = true
        adding = false
        filledFor = account.id
        address.setText(url)
        key.setText(typed)
        MonitorState.setAccounts(prefs.accounts, account.id)
        MonitorService.restart(ui.context)
        askToNotify()
        onConnected()
    }

    private fun watch(on: Boolean) {
        prefs.monitoring = on
        if (on) MonitorService.start(ui.context) else MonitorService.stop(ui.context)
        last?.let(::render)
    }

    /** A test from the account being edited's listener: said plainly when there is none to ask. */
    private fun sendTest() {
        val account = if (adding) null else prefs.account(prefs.currentId)
        val connected = account != null && MonitorState.snapshot.stateOf(account.id).link is BridgeClient.Link.Connected
        if (connected) MonitorService.requestTest(ui.context, account?.id)
        val name = account?.name ?: ui.string(R.string.account_new_header)
        Toast.makeText(ui.context, ui.string(if (connected) R.string.test_asked else R.string.test_not_connected, name), Toast.LENGTH_LONG).show()
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

    private fun batteryUnrestricted(): Boolean =
        ui.context.getSystemService(PowerManager::class.java)?.isIgnoringBatteryOptimizations(ui.context.packageName) != false

    /** Android's own dialog to exempt this app; its list of apps where that dialog is not offered. */
    @SuppressLint("BatteryLife") // Sideloaded, and holding connections open is the app's whole job.
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

    private fun confirmRemove() {
        val account = prefs.account(prefs.currentId) ?: return
        AlertDialog.Builder(ui.context)
            .setTitle(ui.string(R.string.account_remove_title, account.name))
            .setMessage(ui.string(R.string.account_remove_body))
            .setNegativeButton(android.R.string.cancel, null)
            .setPositiveButton(ui.string(R.string.account_remove_confirm)) { _, _ ->
                prefs.remove(account.id)
                NotifierApplication.recents(ui.context).clear(account.id)
                filledFor = null
                MonitorState.setAccounts(prefs.accounts, prefs.currentId)
                if (prefs.isConfigured) {
                    MonitorService.restart(ui.context)
                } else {
                    prefs.monitoring = false
                    MonitorService.stop(ui.context)
                    address.setText("")
                    key.setText("")
                }
            }
            .show()
    }

    private fun toggleKey(button: ImageButton) {
        keyShown = !keyShown
        key.inputType = if (keyShown) SHOWN_KEY else HIDDEN_KEY
        key.typeface = Typeface.MONOSPACE
        key.setSelection(key.text.length)
        button.contentDescription = ui.string(if (keyShown) R.string.hide_key else R.string.show_key)
    }

    private fun input(hint: String, type: Int): EditText = EditText(ui.context).apply {
        this.hint = hint
        // Single line first: setting it replaces the transformation, so set
        // after the input type it would show a password field's key in clear.
        isSingleLine = true
        inputType = type
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
        const val ADDING = "connect_adding"
    }
}
