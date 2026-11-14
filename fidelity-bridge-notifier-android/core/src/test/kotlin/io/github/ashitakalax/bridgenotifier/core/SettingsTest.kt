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

    @Test
    fun aPastedKeyLosesTheEnvLinesNameItsQuotesAndItsSpaces() {
        val key = "Ab0._~+/-".repeat(4) + "=="
        for (pasted in listOf(
            key,
            "  $key\n",
            "FIDELITY_BRIDGE_NOTIFY_KEY=$key",
            "FIDELITY_BRIDGE_NOTIFY_KEY = \"$key\"",
            "export FIDELITY_BRIDGE_NOTIFY_KEY='$key'",
            "\"$key\"",
        )) {
            assertEquals(pasted, key, ApiKeys.clean(pasted))
        }
        // The whole line would have passed for a key.
        assertTrue(ApiKeys.looksValid("FIDELITY_BRIDGE_NOTIFY_KEY=$key"))
        assertEquals("", ApiKeys.clean("   "))
    }

    @Test
    fun anAddressOnlyItsOwnNetworkReachesIsLocal() {
        for (local in listOf(
            "192.168.1.10", "10.0.0.5", "172.16.4.1", "172.31.0.9", "100.101.102.103", "169.254.1.1",
            "127.0.0.1", "server.lan", "nas.local", "homeserver", "[fd00::5]", "[fe80::1]",
        )) {
            assertTrue(local, BridgeAddress.isLocalNetwork(BridgeAddress.parse(local)!!))
        }
        for (public in listOf("8.8.8.8", "172.32.0.1", "100.128.0.1", "bridge.example.com", "wss://bridge.example:443", "[2001:db8::1]")) {
            assertFalse(public, BridgeAddress.isLocalNetwork(BridgeAddress.parse(public)!!))
        }
        assertFalse(BridgeAddress.isLocalNetwork(""))
    }
}
