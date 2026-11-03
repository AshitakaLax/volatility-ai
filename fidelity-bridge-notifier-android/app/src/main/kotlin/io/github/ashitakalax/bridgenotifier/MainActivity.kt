package io.github.ashitakalax.bridgenotifier

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.FrameLayout
import android.widget.TextView

/** The app's pages. Connect is the settings page; the other three have tabs. */
enum class Tab { CONNECT, HOME, LOTS, ACTIVITY }

/**
 * Four pages over a tab bar: Connect at start-up (until switched off there),
 * then Home, Lots and Activity. Each page redraws from MonitorState's snapshot.
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
        prefs = Prefs(this)
        val ui = Ui(this)
        screens = mapOf(
            Tab.CONNECT to ConnectScreen(ui, prefs) { show(Tab.HOME) },
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

        val saved = savedInstanceState?.getString(TAB)?.let { name -> Tab.values().firstOrNull { it.name == name } }
        show(saved ?: if (!prefs.isConfigured || prefs.openConnectAtStart) Tab.CONNECT else Tab.HOME)

        askToNotify()
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
