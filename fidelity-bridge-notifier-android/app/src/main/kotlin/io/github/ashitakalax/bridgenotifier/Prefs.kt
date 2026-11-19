package io.github.ashitakalax.bridgenotifier

import android.content.Context
import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.Accounts
import io.github.ashitakalax.bridgenotifier.core.Book
import io.github.ashitakalax.bridgenotifier.core.Broker
import io.github.ashitakalax.bridgenotifier.core.DayFigures
import io.github.ashitakalax.bridgenotifier.core.EventKind
import io.github.ashitakalax.bridgenotifier.core.Position
import io.github.ashitakalax.bridgenotifier.core.PositionStore
import io.github.ashitakalax.bridgenotifier.core.ProfitHistory
import io.github.ashitakalax.bridgenotifier.core.Updates
import java.time.LocalDate

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
        histories.remove(id)
        prefs.edit().remove(HISTORY + id).remove(SUMMARY_DONE + id).remove(HEARD + id).apply()
        if (prefs.getString(CURRENT, null) == id) prefs.edit().remove(CURRENT).apply()
    }

    /** [id]'s profit, day by day, oldest first: what the listener sent, kept longer than it keeps it. */
    fun history(id: String): List<DayFigures> =
        histories.getOrPut(id) { ProfitHistory.decode(prefs.getString(HISTORY + id, null)) }

    /** [book]'s days into [id]'s history; true if that changed it. */
    fun recordBook(id: String, book: Book): Boolean {
        val before = history(id)
        val after = ProfitHistory.merge(before, book)
        if (after == before) return false
        histories[id] = after
        prefs.edit().putString(HISTORY + id, ProfitHistory.encode(after)).apply()
        return true
    }

    /** The last market day [id]'s end-of-day note covered (DailySummary). */
    fun summaryDone(id: String): LocalDate? =
        prefs.getString(SUMMARY_DONE + id, null)?.let { runCatching { LocalDate.parse(it) }.getOrNull() }

    fun setSummaryDone(id: String, day: LocalDate) {
        prefs.edit().putString(SUMMARY_DONE + id, day.toString()).apply()
    }

    /** When [id]'s listener was last heard (epoch milliseconds), kept for when the app starts out of reach. */
    fun heardAt(id: String): Long? = prefs.getLong(HEARD + id, 0L).takeIf { it > 0 }

    fun setHeardAt(id: String, at: Long) {
        prefs.edit().putLong(HEARD + id, at).apply()
    }

    /** Whether the app asks GitHub, twice a day at most, whether a newer version is out. On unless switched off. */
    var checkUpdates: Boolean
        get() = prefs.getBoolean(CHECK_UPDATES, true)
        set(value) = prefs.edit().putBoolean(CHECK_UPDATES, value).apply()

    /** When GitHub was last asked (epoch milliseconds); 0 never. */
    var updateCheckedAt: Long
        get() = prefs.getLong(UPDATE_CHECKED, 0L)
        set(value) = prefs.edit().putLong(UPDATE_CHECKED, value).apply()

    /** What GitHub last said was the latest release. */
    var latestRelease: Updates.Release?
        get() {
            val tag = prefs.getString(RELEASE_TAG, null) ?: return null
            val page = prefs.getString(RELEASE_PAGE, null) ?: return null
            return Updates.Release(prefs.getString(RELEASE_VERSION, null), tag, page, prefs.getBoolean(RELEASE_DEBUG, false))
        }
        set(value) {
            prefs.edit().apply {
                if (value == null) {
                    remove(RELEASE_TAG).remove(RELEASE_PAGE).remove(RELEASE_VERSION).remove(RELEASE_DEBUG)
                } else {
                    putString(RELEASE_TAG, value.tag).putString(RELEASE_PAGE, value.page)
                        .putString(RELEASE_VERSION, value.version).putBoolean(RELEASE_DEBUG, value.debugOnly)
                }
            }.apply()
        }

    /** Why the last check failed; null when it worked. */
    var updateError: String?
        get() = prefs.getString(UPDATE_ERROR, null)
        set(value) = prefs.edit().putString(UPDATE_ERROR, value).apply()

    /** The newer version a notification already said is out, so it is said once. */
    var announcedVersion: String?
        get() = prefs.getString(ANNOUNCED, null)
        set(value) = prefs.edit().putString(ANNOUNCED, value).apply()

    /** The newer version whose banner was closed. */
    var dismissedVersion: String?
        get() = prefs.getString(DISMISSED, null)
        set(value) = prefs.edit().putString(DISMISSED, value).apply()

    /** Whether the app should be watching: survives a reboot. */
    var monitoring: Boolean
        get() = prefs.getBoolean(MONITORING, false)
        set(value) = prefs.edit().putBoolean(MONITORING, value).apply()

    /** Whether the app says so when it cannot reach an account's listener. */
    var alertWhenUnreachable: Boolean
        get() = prefs.getBoolean(ALERT_UNREACHABLE, true)
        set(value) = prefs.edit().putBoolean(ALERT_UNREACHABLE, value).apply()

    /**
     * Whether the app asks for a fingerprint, face or the screen lock when it
     * opens (and after a minute away). On unless switched off.
     */
    var lockApp: Boolean
        get() = prefs.getBoolean(LOCK_APP, true)
        set(value) = prefs.edit().putBoolean(LOCK_APP, value).apply()

    /** Whether the app opens on its Connect page; off (the default), it opens on Home once set up. */
    var openConnectAtStart: Boolean
        get() = prefs.getBoolean(OPEN_CONNECT, false)
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
            val id = FIRST_ACCOUNT
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

    companion object {
        /** The id the single bridge of before accounts became (migrate), and Recents' old list with it. */
        const val FIRST_ACCOUNT = "a1"

        private const val ACCOUNTS = "accounts"
        private const val CURRENT = "current_account"
        private const val MONITORING = "monitoring"
        private const val ALERT_UNREACHABLE = "alert_unreachable"
        private const val OPEN_CONNECT = "open_connect_at_start"
        private const val LOCK_APP = "lock_app"
        private const val UNREACHABLE_GRACE = "unreachable_grace_ms"
        private const val STREAM = "position_stream_"
        private const val LAST_ID = "position_id_"
        private const val HISTORY = "history_"
        private const val SUMMARY_DONE = "summary_done_"
        private const val HEARD = "heard_at_"
        private const val CHECK_UPDATES = "check_updates"
        private const val UPDATE_CHECKED = "update_checked_at"
        private const val UPDATE_ERROR = "update_error"
        private const val RELEASE_TAG = "release_tag"
        private const val RELEASE_PAGE = "release_page"
        private const val RELEASE_VERSION = "release_version"
        private const val RELEASE_DEBUG = "release_debug_only"
        private const val ANNOUNCED = "update_announced"
        private const val DISMISSED = "update_dismissed"

        /** Each account's history, read once: every screen and the service share one process. Main thread only. */
        private val histories = mutableMapOf<String, List<DayFigures>>()

        // Before accounts: one bridge.
        private const val LEGACY_URL = "url"
        private const val LEGACY_KEY = "api_key"
        private const val LEGACY_STREAM = "position_stream"
        private const val LEGACY_ID = "position_id"

        // Before each account had its own: one list of kinds for every bridge.
        private const val DISABLED_KINDS = "disabled_kinds"
        private const val ENABLED_KINDS_BEFORE = "kinds"
    }
}
