package io.github.ashitakalax.bridgenotifier

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Typeface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.format.DateFormat
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowInsetsController
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

/**
 * The app's pages. Connect is the settings page; Overview, all accounts at
 * once, is there with more than one; the other three have tabs.
 */
enum class Tab { CONNECT, OVERVIEW, HOME, LOTS, ACTIVITY }

/**
 * Four pages over a tab bar: Connect at start-up (until switched off there),
 * then Home, Lots and Activity -- and, with more than one account, All
 * accounts first. Each page redraws from MonitorState's snapshot, for the
 * account shown: the whole screen wears that account's broker colour (Alpaca
 * yellow, Fidelity green), and a chip each over the page switches between
 * them. A notification tapped opens its account on the page it is about.
 * LockGate asks for the owner's fingerprint, face or screen lock before any
 * of it shows.
 */
class MainActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var ui: Ui
    private lateinit var screens: Map<Tab, Screen>
    private lateinit var lots: LotsScreen
    private lateinit var root: View
    private lateinit var accountBar: View
    private lateinit var accountChips: LinearLayout
    private lateinit var updateBar: LinearLayout
    private lateinit var container: FrameLayout
    private lateinit var nav: View
    private lateinit var navRule: View
    private lateinit var tabs: Map<Tab, TextView>
    private lateinit var gate: LockGate
    private var current = Tab.HOME
    private var askedToNotify = false
    private var stopObserving: (() -> Unit)? = null
    private val main = Handler(Looper.getMainLooper())

    /** "Last heard 4 minutes ago" goes stale too: redrawn every half minute while in sight. */
    private val refresh = object : Runnable {
        override fun run() {
            render(MonitorState.snapshot)
            main.postDelayed(this, REFRESH_MILLIS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        matchSystemBars()
        prefs = Prefs(this)
        ui = Ui(this)
        root = findViewById(R.id.root)
        gate = LockGate(this, ui, prefs, root) { locked ->
            wear(MonitorState.snapshot)
            // Asked once the owner is in, not over the lock, and once there is
            // something to be notified about: on Save and connect the first
            // time (ConnectScreen), here from then on.
            if (!locked && !askedToNotify && prefs.isConfigured) {
                askedToNotify = true
                askToNotify()
            }
        }
        addContentView(gate.view, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        MonitorState.setAccounts(prefs.accounts, prefs.currentId)
        lots = LotsScreen(ui)
        screens = mapOf(
            Tab.CONNECT to ConnectScreen(ui, prefs, ::askToNotify) { show(Tab.HOME) },
            Tab.OVERVIEW to OverviewScreen(ui, prefs, open = { account -> pick(account.id, Tab.HOME) }, go = ::show),
            Tab.HOME to HomeScreen(ui, prefs, ::show),
            Tab.LOTS to lots,
            Tab.ACTIVITY to ActivityScreen(ui),
        )
        container = findViewById(R.id.screen)
        accountBar = findViewById(R.id.account_bar)
        accountChips = findViewById(R.id.account_chips)
        updateBar = findViewById(R.id.update_bar)
        nav = findViewById(R.id.nav)
        navRule = findViewById(R.id.nav_rule)
        tabs = mapOf(
            Tab.HOME to findViewById(R.id.nav_home),
            Tab.LOTS to findViewById(R.id.nav_lots),
            Tab.ACTIVITY to findViewById(R.id.nav_activity),
        )
        tabs.forEach { (tab, view) -> view.setOnClickListener { show(tab) } }

        // Turned, or the phone went dark: back to the same page, as it was.
        savedInstanceState?.let { state -> screens.values.forEach { it.restore(state) } }
        val saved = savedInstanceState?.getString(TAB)?.let(::tabNamed)
        val asked = if (savedInstanceState == null) opened(intent) else null
        show(saved ?: asked ?: if (!prefs.isConfigured || prefs.openConnectAtStart) Tab.CONNECT else landing())

        // Watching, but the process was gone (an update, the system): pick it up again.
        if (prefs.monitoring && prefs.isConfigured) MonitorService.start(this)
    }

    /** A notification tapped while the app was open: its account, on its page. */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        opened(intent)?.let(::show)
    }

    /**
     * What a notification's tap asks for (Alerts.open): the account it is
     * about made the one shown, and the page to show; null for none.
     */
    private fun opened(intent: Intent?): Tab? {
        val page = intent?.getStringExtra(EXTRA_PAGE)?.let(::tabNamed) ?: return null
        val id = intent.getStringExtra(EXTRA_ACCOUNT)
        if (id != null && prefs.account(id) != null) {
            prefs.currentId = id
            MonitorState.setAccounts(prefs.accounts, id)
        }
        if (page == Tab.LOTS) lots.showSales(intent.getBooleanExtra(EXTRA_SALES, false))
        return page
    }

    /** Home with one account; with more, all of them at once. */
    private fun landing(): Tab = if (prefs.accounts.size > 1) Tab.OVERVIEW else Tab.HOME

    private fun pick(id: String, tab: Tab) {
        prefs.currentId = id
        MonitorState.setAccounts(prefs.accounts, id)
        show(tab)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString(TAB, current.name)
        screens.values.forEach { it.save(outState) }
    }

    override fun onStart() {
        super.onStart()
        Format.twentyFourHour = DateFormat.is24HourFormat(this)
        stopObserving = MonitorState.observe(::render)
        // Locked, the app's card in Recents must not show the page either.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) setRecentsScreenshotEnabled(!prefs.lockApp)
        gate.started()
        main.postDelayed(refresh, REFRESH_MILLIS)
        UpdateChecker.maybeCheck(this)
    }

    override fun onStop() {
        gate.stopped()
        main.removeCallbacks(refresh)
        stopObserving?.invoke()
        stopObserving = null
        super.onStop()
    }

    @Deprecated("Activity.onActivityResult; this app has no AndroidX")
    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (!gate.onActivityResult(requestCode, resultCode)) super.onActivityResult(requestCode, resultCode, data)
    }

    @Deprecated("Activity.onBackPressed; this app has no AndroidX")
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        // Back from a page returns Home, and Home to all accounts, before it leaves the app.
        val back = when {
            !prefs.isConfigured -> null
            current == Tab.HOME -> Tab.OVERVIEW.takeIf { prefs.accounts.size > 1 }
            current == Tab.OVERVIEW -> null
            else -> Tab.HOME
        }
        if (back != null) show(back) else super.onBackPressed()
    }

    private fun show(tab: Tab) {
        current = if (tab == Tab.OVERVIEW && MonitorState.snapshot.accounts.size < 2) Tab.HOME else tab
        container.removeAllViews()
        container.addView(screens.getValue(current).view)
        val withTabs = current != Tab.CONNECT
        nav.visibility = if (withTabs) View.VISIBLE else View.GONE
        navRule.visibility = nav.visibility
        tabs.forEach { (each, view) ->
            val on = each == current
            val color = getColor(if (on) R.color.accent else R.color.muted)
            view.setTextColor(color)
            view.compoundDrawableTintList = ColorStateList.valueOf(color)
            view.typeface = Typeface.create(Typeface.SANS_SERIF, if (on) Typeface.BOLD else Typeface.NORMAL)
            view.isSelected = on
        }
        render(MonitorState.snapshot)
    }

    private fun render(snapshot: MonitorState.Snapshot) {
        // An account removed down to one: there is no "all" to show.
        if (current == Tab.OVERVIEW && snapshot.accounts.size < 2) return show(Tab.HOME)
        wear(snapshot)
        renderUpdate()
        screens.getValue(current).render(snapshot)
    }

    /** The account shown's colour on the whole screen, and the chips to switch. */
    @Suppress("DEPRECATION") // statusBarColor: this app opts out of edge-to-edge (values-v35)
    private fun wear(snapshot: MonitorState.Snapshot) {
        val overview = current == Tab.OVERVIEW
        val look = if (overview) BrokerLook.of(null) else BrokerLook.of(snapshot.account?.broker)
        root.setBackgroundColor(getColor(look.ground))
        // Locked, not even the colour says which account was showing.
        window.statusBarColor = getColor(if (gate.locked) R.color.ground else look.ground)
        val many = snapshot.accounts.size > 1 && current != Tab.CONNECT
        accountBar.visibility = if (many) View.VISIBLE else View.GONE
        accountChips.removeAllViews()
        if (!many) return
        val spaced = { LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { marginEnd = ui.dp(8) } }
        accountChips.addView(ui.accountChip(getString(R.string.chip_all), BrokerLook.of(null), selected = overview) { show(Tab.OVERVIEW) }, spaced())
        val now = System.currentTimeMillis()
        for (account in snapshot.accounts) {
            accountChips.addView(
                ui.accountChip(
                    if (account.mutedAt(now)) getString(R.string.chip_muted, account.name) else account.name,
                    BrokerLook.of(account.broker),
                    selected = !overview && account.id == snapshot.account?.id,
                ) {
                    if (overview) pick(account.id, Tab.HOME) else pick(account.id, current)
                },
                spaced(),
            )
        }
    }

    /** A newer app is out: a banner over every page but Connect (which says it too), until closed. */
    private fun renderUpdate() {
        val release = UpdateChecker.available(prefs)
            ?.takeIf { it.version != prefs.dismissedVersion && current != Tab.CONNECT }
        updateBar.removeAllViews()
        updateBar.visibility = if (release != null) View.VISIBLE else View.GONE
        if (release == null) return
        updateBar.background = ui.rounded(R.color.accent_soft, radius = 12, stroke = R.color.accent)
        updateBar.addView(
            ui.grow(
                ui.column().apply {
                    addView(ui.text(getString(R.string.update_title, release.version ?: release.tag), size = 13f, bold = true))
                    addView(ui.text(UpdateChecker.howToInstall(this@MainActivity, release), size = 12f, color = R.color.ink_soft))
                },
            ),
        )
        updateBar.addView(
            ui.text(getString(R.string.update_get), size = 13f, color = R.color.accent, bold = true).apply {
                gravity = Gravity.CENTER
                minimumWidth = ui.dp(48)
                minHeight = ui.dp(44)
                setOnClickListener { openPage(release.page) }
            },
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
        )
        updateBar.addView(
            ui.text("✕", size = 15f, color = R.color.muted).apply {
                gravity = Gravity.CENTER
                minimumWidth = ui.dp(44)
                minHeight = ui.dp(44)
                contentDescription = getString(R.string.update_dismiss)
                setOnClickListener {
                    prefs.dismissedVersion = release.version
                    renderUpdate()
                }
            },
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
        )
    }

    private fun openPage(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (_: android.content.ActivityNotFoundException) {
            android.widget.Toast.makeText(this, url, android.widget.Toast.LENGTH_LONG).show()
        }
    }

    /**
     * Dark icons on the light bars, light ones on the dark: the theme says so
     * for the status bar, and this for the navigation bar too where the
     * system can be told (Android 11 on).
     */
    private fun matchSystemBars() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return
        val night = resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES
        val light = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
        window.insetsController?.setSystemBarsAppearance(if (night) 0 else light, light)
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

    companion object {
        /** A notification's tap: the account it is about, and the page (a Tab's name). */
        const val EXTRA_ACCOUNT = "open_account"
        const val EXTRA_PAGE = "open_page"

        /** With the Lots page: its sales rather than its open lots. */
        const val EXTRA_SALES = "open_sales"

        private const val REQUEST_NOTIFY = 1
        private const val TAB = "tab"
        private const val REFRESH_MILLIS = 30_000L

        private fun tabNamed(name: String): Tab? = Tab.entries.firstOrNull { it.name == name }
    }
}
