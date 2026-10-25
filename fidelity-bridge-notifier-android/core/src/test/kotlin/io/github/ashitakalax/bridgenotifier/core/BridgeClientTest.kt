package io.github.ashitakalax.bridgenotifier.core

import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlinx.serialization.json.put
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BridgeClientTest {
    private val bridge = FakeBridge()
    private val recorder = Recorder()
    private var client: BridgeClient? = null

    @After
    fun tearDown() {
        client?.stop()
        bridge.close()
    }

    private fun client(positions: PositionStore = MemoryPositionStore(), key: String = TEST_KEY): BridgeClient =
        BridgeClient(
            ClientSettings(bridge.url, key, clientName = "test", clientVersion = "0.0.1"),
            recorder,
            positions,
            backoff = Backoff(initialMillis = 20, maxMillis = 40),
            goodbyeRetryMillis = 50,
        ).also {
            client = it
            it.start()
        }

    @Test
    fun itProvesTheKeyAndHearsNotificationsAsTheyHappen() {
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            session.send(FakeBridge.notification(1))
        }
        val positions = MemoryPositionStore()
        client(positions)
        val connected = recorder.awaitLink<BridgeClient.Link.Connected>()
        assertEquals("s1", connected.hello.stream)
        assertEquals("1.4.0", recorder.statuses.poll(5, TimeUnit.SECONDS)!!.extension!!.version)
        val (notification, fresh) = recorder.nextNotification()
        assertEquals("n1", notification.title)
        assertTrue(fresh)
        assertEquals(Position("s1", 1), positions.load())
        val auth = bridge.auths.poll(5, TimeUnit.SECONDS)!!
        assertEquals("test", auth["client"]!!.jsonObject["name"]!!.jsonPrimitive.content)
        assertFalse("the key never crosses the wire", auth.toString().contains(TEST_KEY))
    }

    @Test
    fun itSaysWhereItLeftOffAndHearsOnlyWhatItMissed() {
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            session.send(FakeBridge.notification(4, replay = true)) // already seen: dropped
            session.send(FakeBridge.notification(5, replay = true))
        }
        client(MemoryPositionStore(Position("s1", 4)))
        val since = bridge.auths.poll(5, TimeUnit.SECONDS)!!["since"]!!.jsonObject
        assertEquals("s1", since["stream"]!!.jsonPrimitive.content)
        assertEquals(4L, since["id"]!!.jsonPrimitive.long)
        val (notification, fresh) = recorder.nextNotification()
        assertEquals(5L, notification.id)
        assertTrue("missed while away: news", fresh)
    }

    @Test
    fun onAFirstEverConnectionTheReplaysAreHistoryNotNews() {
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            session.send(FakeBridge.notification(1, replay = true))
            session.send(FakeBridge.notification(2))
        }
        client()
        assertEquals(1L to false, recorder.nextNotification().let { it.first.id to it.second })
        assertEquals(2L to true, recorder.nextNotification().let { it.first.id to it.second })
    }

    @Test
    fun aRefusedKeyIsSaidAndNotRetried() {
        bridge.accept()
        bridge.accept() // would be used by a retry
        client(key = "wrong-key-0123456789abcdefghijklmnopqrstuvw")
        val refused = recorder.awaitLink<BridgeClient.Link.Refused>()
        assertTrue(refused.reason, refused.reason.contains("FIDELITY_BRIDGE_NOTIFY_KEY"))
        assertNull(recorder.links.poll(300, TimeUnit.MILLISECONDS))
        assertEquals(1, bridge.server.requestCount)
    }

    @Test
    fun aBridgeThatCannotProveTheKeyIsNotBelieved() {
        bridge.accept(forgeProof = true)
        client()
        assertTrue(recorder.awaitLink<BridgeClient.Link.Refused>().reason.contains("could not prove"))
    }

    @Test
    fun theExtensionsSocketIsNotMistakenForTheListener() {
        bridge.accept(protocol = "fidelity-bridge/v1")
        client()
        assertTrue(recorder.awaitLink<BridgeClient.Link.Refused>().reason.contains("8766"))
    }

    @Test
    fun aForgedMessageDropsTheConnectionAndItReconnects() {
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            val sealed = session.seal(FakeBridge.notification(1))
            session.sendRaw(sealed.replace("n1", "n9"))
        }
        bridge.accept { session -> session.send(FakeBridge.hello()) }
        client()
        recorder.awaitLink<BridgeClient.Link.Connected>()
        val waiting = recorder.awaitLink<BridgeClient.Link.Waiting>()
        assertTrue(waiting.reason, waiting.reason.contains("failed its check"))
        assertFalse(waiting.deliberate)
        recorder.awaitLink<BridgeClient.Link.Connected>()
        assertTrue("nothing forged was delivered", recorder.notifications.isEmpty())
    }

    @Test
    fun aGoodbyeIsARestartAndItComesBackShortly() {
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            session.send(buildJsonObject { put("type", "goodbye"); put("reason", "the session ended") })
            session.socket.close(1001, "the bridge is stopping")
        }
        bridge.accept { session -> session.send(FakeBridge.hello()) }
        client()
        recorder.awaitLink<BridgeClient.Link.Connected>()
        val waiting = recorder.awaitLink<BridgeClient.Link.Waiting>()
        assertTrue(waiting.deliberate)
        assertEquals("the session ended", waiting.reason)
        recorder.awaitLink<BridgeClient.Link.Connected>()
    }

    @Test
    fun aTestRequestIsSealedAndItsAnswerIsNotRemembered() {
        val positions = MemoryPositionStore()
        bridge.accept { session ->
            session.send(FakeBridge.hello())
            Thread {
                val request = bridge.received.poll(5, TimeUnit.SECONDS)
                if (request?.get("type")?.jsonPrimitive?.content == "test") {
                    session.send(FakeBridge.notification(0, kind = EventKind.TEST))
                }
            }.start()
        }
        val c = client(positions)
        recorder.awaitLink<BridgeClient.Link.Connected>()
        c.requestTest()
        val (notification, fresh) = recorder.nextNotification()
        assertTrue(notification.isTest && fresh)
        assertNull(positions.load())
    }

    @Test
    fun stoppingClosesAndNeverRetries() {
        bridge.accept { session -> session.send(FakeBridge.hello()) }
        bridge.accept { session -> session.send(FakeBridge.hello()) }
        val c = client()
        recorder.awaitLink<BridgeClient.Link.Connected>()
        c.stop()
        recorder.awaitLink<BridgeClient.Link.Stopped>()
        c.reconnectNow()
        assertNull(recorder.links.poll(300, TimeUnit.MILLISECONDS))
        assertEquals(1, bridge.server.requestCount)
    }

    @Test
    fun anUnreachableBridgeIsRetriedWithAReason() {
        bridge.close()
        client()
        val waiting = recorder.awaitLink<BridgeClient.Link.Waiting>()
        assertTrue(waiting.reason, waiting.reason.contains("could not reach"))
    }
}
