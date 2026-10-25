package io.github.ashitakalax.bridgenotifier.core

import kotlin.random.Random

/**
 * How long to wait before trying the bridge again: doubling from
 * [initialMillis] up to [maxMillis], each wait drawn from its upper half so
 * that two phones never retry in step. [reset] once connected.
 */
class Backoff(
    private val initialMillis: Long = 1_000,
    private val maxMillis: Long = 60_000,
    private val random: Random = Random.Default,
) {
    private var attempt = 0

    fun next(): Long {
        val ceiling = minOf(maxMillis, initialMillis shl minOf(attempt, 20))
        attempt += 1
        return ceiling / 2 + random.nextLong(ceiling / 2 + 1)
    }

    fun reset() {
        attempt = 0
    }
}
