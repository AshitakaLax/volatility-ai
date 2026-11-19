package io.github.ashitakalax.bridgenotifier

import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.Notification

/**
 * What the service knows, for the screen to show: each account's link,
 * status and recent notifications, and which account the pages show. Main
 * thread only: the service hands everything over there before it lands here.
 */
object MonitorState {
    // As many as a listener keeps for a replay: the Activity page's history.
    const val RECENT = 200

    /** Whether the phone itself is somewhere an account's listener can be reached from. */
    enum class Phone {
        ONLINE,

        /** No network at all. */
        OFFLINE,

        /** On mobile data alone, and the listener is at an address only its own network reaches. */
        AWAY,
    }

    /** One account's connection and what it said. */
    data class AccountState(
        val link: BridgeClient.Link = BridgeClient.Link.Idle,
        val status: BridgeStatus = BridgeStatus.UNKNOWN,
        /** When [status] arrived, by the phone's clock; null before the first. */
        val statusAt: Long? = null,
        val recent: List<Notification> = emptyList(),
        /** When its listener was last heard (epoch milliseconds), in this run of the app. */
        val heardAt: Long? = null,
        /** Whether the phone can be where this account's listener is. */
        val phone: Phone = Phone.ONLINE,
    )

    data class Snapshot(
        val accounts: List<Account> = emptyList(),
        val currentId: String? = null,
        val states: Map<String, AccountState> = emptyMap(),
    ) {
        /** The account the pages show. */
        val account: Account? get() = accounts.firstOrNull { it.id == currentId } ?: accounts.firstOrNull()

        fun stateOf(id: String?): AccountState = id?.let { states[it] } ?: AccountState()

        private val current: AccountState get() = stateOf(account?.id)

        // The current account's, so a page reads as it did with one bridge.
        val link: BridgeClient.Link get() = current.link
        val status: BridgeStatus get() = current.status
        val recent: List<Notification> get() = current.recent
        val statusAt: Long? get() = current.statusAt
        val phone: Phone get() = current.phone
    }

    var snapshot = Snapshot()
        private set

    private val observers = mutableListOf<(Snapshot) -> Unit>()

    /** Calls [observer] now and on every change; returns how to stop. */
    fun observe(observer: (Snapshot) -> Unit): () -> Unit {
        observers += observer
        observer(snapshot)
        return { observers -= observer }
    }

    fun update(change: (Snapshot) -> Snapshot) {
        snapshot = change(snapshot)
        observers.toList().forEach { it(snapshot) }
    }

    /** The accounts as saved; the state of one no longer saved is dropped. */
    fun setAccounts(accounts: List<Account>, currentId: String?) = update { snapshot ->
        val ids = accounts.map { it.id }.toSet()
        snapshot.copy(accounts = accounts, currentId = currentId, states = snapshot.states.filterKeys { it in ids })
    }

    fun updateAccount(id: String, change: (AccountState) -> AccountState) = update { snapshot ->
        snapshot.copy(states = snapshot.states + (id to change(snapshot.stateOf(id))))
    }
}
