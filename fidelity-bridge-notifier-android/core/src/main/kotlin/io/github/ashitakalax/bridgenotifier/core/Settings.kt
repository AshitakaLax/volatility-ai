package io.github.ashitakalax.bridgenotifier.core

import java.net.URI
import java.net.URISyntaxException

/** The notification key, as the bridge's keygen makes it. */
object ApiKeys {
    // The bridge accepts exactly this alphabet and length range
    // (fidelity_gateway/bridge/keys.py); a key it would refuse is refused here.
    private val PATTERN = Regex("[A-Za-z0-9._~+/=-]{32,256}")

    fun looksValid(key: String): Boolean = PATTERN.matches(key)
}

/**
 * Where the bridge's notification listener is, from what someone types:
 * `192.168.1.10`, `192.168.1.10:9000`, `my-server.lan`, or a full
 * `ws://` / `wss://` URL. A missing port is the listener's default (8766)
 * and a missing path is /notifications.
 */
object BridgeAddress {
    fun parse(text: String): String? {
        val trimmed = text.trim()
        if (trimmed.isEmpty() || trimmed.any { it.isWhitespace() }) return null
        val withScheme = if ("://" in trimmed) trimmed else "ws://$trimmed"
        val uri = try {
            URI(withScheme)
        } catch (_: URISyntaxException) {
            return null
        }
        val scheme = uri.scheme?.lowercase()
        if (scheme != "ws" && scheme != "wss") return null
        val host = uri.host ?: return null
        if (uri.userInfo != null || uri.query != null || uri.fragment != null) return null
        val port = if (uri.port == -1) NotifyProtocol.DEFAULT_PORT else uri.port
        val path = uri.path.takeUnless { it.isNullOrEmpty() || it == "/" } ?: NotifyProtocol.PATH
        val bracketed = if (':' in host && !host.startsWith("[")) "[$host]" else host
        return "$scheme://$bracketed:$port$path"
    }

    /** Whether messages to it travel unencrypted (they are still sealed). */
    fun isPlainText(url: String): Boolean = url.startsWith("ws://")
}

/** The last notification the app saw: which bridge run, which number. */
data class Position(val stream: String, val id: Long)

/** Where the app keeps its [Position], so a restart does not show anything twice. */
interface PositionStore {
    fun load(): Position?
    fun save(position: Position)
}

class MemoryPositionStore(private var position: Position? = null) : PositionStore {
    override fun load(): Position? = position
    override fun save(position: Position) {
        this.position = position
    }
}
