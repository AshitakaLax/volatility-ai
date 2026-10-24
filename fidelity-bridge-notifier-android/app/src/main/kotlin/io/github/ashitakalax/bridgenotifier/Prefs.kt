package io.github.ashitakalax.bridgenotifier

import android.content.Context
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Position
import io.github.ashitakalax.bridgenotifier.core.PositionStore

/**
 * The app's settings, and where it left off. Private to the app and kept
 * out of backups (AndroidManifest.xml): the key only reads notifications,
 * but it is still a key.
 */
class Prefs(context: Context) : PositionStore {
    private val prefs = context.getSharedPreferences("bridge_notifier", Context.MODE_PRIVATE)

    /** The listener's ws:// or wss:// URL, as BridgeAddress.parse completed it. */
    var url: String
        get() = prefs.getString(URL, "").orEmpty()
        set(value) = prefs.edit().putString(URL, value).apply()

    var apiKey: String
        get() = prefs.getString(API_KEY, "").orEmpty()
        set(value) = prefs.edit().putString(API_KEY, value).apply()

    /** Whether the app should be watching: survives a reboot. */
    var monitoring: Boolean
        get() = prefs.getBoolean(MONITORING, false)
        set(value) = prefs.edit().putBoolean(MONITORING, value).apply()

    /** Which kinds are shown as notifications. All of them until changed. */
    var enabledKinds: Set<String>
        get() = prefs.getStringSet(KINDS, null)?.toSet() ?: EventKind.ALL.toSet()
        set(value) = prefs.edit().putStringSet(KINDS, value).apply()

    /** Whether the app says so when it cannot reach the bridge. */
    var alertWhenUnreachable: Boolean
        get() = prefs.getBoolean(ALERT_UNREACHABLE, true)
        set(value) = prefs.edit().putBoolean(ALERT_UNREACHABLE, value).apply()

    /** How long the bridge may be unreachable before that is worth saying. */
    val unreachableGraceMillis: Long
        get() = prefs.getLong(UNREACHABLE_GRACE, 120_000L)

    val isConfigured: Boolean
        get() = url.isNotEmpty() && apiKey.isNotEmpty()

    override fun load(): Position? {
        val stream = prefs.getString(STREAM, null) ?: return null
        return Position(stream, prefs.getLong(LAST_ID, 0L))
    }

    override fun save(position: Position) {
        prefs.edit().putString(STREAM, position.stream).putLong(LAST_ID, position.id).apply()
    }

    /** A different bridge: what it kept before is history, not news. */
    fun forgetPosition() {
        prefs.edit().remove(STREAM).remove(LAST_ID).apply()
    }

    private companion object {
        const val URL = "url"
        const val API_KEY = "api_key"
        const val MONITORING = "monitoring"
        const val KINDS = "kinds"
        const val ALERT_UNREACHABLE = "alert_unreachable"
        const val UNREACHABLE_GRACE = "unreachable_grace_ms"
        const val STREAM = "position_stream"
        const val LAST_ID = "position_id"
    }
}
