package io.github.ashitakalax.bridgenotifier.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlinx.serialization.json.put
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

/**
 * The shared vectors, which the bridge's
 * fidelity_gateway/tests/test_bridge_notify_protocol.py reproduces too: what
 * keeps the two halves of the protocol speaking one language.
 */
class ProtocolVectorsTest {
    private val vectors: JsonObject = Json.parseToJsonElement(
        javaClass.getResource("/vectors/notify-protocol-v1.json")!!.readText(),
    ).jsonObject

    private fun text(name: String) = vectors[name]!!.jsonPrimitive.content

    @Test
    fun theVectorsAreForThisProtocol() {
        assertEquals(NotifyProtocol.PROTOCOL, text("protocol"))
    }

    @Test
    fun theHandshakeReproducesTheVectors() {
        val key = text("apiKey")
        val bridgeNonce = text("bridgeNonce")
        val appNonce = text("appNonce")
        assertEquals(text("appProof"), NotifyProtocol.appProof(key, bridgeNonce, appNonce))
        assertEquals(text("bridgeProof"), NotifyProtocol.bridgeProof(key, bridgeNonce, appNonce))
        assertEquals(text("sessionKey"), NotifyProtocol.sessionKey(key, bridgeNonce, appNonce).toHex())
    }

    @Test
    fun everySealedMessageReproducesTheVectors() {
        val key = NotifyProtocol.sessionKey(text("apiKey"), text("bridgeNonce"), text("appNonce"))
        val messages = vectors["messages"] as JsonArray
        assertTrue("UTF-8 must be pinned", messages.any { m -> m.jsonObject["payload"]!!.jsonPrimitive.content.any { it.code > 127 } })
        for (element in messages) {
            val m = element.jsonObject
            val mac = NotifyProtocol.messageMac(
                key,
                m["sender"]!!.jsonPrimitive.content,
                m["seq"]!!.jsonPrimitive.long,
                m["payload"]!!.jsonPrimitive.content,
            )
            assertEquals(m["mac"]!!.jsonPrimitive.content, mac)
        }
    }

    @Test
    fun theBridgesMessagesOpenAtTheApp() {
        val app = Channel(NotifyProtocol.sessionKey(text("apiKey"), text("bridgeNonce"), text("appNonce")))
        for (element in vectors["messages"] as JsonArray) {
            val m = element.jsonObject
            if (m["sender"]!!.jsonPrimitive.content != "bridge") continue
            val envelope = buildJsonObject {
                put("seq", m["seq"]!!.jsonPrimitive.long)
                put("payload", m["payload"]!!.jsonPrimitive.content)
                put("mac", m["mac"]!!.jsonPrimitive.content)
            }
            assertEquals(Json.parseToJsonElement(m["payload"]!!.jsonPrimitive.content), app.open(envelope.toString()))
        }
    }

    @Test
    fun theProofsAndTheSessionKeyAllDiffer() {
        val args = Triple("k".repeat(40), "a".repeat(64), "b".repeat(64))
        val app = NotifyProtocol.appProof(args.first, args.second, args.third)
        val bridge = NotifyProtocol.bridgeProof(args.first, args.second, args.third)
        assertNotEquals(app, bridge)
        assertNotEquals(app, NotifyProtocol.sessionKey(args.first, args.second, args.third).toHex())
    }

    @Test
    fun aSealedMessageOpensOnlyOnTheOtherSideInOrderAndUntampered() {
        val key = ByteArray(32) { it.toByte() }
        val bridge = Channel(key, sender = "bridge", peer = "app")
        val app = Channel(key)
        val first = bridge.seal(buildJsonObject { put("type", "status") })
        val second = bridge.seal(buildJsonObject { put("type", "goodbye") })
        assertRejected("expected message 1") { app.open(second) }
        assertRejected("integrity") { app.open(first.replace("status", "statuz")) }
        assertRejected("integrity") { Channel(key, sender = "bridge", peer = "app").open(first) }
        assertEquals("status", app.open(first)["type"]!!.jsonPrimitive.content)
        assertRejected("expected message 2") { app.open(first) }
        assertEquals(1L, app.received)
    }

    @Test
    fun noncesAreFreshHex() {
        val a = NotifyProtocol.newNonce()
        assertTrue(NotifyProtocol.isNonce(a))
        assertNotEquals(a, NotifyProtocol.newNonce())
        assertFalse(NotifyProtocol.isNonce("A".repeat(64)))
        assertFalse(NotifyProtocol.isNonce(null))
    }

    private fun assertRejected(containing: String, block: () -> Unit) {
        try {
            block()
            fail("expected a ProtocolException")
        } catch (e: ProtocolException) {
            assertTrue("${e.message} should mention $containing", e.message!!.contains(containing))
        }
    }
}
