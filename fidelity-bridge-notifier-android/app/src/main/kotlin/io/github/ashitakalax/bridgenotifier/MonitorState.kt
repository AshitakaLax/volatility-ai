package io.github.ashitakalax.bridgenotifier

import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.Notification

/**
 * What the service knows, for the screen to show. Main thread only: the
 * service hands everything over there before it lands here.
 */
object MonitorState {
    // As many as the bridge keeps for a replay: the Activity page's history.
    const val RECENT = 200

    /** Whether the phone itself is somewhere the bridge can be reached from. */
    enum class Phone {
        ONLINE,

        /** No network at all. */
        OFFLINE,

        /** On mobile data alone, and the bridge is at an address only its own network reaches. */
        AWAY,
    }

    data class Snapshot(
        val link: BridgeClient.Link = BridgeClient.Link.Idle,
        val status: BridgeStatus = BridgeStatus.UNKNOWN,
        /** When [status] arrived, by the phone's clock; null before the first. */
        val statusAt: Long? = null,
        val recent: List<Notification> = emptyList(),
        val phone: Phone = Phone.ONLINE,
    )

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
}
