package io.github.ashitakalax.bridgenotifier.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SettingsTest {
    @Test
    fun anAddressIsCompletedWithTheDefaultPortAndPath() {
        assertEquals("ws://192.168.1.10:8766/notifications", BridgeAddress.parse("192.168.1.10"))
        assertEquals("ws://192.168.1.10:9000/notifications", BridgeAddress.parse(" 192.168.1.10:9000 "))
        assertEquals("ws://server.lan:8766/notifications", BridgeAddress.parse("server.lan"))
        assertEquals("wss://bridge.example:443/notifications", BridgeAddress.parse("wss://bridge.example:443"))
        assertEquals("ws://h:1/custom", BridgeAddress.parse("ws://h:1/custom"))
        assertEquals("ws://[fd00::5]:8766/notifications", BridgeAddress.parse("[fd00::5]"))
    }

    @Test
    fun anythingElseIsNotAnAddress() {
        for (bad in listOf("", "  ", "http://h", "ws://", "ws://user:pw@h", "ws://h/x?q=1", "a b")) {
            assertNull(bad, BridgeAddress.parse(bad))
        }
    }

    @Test
    fun plainTextIsSaidSo() {
        assertTrue(BridgeAddress.isPlainText("ws://h:1/notifications"))
        assertFalse(BridgeAddress.isPlainText("wss://h:1/notifications"))
    }

    @Test
    fun keysFollowTheBridgesAlphabet() {
        assertTrue(ApiKeys.looksValid("a".repeat(32)))
        assertTrue(ApiKeys.looksValid("Ab0._~+/=-".repeat(4)))
        assertFalse(ApiKeys.looksValid("a".repeat(31)))
        assertFalse(ApiKeys.looksValid("a".repeat(257)))
        assertFalse(ApiKeys.looksValid("a".repeat(31) + " "))
    }
}
