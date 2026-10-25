package io.github.ashitakalax.bridgenotifier

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.format.DateUtils
import android.text.style.StyleSpan
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import io.github.ashitakalax.bridgenotifier.core.ApiKeys
import io.github.ashitakalax.bridgenotifier.core.BridgeAddress
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.HostStatus
import io.github.ashitakalax.bridgenotifier.core.Notification

/** One screen: how the bridge is, what it said lately, and the settings. */
class MainActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var linkText: TextView
    private lateinit var readinessText: TextView
    private lateinit var readinessList: LinearLayout
    private lateinit var sessionText: TextView
    private lateinit var checkText: TextView
    private lateinit var extensionText: TextView
    private lateinit var tradingText: TextView
    private lateinit var engineText: TextView
    private lateinit var recentList: LinearLayout
    private lateinit var recentEmpty: TextView
    private lateinit var addressInput: EditText
    private lateinit var keyInput: EditText
    private lateinit var plainTextWarning: TextView
    private lateinit var notificationsWarning: TextView
    private lateinit var alertUnreachable: CheckBox
    private var stopObserving: (() -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        prefs = Prefs(this)

        linkText = view(R.id.link_text)
        extensionText = view(R.id.extension_text)
        tradingText = view(R.id.trading_text)
        engineText = view(R.id.engine_text)
        readinessText = view(R.id.readiness_text)
        readinessList = view(R.id.readiness_list)
        sessionText = view(R.id.session_text)
        checkText = view(R.id.check_text)
        recentList = view(R.id.recent_list)
        recentEmpty = view(R.id.recent_empty)
        addressInput = view(R.id.address_input)
        keyInput = view(R.id.key_input)
        plainTextWarning = view(R.id.plaintext_warning)
        notificationsWarning = view(R.id.notifications_warning)
        alertUnreachable = view(R.id.alert_unreachable)

        addressInput.setText(prefs.url)
        keyInput.setText(prefs.apiKey)
        alertUnreachable.isChecked = prefs.alertWhenUnreachable
        alertUnreachable.setOnCheckedChangeListener { _, checked -> prefs.alertWhenUnreachable = checked }
        buildKindSwitches(view(R.id.kinds_list))

        view<Button>(R.id.save_button).setOnClickListener { saveAndWatch() }
        view<Button>(R.id.stop_button).setOnClickListener {
            prefs.monitoring = false
            MonitorService.stop(this)
        }
        view<Button>(R.id.test_button).setOnClickListener { MonitorService.requestTest(this) }

        askToNotify()
        // Watching, but the process was gone (an update, the system): pick it up again.
        if (prefs.monitoring && prefs.isConfigured) MonitorService.start(this)
    }

    private fun <T : View> view(id: Int): T = findViewById<T>(id)!!

    override fun onStart() {
        super.onStart()
        stopObserving = MonitorState.observe(::render)
        notificationsWarning.visibility = if (Alerts.notificationsEnabled(this)) View.GONE else View.VISIBLE
    }

    override fun onStop() {
        stopObserving?.invoke()
        stopObserving = null
        super.onStop()
    }

    private fun buildKindSwitches(container: LinearLayout) {
        for (kind in EventKind.ALL) {
            val box = CheckBox(this)
            box.text = EventKind.label(kind)
            box.isChecked = kind !in prefs.disabledKinds
            box.setOnCheckedChangeListener { _, checked ->
                prefs.disabledKinds = if (checked) prefs.disabledKinds - kind else prefs.disabledKinds + kind
            }
            container.addView(box)
        }
    }

    private fun saveAndWatch() {
        val url = BridgeAddress.parse(addressInput.text.toString())
        if (url == null) {
            addressInput.error = getString(R.string.error_address)
            return
        }
        val key = keyInput.text.toString().trim()
        if (!ApiKeys.looksValid(key)) {
            keyInput.error = getString(R.string.error_key)
            return
        }
        if (url != prefs.url) prefs.forgetPosition()
        prefs.url = url
        prefs.apiKey = key
        prefs.monitoring = true
        addressInput.setText(url)
        MonitorService.restart(this)
    }

    private fun askToNotify() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_NOTIFY)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        notificationsWarning.visibility = if (Alerts.notificationsEnabled(this)) View.GONE else View.VISIBLE
    }

    private fun render(snapshot: MonitorState.Snapshot) {
        renderLink(snapshot.link)
        renderStatus(snapshot.status)
        renderRecent(snapshot.recent)
        plainTextWarning.visibility = if (BridgeAddress.isPlainText(prefs.url)) View.VISIBLE else View.GONE
    }

    private fun renderLink(link: BridgeClient.Link) {
        val (text, color) = when (link) {
            is BridgeClient.Link.Connected -> getString(R.string.link_connected, MonitorService.hostOf(prefs.url)) to R.color.status_ok
            BridgeClient.Link.Connecting -> getString(R.string.link_connecting, MonitorService.hostOf(prefs.url)) to R.color.status_warn
            is BridgeClient.Link.Waiting -> getString(
                if (link.deliberate) R.string.link_stopped_by_bridge else R.string.link_waiting,
                link.reason,
                (link.retryInMillis + 999) / 1000,
            ) to if (link.deliberate) R.color.status_idle else R.color.status_warn
            is BridgeClient.Link.Refused -> getString(R.string.link_refused, link.reason) to R.color.status_bad
            BridgeClient.Link.Idle, BridgeClient.Link.Stopped -> getString(R.string.link_idle) to R.color.status_idle
        }
        linkText.text = text
        linkText.setTextColor(getColor(color))
    }

    /** Ready to trade, or the one thing to fix -- and the chain behind it. */
    private fun renderReadiness(host: HostStatus?) {
        readinessList.removeAllViews()
        if (host == null) {
            readinessText.text = getString(R.string.readiness_unknown)
            readinessText.setTextColor(getColor(R.color.status_idle))
            sessionText.visibility = View.GONE
            checkText.visibility = View.GONE
            return
        }
        readinessText.text = if (host.ready) {
            getString(R.string.readiness_ready)
        } else {
            getString(R.string.readiness_not_ready, host.summary) +
                (host.fix?.let { "\n" + getString(R.string.readiness_fix, it) } ?: "")
        }
        readinessText.setTextColor(getColor(if (host.ready) R.color.status_ok else R.color.status_bad))
        for (item in host.items) {
            val (mark, color) = when (item.state) {
                "ok" -> "✓" to R.color.status_ok
                "warn" -> "!" to R.color.status_warn
                "fail" -> "✗" to R.color.status_bad
                else -> "?" to R.color.status_idle
            }
            val row = TextView(this)
            row.text = "$mark ${item.label}: ${item.detail}" +
                (item.fix?.takeIf { item.state == "fail" }?.let { "\n   " + getString(R.string.readiness_fix, it) } ?: "")
            row.setTextColor(getColor(color))
            readinessList.addView(row)
        }
        sessionText.visibility = View.VISIBLE
        sessionText.text = when {
            host.sessionOpen && host.attached == "loop" ->
                getString(R.string.session_open_attached, ago(host.attachedSince))
            host.sessionOpen -> getString(R.string.session_open_none)
            else -> getString(R.string.session_closed, ago(host.nextOpen))
        }
        checkText.visibility = View.VISIBLE
        val check = host.lastCheck
        checkText.text = when {
            check == null -> getString(R.string.check_never)
            check.ok -> getString(R.string.check_passed, ago(check.at), check.detail)
            else -> getString(R.string.check_failed, ago(check.at), check.detail)
        }
    }

    private fun renderStatus(status: BridgeStatus) {
        renderReadiness(status.bridge)
        val extension = status.extension
        extensionText.text = when {
            extension == null -> getString(R.string.unknown)
            extension.connected -> getString(
                R.string.extension_connected,
                extension.version ?: "?",
                ago(extension.since),
            )
            else -> getString(R.string.extension_disconnected, ago(extension.disconnectedAt))
        } + (extension?.advice?.let { "\n$it" } ?: "")
        tradingText.text = getString(
            when (extension?.trading) {
                true -> R.string.trading_on
                false -> R.string.trading_off
                null -> R.string.trading_unknown
            },
        )
        val engine = status.engine
        engineText.text = if (engine == null) {
            getString(R.string.engine_unknown)
        } else {
            listOfNotNull(
                listOfNotNull(engine.state, engine.symbol, engine.mode).joinToString(" · "),
                engine.detail,
                engine.lastTickAt?.let { getString(R.string.engine_last_tick, ago(it)) },
            ).joinToString("\n")
        }
    }

    private fun renderRecent(recent: List<Notification>) {
        recentList.removeAllViews()
        recentEmpty.visibility = if (recent.isEmpty()) View.VISIBLE else View.GONE
        for (notification in recent.take(SHOWN)) {
            val text = SpannableStringBuilder(notification.title)
            text.setSpan(StyleSpan(Typeface.BOLD), 0, text.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            if (notification.body.isNotEmpty()) text.append('\n').append(notification.body)
            text.append('\n').append(ago(notification.at))
            val view = TextView(this)
            view.text = text
            view.setPadding(0, 0, 0, resources.getDimensionPixelSize(R.dimen.item_gap))
            recentList.addView(view)
        }
    }

    private fun ago(iso: String?): String {
        val millis = iso?.let(Alerts::epochMillis) ?: return getString(R.string.unknown)
        return DateUtils.getRelativeTimeSpanString(millis).toString()
    }

    private companion object {
        const val REQUEST_NOTIFY = 1
        const val SHOWN = 20
    }
}
