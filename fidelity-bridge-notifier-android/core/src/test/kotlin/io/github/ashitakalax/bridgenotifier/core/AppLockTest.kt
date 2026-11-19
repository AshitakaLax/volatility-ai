package io.github.ashitakalax.bridgenotifier.core

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AppLockTest {
    @Test
    fun itAsksWhenTheAppOpensAndUntilTheOwnerProvesIt() {
        val lock = AppLock(awayMillis = 60_000)
        assertTrue(lock.cameBack(0))
        // Cancelled, or sent to another app mid-prompt: still locked.
        lock.left(5_000)
        assertTrue(lock.cameBack(6_000))
        lock.unlocked()
        assertFalse(lock.cameBack(7_000))
    }

    @Test
    fun aMomentAwayIsNotAskedForButAMinuteIs() {
        val lock = AppLock(awayMillis = 60_000)
        lock.unlocked()
        lock.left(10_000)
        assertFalse("back after 59 s", lock.cameBack(69_000))
        lock.left(100_000)
        assertTrue("back after 60 s", lock.cameBack(160_000))
        // And it keeps asking until it is answered.
        assertTrue(lock.cameBack(161_000))
    }

    @Test
    fun comingBackWithoutHavingLeftAsksNothingNew() {
        val lock = AppLock(awayMillis = 60_000)
        lock.unlocked()
        // A screen turned: a new screen comes into sight, nothing went away.
        assertFalse(lock.cameBack(1_000_000))
    }
}
