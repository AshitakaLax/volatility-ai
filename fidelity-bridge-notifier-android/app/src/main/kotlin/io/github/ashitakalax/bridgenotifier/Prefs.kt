package io.github.ashitakalax.bridgenotifier

import android.content.Context
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.Accounts
import io.github.ashitakalax.bridgenotifier.core.Broker
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Position
import io.github.ashitakalax.bridgenotifier.core.PositionStore

/**
 * The app's settings, its accounts, and where each left off. Private to the
 * app and kept out of backups (AndroidManifest.xml): the keys only read
 * notifications, but they are still keys.
 */
class Prefs(context: Context) {
    private val prefs = context.getSharedPreferences("bridge_notifier", Context.MODE_PRIVATE)

    init {
        migrate()
        migrateKinds()
    }

    /** Every account the app watches, in the order they were added. */
    var accounts: List<Account>
        get() = Accounts.decode(prefs.getString(ACCOUNTS, null))
        private set(value) = prefs.edit().putString(ACCOUNTS, Accounts.encode(value)).apply()

    /** The account the pages show; the first when the one chosen is gone. */
    var currentId: String?
        get() = prefs.getString(CURRENT, null)?.takeIf { id -> accounts.any { it.id == id } }
            ?: accounts.firstOrNull()?.id
        set(value) = prefs.edit().putString(CURRENT, value).apply()

    fun account(id: String?): Account? = accounts.firstOrNull { it.id == id }

    /** Change the saved [id] account, if it is still saved: what else changed it since is kept. */
    fun change(id: String, change: (Account) -> Account): Account? {
        val account = account(id) ?: return null
        return change(account).also(::save)
    }

    /** Add [account], or replace the one with its id. */
    fun save(account: Account) {
        val list = accounts
        accounts = if (list.any { it.id == account.id }) {
            list.map { if (it.id == account.id) account else it }
        } else {
            list + account
        }
    }

    fun remove(id: String) {
        accounts = accounts.filterNot { it.id == id }
        forgetPosition(id)
        if (prefs.getString(CURRENT, null) == id) prefs.edit().remove(CURRENT).apply()
    }

    /** Whether the app should be watching: survives a reboot. */
    var monitoring: Boolean
        get() = prefs.getBoolean(MONITORING, false)
        set(value) = prefs.edit().putBoolean(MONITORING, value).apply()

    /** Whether the app says so when it cannot reach an account's listener. */
    var alertWhenUnreachable: Boolean
        get() = prefs.getBoolean(ALERT_UNREACHABLE, true)
        set(value) = prefs.edit().putBoolean(ALERT_UNREACHABLE, value).apply()

    /** Whether the app opens on its Connect page; off, it opens on Home once set up. */
    var openConnectAtStart: Boolean
        get() = prefs.getBoolean(OPEN_CONNECT, true)
        set(value) = prefs.edit().putBoolean(OPEN_CONNECT, value).apply()

    /** How long a listener may be unreachable before that is worth saying. */
    val unreachableGraceMillis: Long
        get() = prefs.getLong(UNREACHABLE_GRACE, 120_000L)

    val isConfigured: Boolean
        get() = accounts.isNotEmpty()

    /** Where one account left off, so a restart does not show anything twice. */
    fun positions(id: String): PositionStore = object : PositionStore {
        override fun load(): Position? {
            val stream = prefs.getString(STREAM + id, null) ?: return null
            return Position(stream, prefs.getLong(LAST_ID + id, 0L))
        }

        override fun save(position: Position) {
            prefs.edit().putString(STREAM + id, position.stream).putLong(LAST_ID + id, position.id).apply()
        }
    }

    /** A different listener: what it kept before is history, not news. */
    fun forgetPosition(id: String) {
        prefs.edit().remove(STREAM + id).remove(LAST_ID + id).apply()
    }

    /** One bridge's address and key, from before there were accounts, become the first account. */
    private fun migrate() {
        if (prefs.contains(ACCOUNTS)) return
        val url = prefs.getString(LEGACY_URL, null).orEmpty()
        val key = prefs.getString(LEGACY_KEY, null).orEmpty()
        val edit = prefs.edit().putString(ACCOUNTS, Accounts.encode(emptyList()))
        if (url.isNotEmpty() && key.isNotEmpty()) {
            val id = "a1"
            edit.putString(ACCOUNTS, Accounts.encode(listOf(Account(id, url, key, broker = Broker.FIDELITY))))
                .putString(CURRENT, id)
            prefs.getString(LEGACY_STREAM, null)?.let { stream ->
                edit.putString(STREAM + id, stream).putLong(LAST_ID + id, prefs.getLong(LEGACY_ID, 0L))
            }
        }
        edit.remove(LEGACY_URL).remove(LEGACY_KEY).remove(LEGACY_STREAM).remove(LEGACY_ID).apply()
    }

    /**
     * The kinds switched off when one list covered every bridge become each
     * account's own. (Settings older still kept the kinds switched ON; read
     * the other way.)
     */
    private fun migrateKinds() {
        if (!prefs.contains(DISABLED_KINDS) && !prefs.contains(ENABLED_KINDS_BEFORE)) return
        val off = prefs.getStringSet(DISABLED_KINDS, null)?.toSet()
            ?: prefs.getStringSet(ENABLED_KINDS_BEFORE, null)?.let { EventKind.ALL.toSet() - it }
            ?: emptySet()
        if (off.isNotEmpty()) accounts = accounts.map { it.copy(mutedKinds = it.mutedKinds + off) }
        prefs.edit().remove(DISABLED_KINDS).remove(ENABLED_KINDS_BEFORE).apply()
    }

    private companion object {
        const val ACCOUNTS = "accounts"
        const val CURRENT = "current_account"
        const val MONITORING = "monitoring"
        const val ALERT_UNREACHABLE = "alert_unreachable"
        const val OPEN_CONNECT = "open_connect_at_start"
        const val UNREACHABLE_GRACE = "unreachable_grace_ms"
        const val STREAM = "position_stream_"
        const val LAST_ID = "position_id_"

        // Before accounts: one bridge.
        const val LEGACY_URL = "url"
        const val LEGACY_KEY = "api_key"
        const val LEGACY_STREAM = "position_stream"
        const val LEGACY_ID = "position_id"

        // Before each account had its own: one list of kinds for every bridge.
        const val DISABLED_KINDS = "disabled_kinds"
        const val ENABLED_KINDS_BEFORE = "kinds"
    }
}
