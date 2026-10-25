package io.github.ashitakalax.bridgenotifier.core

import kotlin.random.Random
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BackoffAndAlarmTest {
    @Test
    fun theWaitDoublesUpToTheCeilingWithinItsUpperHalf() {
        val backoff = Backoff(initialMillis = 1_000, maxMillis = 8_000, random = Random(1))
        val ceilings = listOf(1_000L, 2_000, 4_000, 8_000, 8_000, 8_000)
        for (ceiling in ceilings) {
            val wait = backoff.next()
            assertTrue("$wait within ${ceiling / 2}..$ceiling", wait in ceiling / 2..ceiling)
        }
        backoff.reset()
        assertTrue(backoff.next() <= 1_000)
    }

    @Test
    fun aLossAnnouncedOnceAfterTheGraceAndItsEnd() {
        val alarm = LinkAlarm(graceMillis = 60_000)
        alarm.lost(now = 0)
        alarm.lost(now = 30_000) // still the same loss
        assertEquals(60_000L, alarm.dueAt())
        assertNull(alarm.check(now = 59_999))
        assertEquals(LinkAlarm.Alert.LOST, alarm.check(now = 60_000))
        assertNull(alarm.check(now = 120_000))
        assertNull(alarm.dueAt())
        assertEquals(LinkAlarm.Alert.BACK, alarm.connected())
        assertNull(alarm.connected())
    }

    @Test
    fun aLossThatHealsInsideTheGraceIsNothing() {
        val alarm = LinkAlarm(graceMillis = 60_000)
        alarm.lost(now = 0)
        assertNull(alarm.connected())
        assertNull(alarm.check(now = 120_000))
    }

    @Test
    fun aRestartIsGivenLongerToComeBack() {
        val alarm = LinkAlarm(graceMillis = 60_000, restartGraceMillis = 600_000)
        alarm.lost(now = 0, restarting = true)
        alarm.lost(now = 5_000) // its first retries fail while it restarts
        assertNull(alarm.check(now = 120_000))
        assertEquals(600_000L, alarm.dueAt())
        assertEquals(LinkAlarm.Alert.LOST, alarm.check(now = 600_000))
        assertEquals(LinkAlarm.Alert.BACK, alarm.connected())
    }

    @Test
    fun aResetNeverAlarms() {
        val alarm = LinkAlarm(graceMillis = 60_000)
        alarm.lost(now = 0)
        alarm.reset()
        assertNull(alarm.check(now = 3_600_000))
        assertNull(alarm.connected())
    }
}
