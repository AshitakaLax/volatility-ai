package io.github.ashitakalax.bridgenotifier

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

/** The app's pages. Connect is the settings page; the other three have tabs. */
enum class Tab { CONNECT, HOME, LOTS, ACTIVITY }

/**
 * Four pages over a tab bar: Connect at start-up (until switched off there),
 * then Home, Lots and Activity. Each page redraws from MonitorState's snapshot,
 * for the account shown: the whole screen wears that account's broker colour
 * (Alpaca yellow, Fidelity green), and with more than one account a chip each
 * over the page switches between them. LockGate asks for the owner's
 * fingerprint, face or screen lock before any of it shows.
 */
class MainActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var ui: Ui
    private lateinit var screens: Map<Tab, Screen>
    private lateinit var root: View
    private lateinit var accountBar: View
    private lateinit var accountChips: LinearLayout
    private lateinit var container: FrameLayout
    private lateinit var nav: View
    private lateinit var navRule: View
    private lateinit var tabs: Map<Tab, TextView>
    private lateinit var gate: LockGate
    private var current = Tab.HOME
    private var askedToNotify = false
    private var stopObserving: (() -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        prefs = Prefs(this)
        ui = Ui(this)
        root = findViewById(R.id.root)
        gate = LockGate(this, ui, prefs, root) { locked ->
            wear(MonitorState.snapshot)
            // Asked once the owner is in, not over the lock.
            if (!locked && !askedToNotify) {
                askedToNotify = true
                askToNotify()
            }
        }
        addContentView(gate.view, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
        screens = mapOf(
            Tab.CONNECT to ConnectScreen(ui, prefs) { show(Tab.HOME) },
            Tab.HOME to HomeScreen(ui, ::show),
            Tab.LOTS to LotsScreen(ui),
            Tab.ACTIVITY to ActivityScreen(ui),
        )
        container = findViewById(R.id.screen)
        accountBar = findViewById(R.id.account_bar)
        accountChips = findViewById(R.id.account_chips)
        nav = findViewById(R.id.nav)
        navRule = findViewById(R.id.nav_rule)
        tabs = mapOf(
            Tab.HOME to findViewById(R.id.nav_home),
            Tab.LOTS to findViewById(R.id.nav_lots),
            Tab.ACTIVITY to findViewById(R.id.nav_activity),
        )
        tabs.forEach { (tab, view) -> view.setOnClickListener { show(tab) } }

        val saved = savedInstanceState?.getString(TAB)?.let { name -> Tab.values().firstOrNull { it.name == name } }
        show(saved ?: if (!prefs.isConfigured || prefs.openConnectAtStart) Tab.CONNECT else Tab.HOME)

        // Watching, but the process was gone (an update, the system): pick it up again.
        if (prefs.monitoring && prefs.isConfigured) MonitorService.start(this)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString(TAB, current.name)
    }

    override fun onStart() {
        super.onStart()
        stopObserving = MonitorState.observe(::render)
        // Locked, the app's card in Recents must not show the page either.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) setRecentsScreenshotEnabled(!prefs.lockApp)
        gate.started()
    }

    override fun onStop() {
        gate.stopped()
        stopObserving?.invoke()
        stopObserving = null
        super.onStop()
    }

    @Deprecated("Activity.onActivityResult; this app has no AndroidX")
    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: android.content.Intent?) {
        if (!gate.onActivityResult(requestCode, resultCode)) super.onActivityResult(requestCode, resultCode, data)
    }

    @Deprecated("Activity.onBackPressed; this app has no AndroidX")
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        // Back from a page returns Home before it leaves the app.
        if (current != Tab.HOME && prefs.isConfigured) show(Tab.HOME) else super.onBackPressed()
    }

    private fun show(tab: Tab) {
        current = tab
        container.removeAllViews()
        container.addView(screens.getValue(tab).view)
        val withTabs = tab != Tab.CONNECT
        nav.visibility = if (withTabs) View.VISIBLE else View.GONE
        navRule.visibility = nav.visibility
        tabs.forEach { (each, view) ->
            val on = each == tab
            val color = getColor(if (on) R.color.accent else R.color.muted)
            view.setTextColor(color)
            view.compoundDrawableTintList = ColorStateList.valueOf(color)
            view.typeface = Typeface.create(Typeface.SANS_SERIF, if (on) Typeface.BOLD else Typeface.NORMAL)
            view.isSelected = on
        }
        render(MonitorState.snapshot)
    }

    private fun render(snapshot: MonitorState.Snapshot) {
        wear(snapshot)
        screens.getValue(current).render(snapshot)
    }

    /** The account shown's colour on the whole screen, and the chips to switch. */
    @Suppress("DEPRECATION") // statusBarColor: this app opts out of edge-to-edge (values-v35)
    private fun wear(snapshot: MonitorState.Snapshot) {
        val look = BrokerLook.of(snapshot.account?.broker)
        root.setBackgroundColor(getColor(look.ground))
        // Locked, not even the colour says which account was showing.
        window.statusBarColor = getColor(if (gate.locked) R.color.ground else look.ground)
        val many = snapshot.accounts.size > 1 && current != Tab.CONNECT
        accountBar.visibility = if (many) View.VISIBLE else View.GONE
        accountChips.removeAllViews()
        if (!many) return
        for (account in snapshot.accounts) {
            accountChips.addView(
                ui.accountChip(
                    if (account.muted) getString(R.string.chip_muted, account.name) else account.name,
                    BrokerLook.of(account.broker),
                    selected = account.id == snapshot.account?.id,
                ) {
                    prefs.currentId = account.id
                    MonitorState.setAccounts(prefs.accounts, account.id)
                },
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                    marginEnd = ui.dp(8)
                },
            )
        }
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
        render(MonitorState.snapshot)
    }

    private companion object {
        const val REQUEST_NOTIFY = 1
        const val TAB = "tab"
    }
}
