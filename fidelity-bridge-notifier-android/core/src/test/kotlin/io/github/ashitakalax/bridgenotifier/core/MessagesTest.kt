package io.github.ashitakalax.bridgenotifier.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class MessagesTest {
    private fun obj(text: String): JsonObject = Json.parseToJsonElement(text).jsonObject

    @Test
    fun aNotificationAsTheBridgeSendsIt() {
        val message = BridgeMessage.parse(
            obj(
                """{"type":"notification","notification":{"id":7,"stream":"s1","kind":"sell",
                "severity":"warning","title":"Sold 3 TQQQ","body":"3 at ${'$'}71.20",
                "at":"2026-10-24T14:31:07+00:00","data":{"qty":3}}}""",
            ),
        ) as BridgeMessage.NotificationMessage
        val n = message.notification
        assertFalse(message.replay)
        assertEquals(7L, n.id)
        assertEquals(EventKind.SELL, n.kind)
        assertEquals(Severity.WARNING, n.severity)
        assertEquals("Sold 3 TQQQ", n.title)
        assertEquals("3", n.data["qty"].toString())
    }

    @Test
    fun aReplayIsMarked() {
        val message = BridgeMessage.parse(
            obj("""{"type":"notification","replay":true,"notification":{"id":1,"stream":"s","kind":"buy","title":"t"}}"""),
        )
        assertTrue((message as BridgeMessage.NotificationMessage).replay)
        assertEquals(Severity.INFO, message.notification.severity)
    }

    @Test
    fun aNotificationMissingWhatIdentifiesItIsNotOne() {
        assertNull(Notification.parse(obj("""{"stream":"s","kind":"buy","title":"t"}""")))
        assertNull(Notification.parse(obj("""{"id":"1","stream":"s","kind":"buy","title":"t"}""")))
        assertNull(Notification.parse(obj("""{"id":-1,"stream":"s","kind":"buy","title":"t"}""")))
        assertEquals(
            BridgeMessage.Unknown,
            BridgeMessage.parse(obj("""{"type":"notification","notification":{"id":1}}""")),
        )
    }

    @Test
    fun theHelloCarriesTheStreamTheKindsAndTheStatus() {
        val hello = (
            BridgeMessage.parse(
                obj(
                    """{"type":"hello","stream":"abc","events":["buy","sell",3],
                    "status":{"extension":{"connected":true,"version":"1.4.0","trading":false},
                    "engine":{"state":"running","detail":"trading","symbol":"TQQQ"}}}""",
                ),
            ) as BridgeMessage.HelloMessage
            ).hello
        assertEquals("abc", hello.stream)
        assertEquals(listOf("buy", "sell"), hello.events)
        assertEquals(true, hello.status.extension!!.connected)
        assertEquals(false, hello.status.extension!!.trading)
        assertNull(hello.status.extension!!.previews)
        assertEquals("running", hello.status.engine!!.state)
    }

    @Test
    fun aStatusWithNoEngineYet() {
        val status = (BridgeMessage.parse(obj("""{"type":"status","status":{"extension":{"connected":false},"engine":null}}""")) as BridgeMessage.StatusMessage).status
        assertFalse(status.extension!!.connected)
        assertNull(status.engine)
    }

    @Test
    fun goodbyeAndTheUnknown() {
        assertEquals(BridgeMessage.Goodbye("bye"), BridgeMessage.parse(obj("""{"type":"goodbye","reason":"bye"}""")))
        assertEquals(BridgeMessage.Unknown, BridgeMessage.parse(obj("""{"type":"something-new"}""")))
    }

    @Test
    fun everyKindHasALabel() {
        for (kind in EventKind.ALL + EventKind.TEST) assertFalse(EventKind.label(kind) == kind)
    }
}
