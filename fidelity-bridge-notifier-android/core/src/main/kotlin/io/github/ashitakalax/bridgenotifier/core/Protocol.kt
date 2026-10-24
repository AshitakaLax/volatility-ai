package io.github.ashitakalax.bridgenotifier.core

import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.put

/**
 * fidelity-bridge-notify/v1, the app's half. PROTOCOL.md describes it; the
 * bridge's half is fidelity_gateway/bridge/notify_protocol.py in
 * volatility-ai. Both reproduce core/src/test/resources/vectors/.
 *
 * Neither side ever sends the API key: each proves it holds the key by
 * answering the other's random nonce with an HMAC, and every message after
 * the handshake is sealed with a sequence number and an HMAC under a key
 * derived for that connection alone.
 */
object NotifyProtocol {
    const val PROTOCOL = "fidelity-bridge-notify/v1"
    const val PATH = "/notifications"
    const val DEFAULT_PORT = 8766

    private val HEX64 = Regex("[0-9a-f]{64}")

    fun appProof(apiKey: String, bridgeNonce: String, appNonce: String): String =
        hmac(apiKey.toByteArray(Charsets.UTF_8), "$PROTOCOL|app-proof|$bridgeNonce|$appNonce").toHex()

    fun bridgeProof(apiKey: String, bridgeNonce: String, appNonce: String): String =
        hmac(apiKey.toByteArray(Charsets.UTF_8), "$PROTOCOL|bridge-proof|$bridgeNonce|$appNonce").toHex()

    fun sessionKey(apiKey: String, bridgeNonce: String, appNonce: String): ByteArray =
        hmac(apiKey.toByteArray(Charsets.UTF_8), "$PROTOCOL|session|$bridgeNonce|$appNonce")

    fun messageMac(key: ByteArray, sender: String, seq: Long, payload: String): String =
        hmac(key, "$sender|$seq|$payload").toHex()

    /** 32 random bytes as lower-case hex. */
    fun newNonce(random: SecureRandom = SecureRandom()): String =
        ByteArray(32).also(random::nextBytes).toHex()

    fun isNonce(value: String?): Boolean = value != null && HEX64.matches(value)

    /** Constant time, so the time taken says nothing about a forged proof. */
    fun proofsMatch(expected: String, given: String?): Boolean =
        given != null && MessageDigest.isEqual(expected.toByteArray(), given.toByteArray())

    internal fun isMac(value: String?): Boolean = isNonce(value)

    private fun hmac(key: ByteArray, message: String): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        return mac.doFinal(message.toByteArray(Charsets.UTF_8))
    }
}

private val HEX_DIGITS = "0123456789abcdef".toCharArray()

internal fun ByteArray.toHex(): String {
    val out = CharArray(size * 2)
    forEachIndexed { i, byte ->
        val v = byte.toInt() and 0xff
        out[i * 2] = HEX_DIGITS[v ushr 4]
        out[i * 2 + 1] = HEX_DIGITS[v and 0x0f]
    }
    return String(out)
}

/** Anything short of a perfect, in-order, untampered message. */
class ProtocolException(message: String) : Exception(message)

/**
 * One connection's sealing and checking. Sequence numbers start at 1 in
 * each direction and must arrive exactly in order; a failed check throws
 * and does not advance the counter. The MAC covers the payload TEXT, so
 * the two sides never have to agree on how to serialise anything.
 */
class Channel(
    private val key: ByteArray,
    val sender: String = "app",
    val peer: String = "bridge",
) {
    var sent = 0L
        private set
    var received = 0L
        private set

    fun seal(message: JsonObject): String {
        val payload = message.toString()
        sent += 1
        return buildJsonObject {
            put("seq", sent)
            put("payload", payload)
            put("mac", NotifyProtocol.messageMac(key, sender, sent, payload))
        }.toString()
    }

    fun open(frame: String): JsonObject {
        val envelope = parseObject(frame) ?: throw ProtocolException("not an envelope")
        val seq = (envelope["seq"] as? JsonPrimitive)?.takeUnless { it.isString }?.longOrNull
        if (seq == null || seq != received + 1) {
            throw ProtocolException("expected message ${received + 1}, got ${envelope["seq"]}")
        }
        val payload = (envelope["payload"] as? JsonPrimitive)?.takeIf { it.isString }?.content
            ?: throw ProtocolException("missing payload")
        val mac = (envelope["mac"] as? JsonPrimitive)?.takeIf { it.isString }?.content
        if (!NotifyProtocol.isMac(mac)) throw ProtocolException("missing MAC")
        val expected = NotifyProtocol.messageMac(key, peer, seq, payload)
        if (!NotifyProtocol.proofsMatch(expected, mac)) {
            throw ProtocolException("message $seq failed its integrity check")
        }
        val message = parseObject(payload) ?: throw ProtocolException("message $seq is not an object")
        received = seq
        return message
    }
}

internal fun parseObject(text: String): JsonObject? =
    try {
        Json.parseToJsonElement(text) as? JsonObject
    } catch (_: SerializationException) {
        null
    } catch (_: IllegalArgumentException) {
        null
    }
