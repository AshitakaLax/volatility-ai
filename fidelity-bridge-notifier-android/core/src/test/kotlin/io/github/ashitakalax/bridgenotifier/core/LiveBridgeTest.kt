package io.github.ashitakalax.bridgenotifier.core

import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test

/**
 * Against a real bridge, when asked: set BRIDGE_NOTIFY_URL (e.g.
 * ws://192.168.1.10:8766/notifications) and BRIDGE_NOTIFY_KEY, then
 * `./gradlew -p core test --tests '*LiveBridgeTest'`. Connects, asks for a
 * test notification, and checks it arrives. Skipped otherwise.
 */
class LiveBridgeTest {
    @Test
    fun aRealBridgeAnswersATestRequest() {
        val url = System.getenv("BRIDGE_NOTIFY_URL")
        val key = System.getenv("BRIDGE_NOTIFY_KEY")
        assumeTrue("BRIDGE_NOTIFY_URL and BRIDGE_NOTIFY_KEY are not set", url != null && key != null)
        val recorder = Recorder()
        val client = BridgeClient(ClientSettings(BridgeAddress.parse(url!!)!!, key!!, "LiveBridgeTest"), recorder, MemoryPositionStore())
        try {
            client.start()
            val connected = recorder.awaitLink<BridgeClient.Link.Connected>()
            println("connected: stream ${connected.hello.stream}, events ${connected.hello.events}")
            println("status: ${connected.hello.status}")
            client.requestTest()
            while (true) {
                val (notification, _) = recorder.nextNotification()
                println("notification: ${notification.kind}: ${notification.title} -- ${notification.body}")
                if (notification.isTest) break
            }
            assertTrue(true)
        } finally {
            client.stop()
        }
    }
}
