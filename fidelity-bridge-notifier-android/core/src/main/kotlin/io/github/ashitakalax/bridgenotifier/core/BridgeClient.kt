package io.github.ashitakalax.bridgenotifier.core

import java.net.ConnectException
import java.net.NoRouteToHostException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.security.SecureRandom
import java.util.concurrent.Executors
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

data class ClientSettings(
    /** ws:// or wss:// URL of the listener; see [BridgeAddress.parse]. */
    val url: String,
    val apiKey: String,
    val clientName: String = "Fidelity Bridge Notifier",
    val clientVersion: String = "",
)

fun defaultHttpClient(): OkHttpClient = OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)
    // A notification can be hours apart: liveness is the pings' job.
    .readTimeout(0, TimeUnit.MILLISECONDS)
    .pingInterval(30, TimeUnit.SECONDS)
    .build()

/**
 * The app's connection to the bridge's notification listener: the
 * handshake, the sealed channel, catching up on what was missed, and
 * reconnecting -- with backoff after a failure, shortly after a goodbye (the
 * bridge restarting), and not at all after the bridge refused the key.
 *
 * Everything happens on one thread, [executor]'s, and so does every call to
 * [Listener]: a caller on Android hands each to the main thread itself.
 * One client connects once; after [stop], make a new one.
 */
class BridgeClient(
    private val settings: ClientSettings,
    private val listener: Listener,
    private val positions: PositionStore,
    private val http: OkHttpClient = defaultHttpClient(),
    private val executor: ScheduledExecutorService = Executors.newSingleThreadScheduledExecutor { task ->
        Thread(task, "bridge-client").apply { isDaemon = true }
    },
    private val backoff: Backoff = Backoff(),
    private val random: SecureRandom = SecureRandom(),
    private val handshakeTimeoutMillis: Long = 15_000,
    // The bridge is always on: a goodbye is a restart, back in seconds.
    private val goodbyeRetryMillis: Long = 5_000,
) {
    sealed interface Link {
        data object Idle : Link
        data object Connecting : Link
        data class Connected(val hello: Hello) : Link

        /** Not connected; trying again in [retryInMillis]. [deliberate]: the bridge said goodbye -- it is restarting. */
        data class Waiting(val retryInMillis: Long, val reason: String, val deliberate: Boolean) : Link

        /** Not connected, and not trying again until the settings change: the key was refused. */
        data class Refused(val reason: String) : Link
        data object Stopped : Link
    }

    interface Listener {
        fun onLink(link: Link) {}

        /**
         * [fresh]: news to this app -- as it happened, or missed while it was
         * away. Replays sent to an app that had never connected before are not
         * fresh: history to list, not to announce.
         */
        fun onNotification(notification: Notification, fresh: Boolean) {}
        fun onStatus(status: BridgeStatus) {}
    }

    private var attempt: Attempt? = null
    private var retry: ScheduledFuture<*>? = null
    private var started = false
    private var stopped = false

    fun start() = post {
        if (!started && !stopped) {
            started = true
            connect()
        }
    }

    /** Stop for good: close the connection and never try again. */
    fun stop() {
        post {
            stopped = true
            retry?.cancel(false)
            attempt?.socket?.close(1000, "the app stopped watching")
            attempt = null
            listener.onLink(Link.Stopped)
        }
        executor.shutdown()
    }

    /** Skip the rest of a wait -- the network just came back, say. */
    fun reconnectNow() = post {
        if (!started || stopped || attempt != null || retry == null) return@post
        retry?.cancel(false)
        retry = null
        connect()
    }

    /** Ask the bridge for a test notification; it arrives like any other. */
    fun requestTest() = post {
        attempt?.takeIf { it.ready }?.sendSealed(buildJsonObject { put("type", "test") })
    }

    private fun post(block: () -> Unit) {
        try {
            executor.execute(block)
        } catch (_: RejectedExecutionException) {
            // Stopped: nothing is listening any more.
        }
    }

    private fun connect() {
        val request = try {
            Request.Builder().url(settings.url).build()
        } catch (_: IllegalArgumentException) {
            listener.onLink(Link.Refused("${settings.url} is not a ws:// or wss:// address"))
            return
        }
        val next = Attempt(since = positions.load())
        attempt = next
        listener.onLink(Link.Connecting)
        next.socket = http.newWebSocket(request, next)
        executor.schedule(
            { if (attempt === next && !next.ready) next.fail("no answer from the bridge") },
            handshakeTimeoutMillis,
            TimeUnit.MILLISECONDS,
        )
    }

    private fun ended(ending: Attempt, reason: String) {
        if (attempt !== ending) return
        attempt = null
        if (stopped) return
        val goodbye = ending.goodbye
        val delay = if (goodbye != null) maxOf(goodbyeRetryMillis, backoff.next()) else backoff.next()
        listener.onLink(Link.Waiting(delay, goodbye ?: reason, deliberate = goodbye != null))
        retry = executor.schedule(
            {
                retry = null
                if (!stopped && attempt == null) connect()
            },
            delay,
            TimeUnit.MILLISECONDS,
        )
    }

    private enum class Stage { CHALLENGE, WELCOME, HELLO, READY, DONE }

    /** One connection, from the challenge to its end. */
    private inner class Attempt(val since: Position?) : WebSocketListener() {
        var socket: WebSocket? = null
        var goodbye: String? = null
            private set
        private var stage = Stage.CHALLENGE
        private var bridgeNonce = ""
        private var appNonce = ""
        private var channel: Channel? = null

        val ready: Boolean get() = stage == Stage.READY

        override fun onMessage(webSocket: WebSocket, text: String) = post {
            if (attempt === this) handle(text)
        }

        override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
            webSocket.close(1000, null)
            post { ended(this, closedReason(code, reason)) }
        }

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) = post {
            ended(this, closedReason(code, reason))
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) = post {
            ended(this, failureReason(t, response))
        }

        fun sendSealed(message: JsonObject) {
            val sealed = channel?.seal(message) ?: return
            socket?.send(sealed)
        }

        fun fail(reason: String) {
            stage = Stage.DONE
            socket?.cancel()
            ended(this, reason)
        }

        private fun refuse(reason: String) {
            stage = Stage.DONE
            socket?.close(1000, null)
            attempt = null
            listener.onLink(Link.Refused(reason))
        }

        private fun handle(text: String) {
            when (stage) {
                Stage.CHALLENGE -> onChallenge(text)
                Stage.WELCOME -> onWelcome(text)
                Stage.HELLO, Stage.READY -> onSealed(text)
                Stage.DONE -> Unit
            }
        }

        private fun onChallenge(text: String) {
            val challenge = parseObject(text)
            val nonce = challenge?.string("nonce")
            if (challenge?.string("type") != "challenge" ||
                challenge.string("protocol") != NotifyProtocol.PROTOCOL ||
                nonce == null || !NotifyProtocol.isNonce(nonce)
            ) {
                return refuse(
                    "Nothing at this address speaks ${NotifyProtocol.PROTOCOL}. Is it the " +
                        "bridge's notification port (8766 by default), not the extension's?",
                )
            }
            bridgeNonce = nonce
            appNonce = NotifyProtocol.newNonce(random)
            val auth = buildJsonObject {
                put("type", "auth")
                put("protocol", NotifyProtocol.PROTOCOL)
                put("nonce", appNonce)
                put("proof", NotifyProtocol.appProof(settings.apiKey, bridgeNonce, appNonce))
                if (since == null) {
                    put("since", JsonNull)
                } else {
                    put(
                        "since",
                        buildJsonObject {
                            put("stream", since.stream)
                            put("id", since.id)
                        },
                    )
                }
                put(
                    "client",
                    buildJsonObject {
                        put("name", settings.clientName)
                        put("version", settings.clientVersion)
                    },
                )
            }
            stage = Stage.WELCOME
            socket?.send(auth.toString())
        }

        private fun onWelcome(text: String) {
            val reply = parseObject(text)
            when (reply?.string("type")) {
                "welcome" -> {
                    val expected = NotifyProtocol.bridgeProof(settings.apiKey, bridgeNonce, appNonce)
                    if (!NotifyProtocol.proofsMatch(expected, reply.string("proof"))) {
                        return refuse("The bridge at this address could not prove it holds the key.")
                    }
                    channel = Channel(NotifyProtocol.sessionKey(settings.apiKey, bridgeNonce, appNonce))
                    stage = Stage.HELLO
                }
                "denied" -> when (val reason = reply.string("reason")) {
                    "bad_proof" -> refuse(
                        "The bridge refused the API key. It must be the bridge's " +
                            "FIDELITY_BRIDGE_NOTIFY_KEY (keygen --notify), not the extension's.",
                    )
                    "too_many_apps" -> fail("the bridge has as many apps connected as it allows")
                    "stopping" -> fail("the bridge is stopping")
                    else -> fail("the bridge refused the connection (${reason ?: "no reason"})")
                }
                else -> fail("the bridge answered the handshake with something else")
            }
        }

        private fun onSealed(text: String) {
            val message = try {
                channel!!.open(text)
            } catch (e: ProtocolException) {
                return fail("a message from the bridge failed its check: ${e.message}")
            }
            when (val parsed = BridgeMessage.parse(message)) {
                is BridgeMessage.HelloMessage -> if (stage == Stage.HELLO) {
                    stage = Stage.READY
                    backoff.reset()
                    listener.onLink(Link.Connected(parsed.hello))
                    listener.onStatus(parsed.hello.status)
                }
                is BridgeMessage.NotificationMessage -> if (stage == Stage.READY) deliver(parsed)
                is BridgeMessage.StatusMessage -> if (stage == Stage.READY) listener.onStatus(parsed.status)
                is BridgeMessage.Goodbye -> goodbye = parsed.reason
                BridgeMessage.Unknown -> Unit
            }
        }

        private fun deliver(message: BridgeMessage.NotificationMessage) {
            val notification = message.notification
            if (notification.isTest) return listener.onNotification(notification, fresh = true)
            val last = positions.load()
            if (last != null && last.stream == notification.stream && notification.id <= last.id) {
                return // already seen
            }
            positions.save(Position(notification.stream, notification.id))
            listener.onNotification(notification, fresh = !message.replay || since != null)
        }
    }

    private fun closedReason(code: Int, reason: String): String =
        "the bridge closed the connection ($code${if (reason.isNotEmpty()) ": $reason" else ""})"

    private fun failureReason(t: Throwable, response: Response?): String = when {
        response?.code == 403 ->
            "the bridge refused this device's address (403): add it to the bridge's allowed clients"
        response?.code == 404 -> "nothing listens at that path (404): it should end in ${NotifyProtocol.PATH}"
        response != null -> "the bridge answered HTTP ${response.code}"
        t is UnknownHostException -> "unknown host"
        t is ConnectException -> "could not reach the bridge (is it running?)"
        t is NoRouteToHostException -> "no route to the bridge (are you on its network?)"
        t is SocketTimeoutException -> "timed out reaching the bridge"
        else -> t.message ?: t.javaClass.simpleName
    }
}
