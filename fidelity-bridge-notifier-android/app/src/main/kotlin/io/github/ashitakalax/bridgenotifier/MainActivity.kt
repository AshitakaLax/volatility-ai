package io.github.ashitakalax.bridgenotifier

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.text.format.DateFormat
import android.view.View
import android.view.WindowInsetsController
import android.widget.FrameLayout
import android.widget.TextView

/** The app's pages. Connect is the settings page; the other three have tabs. */
enum class Tab { CONNECT, HOME, LOTS, ACTIVITY }

/**
 * Four pages over a tab bar: Home, Lots and Activity, and Connect until the
 * bridge is set (or at every start, if switched on there). A notification
 * opens the page that says more about it. Each page redraws from
 * MonitorState's snapshot.
 */
class MainActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var screens: Map<Tab, Screen>
    private lateinit var container: FrameLayout
    private lateinit var nav: View
    private lateinit var navRule: View
    private lateinit var tabs: Map<Tab, TextView>
    private var current = Tab.HOME
    private var stopObserving: (() -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        matchSystemBars()
        prefs = Prefs(this)
        val ui = Ui(this)
        screens = mapOf(
            Tab.CONNECT to ConnectScreen(ui, prefs, ::askToNotify) { show(Tab.HOME) },
            Tab.HOME to HomeScreen(ui, prefs, ::show),
            Tab.LOTS to LotsScreen(ui),
            Tab.ACTIVITY to ActivityScreen(ui),
        )
        container = findViewById(R.id.screen)
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
        show(
            saved ?: when {
                !prefs.isConfigured || prefs.openConnectAtStart -> Tab.CONNECT
                else -> tabOf(intent) ?: Tab.HOME
            },
        )

        // Asked once there is something to be notified about: on Save and
        // connect the first time (ConnectScreen), here from then on.
        if (prefs.isConfigured) askToNotify()
        // Watching, but the process was gone (an update, the system): pick it up again.
        if (prefs.monitoring && prefs.isConfigured) MonitorService.start(this)
    }

    /** Already open, and a notification was tapped: its page. */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (prefs.isConfigured) tabOf(intent)?.let(::show)
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
    }

    override fun onStop() {
        stopObserving?.invoke()
        stopObserving = null
        super.onStop()
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
        screens.getValue(current).render(snapshot)
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

    private fun tabNamed(name: String): Tab? = Tab.values().firstOrNull { it.name == name }

    private fun tabOf(intent: Intent?): Tab? = intent?.getStringExtra(Alerts.EXTRA_TAB)?.let(::tabNamed)

    private companion object {
        const val REQUEST_NOTIFY = 1
        const val TAB = "tab"
    }
}
