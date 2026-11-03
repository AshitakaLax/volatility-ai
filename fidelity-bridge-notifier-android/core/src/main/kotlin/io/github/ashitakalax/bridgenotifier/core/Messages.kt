package io.github.ashitakalax.bridgenotifier.core

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.longOrNull

/** What the bridge can tell the app: its notifications' kinds. */
object EventKind {
    const val BUY = "buy"
    const val SELL = "sell"
    const val ORDER_UPDATE = "order_update"
    const val ORDER_PROBLEM = "order_problem"
    const val ENGINE = "engine"
    const val SESSION = "session"
    const val READINESS = "readiness"
    const val FIDELITY_SIGNIN = "fidelity_signin"
    const val ACCOUNT_CHECK = "account_check"
    const val CONNECTED = "connected"
    const val DISCONNECTED = "disconnected"
    const val TRADING_SWITCH = "trading_switch"
    const val REFUSED = "refused"
    const val BRIDGE = "bridge"
    const val WINDOW = "window"

    /** A test the app asked for: never numbered, never kept by the bridge. */
    const val TEST = "test"

    /**
     * Every kind the bridge sends, in its order (notifications.py's EVENT_KINDS;
     * the shared vectors hold the list both sides check). A bridge newer than
     * this app may send others: they are shown too, under their own name.
     */
    val ALL = listOf(
        BUY, SELL, ORDER_UPDATE, ORDER_PROBLEM, ENGINE, SESSION, READINESS, FIDELITY_SIGNIN,
        ACCOUNT_CHECK, CONNECTED, DISCONNECTED, TRADING_SWITCH, REFUSED, BRIDGE, WINDOW,
    )

    fun label(kind: String): String = when (kind) {
        BUY -> "Buys filled"
        SELL -> "Sells filled"
        ORDER_UPDATE -> "Orders accepted, cancelled or expired"
        ORDER_PROBLEM -> "Orders rejected, refused or unknown"
        ENGINE -> "Engine started, paused, halted or stopped"
        SESSION -> "Session ended unexpectedly, or a second trader refused"
        READINESS -> "Not ready to trade, or ready again (and before the open)"
        FIDELITY_SIGNIN -> "Fidelity signed out"
        ACCOUNT_CHECK -> "Account check failed, or passed again"
        CONNECTED -> "Extension connected or reconnected"
        DISCONNECTED -> "Extension disconnected"
        TRADING_SWITCH -> "\"Allow trading\" switched on or off"
        REFUSED -> "A connection to the bridge was refused"
        BRIDGE -> "Bridge port taken, or bridge restarting"
        WINDOW -> "A trading window closed: its orders and what filled"
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
    /** The WebSocket close code its last connection ended with, while it is away. */
    val disconnectCode: Long?,
    val version: String?,
    /** What the bridge says to do about the extension's version, if anything. */
    val advice: String?,
    /** Its "Allow trading" switch; null before it has said. */
    val trading: Boolean?,
    val previews: Boolean?,
    /** Its Fidelity tab: signed_in, signed_out, no_tab, elsewhere; null before it has said. */
    val fidelity: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): ExtensionStatus? = obj?.let {
            ExtensionStatus(
                connected = it.bool("connected") == true,
                since = it.string("since"),
                disconnectedAt = it.string("disconnectedAt"),
                disconnectCode = it.long("disconnectCode"),
                version = it.string("version"),
                advice = it.string("advice"),
                trading = it.bool("trading"),
                previews = it.bool("previews"),
                fidelity = it.string("fidelity"),
            )
        }
    }
}

/** One link of the readiness chain (the bridge's readiness.py). */
data class ReadinessItem(
    val id: String,
    val label: String,
    /** ok, warn, fail or unknown. */
    val state: String,
    val detail: String,
    val fix: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): ReadinessItem? {
            val id = obj?.string("id") ?: return null
            return ReadinessItem(
                id = id,
                label = obj.string("label") ?: id,
                state = obj.string("state") ?: "unknown",
                detail = obj.string("detail").orEmpty(),
                fix = obj.string("fix"),
            )
        }
    }
}

/** The last read-only account check. */
data class AccountCheck(val at: String?, val ok: Boolean, val detail: String, val by: String?) {
    companion object {
        fun parse(obj: JsonObject?): AccountCheck? = obj?.let {
            AccountCheck(
                at = it.string("at"),
                ok = it.bool("ok") == true,
                detail = it.string("detail").orEmpty(),
                by = it.string("by"),
            )
        }
    }
}

/**
 * The bridge host's part of the status: whether the connection is ready to
 * trade, the chain behind that verdict, what is attached, the last account
 * check, the next open. Null from a bridge without a host (`serve`).
 */
data class HostStatus(
    val ready: Boolean,
    /** The first failing link's id, or null when ready. */
    val blocking: String?,
    val summary: String,
    val fix: String?,
    val items: List<ReadinessItem>,
    val listening: Boolean,
    val mode: String?,
    val symbol: String?,
    /** The process attached -- "loop" during a session -- or null. */
    val attached: String?,
    val attachedSince: String?,
    val lastCheck: AccountCheck?,
    val sessionOpen: Boolean,
    val nextOpen: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): HostStatus? = obj?.let {
            val attached = it["attached"] as? JsonObject
            HostStatus(
                ready = it.bool("ready") == true,
                blocking = it.string("blocking"),
                summary = it.string("summary").orEmpty(),
                fix = it.string("fix"),
                items = (it["items"] as? JsonArray).orEmpty()
                    .mapNotNull { item -> ReadinessItem.parse(item as? JsonObject) },
                listening = it.bool("listening") == true,
                mode = it.string("mode"),
                symbol = it.string("symbol"),
                attached = attached?.string("process"),
                attachedSince = attached?.string("since"),
                lastCheck = AccountCheck.parse(it["lastCheck"] as? JsonObject),
                sessionOpen = it.bool("sessionOpen") == true,
                nextOpen = it.string("nextOpen"),
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

/** A lot still held: what it cost and where it sells. */
data class OpenLot(
    val id: String,
    val qty: Double,
    val buyPrice: Double,
    val targetPrice: Double,
    /** ISO-8601, UTC; null when the fill journal no longer goes back that far. */
    val boughtAt: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): OpenLot? {
            if (obj == null) return null
            return OpenLot(
                id = obj.string("id") ?: return null,
                qty = obj.double("qty") ?: return null,
                buyPrice = obj.double("buyPrice") ?: return null,
                targetPrice = obj.double("targetPrice") ?: return null,
                boughtAt = obj.string("boughtAt"),
            )
        }
    }
}

/** One sale: what was sold, for what, and what it made after costs. */
data class ClosedLot(
    val id: String?,
    val qty: Double,
    val buyPrice: Double?,
    val sellPrice: Double,
    val pnl: Double?,
    /** profit_target, or signal_exit for a regime exit (the one sale that may lose). */
    val reason: String?,
    val boughtAt: String?,
    val soldAt: String?,
) {
    companion object {
        fun parse(obj: JsonObject?): ClosedLot? {
            if (obj == null) return null
            return ClosedLot(
                id = obj.string("id"),
                qty = obj.double("qty") ?: return null,
                buyPrice = obj.double("buyPrice"),
                sellPrice = obj.double("sellPrice") ?: return null,
                pnl = obj.double("pnl"),
                reason = obj.string("reason"),
                boughtAt = obj.string("boughtAt"),
                soldAt = obj.string("soldAt"),
            )
        }
    }
}

/**
 * The trading book (the bridge's book.py): the open lots, the last sales and
 * today's figures, read from the trader's ledger and fill journal. Null from a
 * bridge older than this, or one with no trader to read.
 */
data class Book(
    val symbol: String?,
    val asOf: String?,
    val lastPrice: Double?,
    val open: List<OpenLot>,
    val openCost: Double,
    /** Open lots at the last price, before costs; null without a price. */
    val unrealized: Double?,
    /** Newest first, at most 20. */
    val closed: List<ClosedLot>,
    /** Today's realised profit after costs, and today's sales and buys. */
    val realizedToday: Double,
    val salesToday: Int,
    val buysToday: Int,
) {
    companion object {
        fun parse(obj: JsonObject?): Book? = obj?.let {
            val today = it["today"] as? JsonObject
            Book(
                symbol = it.string("symbol"),
                asOf = it.string("asOf"),
                lastPrice = it.double("lastPrice"),
                open = (it["open"] as? JsonArray).orEmpty().mapNotNull { lot -> OpenLot.parse(lot as? JsonObject) },
                openCost = it.double("openCost") ?: 0.0,
                unrealized = it.double("unrealized"),
                closed = (it["closed"] as? JsonArray).orEmpty()
                    .mapNotNull { lot -> ClosedLot.parse(lot as? JsonObject) },
                realizedToday = today?.double("realized") ?: 0.0,
                salesToday = today?.long("sales")?.toInt() ?: 0,
                buysToday = today?.long("buys")?.toInt() ?: 0,
            )
        }
    }
}

/**
 * What the bridge shows apps: the extension's side, a trading session's
 * engine (null between sessions), the bridge host's readiness (null
 * without a host) and the trading book (null without a trader to read).
 */
data class BridgeStatus(
    val extension: ExtensionStatus?,
    val engine: EngineStatus?,
    val bridge: HostStatus? = null,
    val book: Book? = null,
) {
    companion object {
        val UNKNOWN = BridgeStatus(null, null, null)

        fun parse(obj: JsonObject?): BridgeStatus = BridgeStatus(
            extension = ExtensionStatus.parse(obj?.get("extension") as? JsonObject),
            engine = EngineStatus.parse(obj?.get("engine") as? JsonObject),
            bridge = HostStatus.parse(obj?.get("bridge") as? JsonObject),
            book = Book.parse(obj?.get("book") as? JsonObject),
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

    /** The bridge is stopping on purpose: a restart or a deploy. It is back shortly. */
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

internal fun JsonObject.double(name: String): Double? =
    (this[name] as? JsonPrimitive)?.takeUnless { it.isString }?.doubleOrNull

internal fun JsonObject.bool(name: String): Boolean? =
    (this[name] as? JsonPrimitive)?.takeUnless { it.isString }?.booleanOrNull
