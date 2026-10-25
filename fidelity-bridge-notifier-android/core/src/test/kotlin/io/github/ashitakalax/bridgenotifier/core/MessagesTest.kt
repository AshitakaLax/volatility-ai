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
    fun theBridgeHostsReadinessIsRead() {
        val status = (
            BridgeMessage.parse(
                obj(
                    """{"type":"status","status":{
                    "extension":{"connected":true,"fidelity":"signed_out","disconnectCode":null},
                    "engine":null,
                    "bridge":{"ready":false,"blocking":"fidelity",
                      "summary":"Fidelity tab: Fidelity signed you out",
                      "fix":"sign in to Fidelity again in that browser",
                      "items":[{"id":"bridge","label":"Bridge","state":"ok","detail":"listening","fix":null},
                               {"id":"fidelity","label":"Fidelity tab","state":"fail",
                                "detail":"Fidelity signed you out","fix":"sign in again"},
                               {"label":"no id: skipped"}],
                      "listening":true,"mode":"live","symbol":"RSP",
                      "attached":{"process":"loop","since":"2026-10-26T13:31:00+00:00"},
                      "lastCheck":{"at":"2026-10-26T13:00:00+00:00","ok":false,"detail":"signed out","by":"30 min before the open"},
                      "sessionOpen":true,"nextOpen":"2026-10-27T13:30:00+00:00"}}}""",
                ),
            ) as BridgeMessage.StatusMessage
            ).status
        assertEquals("signed_out", status.extension!!.fidelity)
        assertNull(status.engine)
        val host = status.bridge!!
        assertFalse(host.ready)
        assertEquals("fidelity", host.blocking)
        assertEquals(listOf("bridge", "fidelity"), host.items.map { it.id })
        assertEquals("fail", host.items[1].state)
        assertEquals("loop", host.attached)
        assertEquals(false, host.lastCheck!!.ok)
        assertTrue(host.sessionOpen)
    }

    @Test
    fun aBridgeWithoutAHostHasNoReadiness() {
        val status = BridgeStatus.parse(obj("""{"extension":{"connected":true}}"""))
        assertNull(status.bridge)
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
