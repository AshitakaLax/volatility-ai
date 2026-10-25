package io.github.ashitakalax.bridgenotifier.core

import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer

const val TEST_KEY = "notify-test-key-9876543210zyxwvutsrqponmlkjihg"

/**
 * The bridge's half of the protocol, for the client's tests: what
 * fidelity_gateway/bridge/notify_server.py does, on a MockWebServer. Each
 * [accept] lets one connection in and runs [onReady] once it is sealed.
 */
class FakeBridge(private val apiKey: String = TEST_KEY) {
    val server = MockWebServer().apply { start() }
    val url: String = server.url(NotifyProtocol.PATH).toString().replaceFirst("http", "ws")
    val auths = LinkedBlockingQueue<JsonObject>()
    val received = LinkedBlockingQueue<JsonObject>()

    inner class Session(val socket: WebSocket, private val channel: Channel) {
        fun send(message: JsonObject) {
            socket.send(channel.seal(message))
        }

        fun sendRaw(text: String) {
            socket.send(text)
        }

        fun seal(message: JsonObject): String = channel.seal(message)
    }

    fun accept(
        protocol: String = NotifyProtocol.PROTOCOL,
        deny: String? = null,
        forgeProof: Boolean = false,
        onReady: (Session) -> Unit = { it.send(hello()) },
    ) {
        server.enqueue(
            MockResponse().withWebSocketUpgrade(
                object : WebSocketListener() {
                    private val bridgeNonce = NotifyProtocol.newNonce()
                    private var channel: Channel? = null

                    override fun onOpen(webSocket: WebSocket, response: Response) {
                        webSocket.send(
                            buildJsonObject {
                                put("type", "challenge")
                                put("protocol", protocol)
                                put("nonce", bridgeNonce)
                            }.toString(),
                        )
                    }

                    override fun onMessage(webSocket: WebSocket, text: String) {
                        channel?.let {
                            received.add(it.open(text))
                            return
                        }
                        val auth = parseObject(text)!!
                        auths.add(auth)
                        val appNonce = auth.string("nonce")!!
                        val expected = NotifyProtocol.appProof(apiKey, bridgeNonce, appNonce)
                        val reason = deny ?: if (NotifyProtocol.proofsMatch(expected, auth.string("proof"))) null else "bad_proof"
                        if (reason != null) {
                            webSocket.send(buildJsonObject { put("type", "denied"); put("reason", reason) }.toString())
                            webSocket.close(1008, "authentication failed")
                            return
                        }
                        val proof = if (forgeProof) "0".repeat(64) else NotifyProtocol.bridgeProof(apiKey, bridgeNonce, appNonce)
                        webSocket.send(buildJsonObject { put("type", "welcome"); put("proof", proof) }.toString())
                        val key = NotifyProtocol.sessionKey(apiKey, bridgeNonce, appNonce)
                        val sealed = Channel(key, sender = "bridge", peer = "app").also { channel = it }
                        onReady(Session(webSocket, sealed))
                    }

                    override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                        webSocket.close(1000, null)
                    }
                },
            ),
        )
    }

    fun close() = server.shutdown()

    companion object {
        fun hello(stream: String = "s1") = buildJsonObject {
            put("type", "hello")
            put("protocol", NotifyProtocol.PROTOCOL)
            put("stream", stream)
            put("events", kotlinx.serialization.json.JsonArray(listOf(kotlinx.serialization.json.JsonPrimitive("buy"))))
            put("status", buildJsonObject {
                put("extension", buildJsonObject { put("connected", true); put("version", "1.4.0") })
            })
        }

        fun notification(id: Long, stream: String = "s1", kind: String = "buy", replay: Boolean = false) = buildJsonObject {
            put("type", "notification")
            if (replay) put("replay", true)
            put("notification", buildJsonObject {
                put("id", id)
                put("stream", stream)
                put("kind", kind)
                put("severity", "info")
                put("title", "n$id")
                put("body", "")
                put("at", "2026-10-24T14:00:00+00:00")
                put("data", buildJsonObject {})
            })
        }
    }
}

/** What a client told its listener, to wait on. */
class Recorder : BridgeClient.Listener {
    val links = LinkedBlockingQueue<BridgeClient.Link>()
    val notifications = LinkedBlockingQueue<Pair<Notification, Boolean>>()
    val statuses = LinkedBlockingQueue<BridgeStatus>()

    override fun onLink(link: BridgeClient.Link) {
        links.add(link)
    }

    override fun onNotification(notification: Notification, fresh: Boolean) {
        notifications.add(notification to fresh)
    }

    override fun onStatus(status: BridgeStatus) {
        statuses.add(status)
    }

    inline fun <reified T : BridgeClient.Link> awaitLink(): T {
        while (true) {
            val link = links.poll(5, TimeUnit.SECONDS) ?: throw AssertionError("no ${T::class.simpleName} link")
            if (link is T) return link
        }
    }

    fun nextNotification(): Pair<Notification, Boolean> =
        notifications.poll(5, TimeUnit.SECONDS) ?: throw AssertionError("no notification")
}
