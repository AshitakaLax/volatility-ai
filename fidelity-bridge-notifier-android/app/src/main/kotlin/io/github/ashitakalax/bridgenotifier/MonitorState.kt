package io.github.ashitakalax.bridgenotifier

import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.BridgeStatus
import io.github.ashitakalax.bridgenotifier.core.Notification

/**
 * What the service knows, for the screen to show. Main thread only: the
 * service hands everything over there before it lands here.
 */
object MonitorState {
    const val RECENT = 50

    data class Snapshot(
        val link: BridgeClient.Link = BridgeClient.Link.Idle,
        val status: BridgeStatus = BridgeStatus.UNKNOWN,
        val recent: List<Notification> = emptyList(),
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
