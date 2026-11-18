package io.github.ashitakalax.bridgenotifier

import io.github.ashitakalax.bridgenotifier.core.Broker

/**
 * How each broker's account looks, so it is plain which one a page shows:
 * the page's ground behind the white cards, and a strong colour (with the ink
 * that reads on it) for its badge, its chip and its notifications.
 */
data class BrokerLook(val ground: Int, val strong: Int, val onStrong: Int) {
    companion object {
        /** Alpaca yellow, Fidelity green; neutral with no account. */
        fun of(broker: Broker?): BrokerLook = when (broker) {
            Broker.ALPACA -> BrokerLook(R.color.alpaca_ground, R.color.alpaca_strong, R.color.alpaca_on_strong)
            Broker.FIDELITY -> BrokerLook(R.color.fidelity_ground, R.color.fidelity_strong, R.color.fidelity_on_strong)
            Broker.OTHER, null -> BrokerLook(R.color.ground, R.color.accent, R.color.card)
        }
    }
}
