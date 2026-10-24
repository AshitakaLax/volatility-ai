package io.github.ashitakalax.bridgenotifier.core

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.longOrNull

/** What the bridge can tell the app: its notifications' kinds. */
object EventKind {
    const val BUY = "buy"
    const val SELL = "sell"
    const val ORDER_UPDATE = "order_update"
    const val ORDER_PROBLEM = "order_problem"
    const val CONNECTED = "connected"
    const val DISCONNECTED = "disconnected"
    const val TRADING_SWITCH = "trading_switch"
    const val ENGINE = "engine"

    /** A test the app asked for: never numbered, never kept by the bridge. */
    const val TEST = "test"

    /** Every kind the bridge sends, in its order (notifications.py's EVENT_KINDS). */
    val ALL = listOf(BUY, SELL, ORDER_UPDATE, ORDER_PROBLEM, CONNECTED, DISCONNECTED, TRADING_SWITCH, ENGINE)

    fun label(kind: String): String = when (kind) {
        BUY -> "Buys filled"
        SELL -> "Sells filled"
        ORDER_UPDATE -> "Orders accepted, cancelled or expired"
        ORDER_PROBLEM -> "Orders rejected, refused or unknown"
        CONNECTED -> "Extension connected or reconnected"
        DISCONNECTED -> "Extension disconnected"
        TRADING_SWITCH -> "\"Allow trading\" switched on or off"
        ENGINE -> "Engine started, paused, halted or stopped"
        TEST -> "Test notifications"
        else -> kind
    }
}

enum class Severity {
    INFO, WARNING, CRITICAL;

    companion object {
        fun parse(text: String?): Severity = when (text) {
            "warning" -> WARNING
            "critical" -> CRITICAL
            else -> INFO
        }
    }
}

/** One thing that happened, as the bridge told it. */
data class Notification(
    val id: Long,
    val stream: String,
    val kind: String,
    val severity: Severity,
    val title: String,
    val body: String,
    /** ISO-8601, UTC. */
    val at: String,
    val data: JsonObject,
) {
    val isTest: Boolean get() = kind == EventKind.TEST

    companion object {
        fun parse(obj: JsonObject?): Notification? {
            if (obj == null) return null
            val id = obj.long("id") ?: return null
            val stream = obj.string("stream") ?: return null
            val kind = obj.string("kind") ?: return null
            val title = obj.string("title") ?: return null
            if (id < 0) return null
            return Notification(
                id = id,
                stream = stream,
                kind = kind,
                severity = Severity.parse(obj.string("severity")),
                title = title,
                body = obj.string("body").orEmpty(),
                at = obj.string("at").orEmpty(),
                data = obj["data"] as? JsonObject ?: JsonObject(emptyMap()),
            )
        }
    }
}

/** The extension's side of the bridge. */
data class ExtensionStatus(
    val connected: Boolean,
    val since: String?,
    val disconnectedAt: String?,
    val version: String?,
    /** What the bridge says to do about the extension's version, if anything. */
    val advice: String?,
    /** Its "Allow trading" switch; null before it has said. */
    val trading: Boolean?,
    val previews: Boolean?,
) {
    companion object {
        fun parse(obj: JsonObject?): ExtensionStatus? = obj?.let {
            ExtensionStatus(
                connected = it.bool("connected") == true,
                since = it.string("since"),
                disconnectedAt = it.string("disconnectedAt"),
                version = it.string("version"),
                advice = it.string("advice"),
                trading = it.bool("trading"),
                previews = it.bool("previews"),
            )
        }
    }
}

/** What the engine last said about itself. */
data class EngineStatus(
    val state: String?,
    val detail: String?,
    val mode: String?,
    val symbol: String?,
    val lastTickAt: String?,
    val updatedAt: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): EngineStatus? = obj?.let {
            EngineStatus(
                state = it.string("state"),
                detail = it.string("detail"),
                mode = it.string("mode"),
                symbol = it.string("symbol"),
                lastTickAt = it.string("lastTickAt"),
                updatedAt = it.string("updatedAt"),
            )
        }
    }
}

data class BridgeStatus(val extension: ExtensionStatus?, val engine: EngineStatus?) {
    companion object {
        val UNKNOWN = BridgeStatus(null, null)

        fun parse(obj: JsonObject?): BridgeStatus = BridgeStatus(
            extension = ExtensionStatus.parse(obj?.get("extension") as? JsonObject),
            engine = EngineStatus.parse(obj?.get("engine") as? JsonObject),
        )
    }
}

/** The bridge's first sealed message: this run's stream, what it sends, how things are. */
data class Hello(val stream: String, val events: List<String>, val status: BridgeStatus)

/** A sealed message from the bridge, after the handshake. */
sealed interface BridgeMessage {
    data class HelloMessage(val hello: Hello) : BridgeMessage

    /** [replay]: sent because the app missed it, not as it happened. */
    data class NotificationMessage(val notification: Notification, val replay: Boolean) : BridgeMessage

    data class StatusMessage(val status: BridgeStatus) : BridgeMessage

    /** The bridge is stopping on purpose: the engine's session ended. */
    data class Goodbye(val reason: String) : BridgeMessage

    /** Something this version does not know: ignored, never an error. */
    data object Unknown : BridgeMessage

    companion object {
        fun parse(obj: JsonObject): BridgeMessage = when (obj.string("type")) {
            "hello" -> obj.string("stream")?.let { stream ->
                HelloMessage(
                    Hello(
                        stream = stream,
                        events = (obj["events"] as? JsonArray).orEmpty()
                            .mapNotNull { (it as? JsonPrimitive)?.takeIf { p -> p.isString }?.content },
                        status = BridgeStatus.parse(obj["status"] as? JsonObject),
                    ),
                )
            } ?: Unknown
            "notification" -> Notification.parse(obj["notification"] as? JsonObject)
                ?.let { NotificationMessage(it, replay = obj.bool("replay") == true) } ?: Unknown
            "status" -> StatusMessage(BridgeStatus.parse(obj["status"] as? JsonObject))
            "goodbye" -> Goodbye(obj.string("reason") ?: "the bridge is stopping")
            else -> Unknown
        }
    }
}

internal fun JsonObject.string(name: String): String? =
    (this[name] as? JsonPrimitive)?.takeIf { it.isString }?.content

internal fun JsonObject.long(name: String): Long? =
    (this[name] as? JsonPrimitive)?.takeUnless { it.isString }?.longOrNull

internal fun JsonObject.bool(name: String): Boolean? =
    (this[name] as? JsonPrimitive)?.takeUnless { it.isString }?.booleanOrNull
