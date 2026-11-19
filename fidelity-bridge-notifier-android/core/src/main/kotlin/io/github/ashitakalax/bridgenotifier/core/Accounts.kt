package io.github.ashitakalax.bridgenotifier.core

import java.net.URI
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * One listener the app watches: its address and key, and what it last said
 * it is about. A Fidelity bridge (port 8766) and the trader notifier's
 * Alpaca deployments (port 8767, a path each) are each an account.
 */
data class Account(
    /** The app's own name for it, never sent anywhere. */
    val id: String,
    /** ws:// or wss://, as [BridgeAddress.parse] completed it. */
    val url: String,
    val apiKey: String,
    /** The hello's label ("Ultimate (paper)"); empty until it has connected once. */
    val label: String = "",
    /** The hello's broker; until it has said, [Accounts.guessBroker] from the address. */
    val broker: Broker = Broker.FIDELITY,
    /** Paper or real money, when the listener said. */
    val paper: Boolean? = null,
    /** The phone stays quiet about this account; what it says still reaches the Activity page. */
    val muted: Boolean = false,
    /** The kinds this account is not to buzz the phone about. Everything else is shown. */
    val mutedKinds: Set<String> = emptySet(),
    /**
     * Its trades summed up in one note after the close (DailySummary) rather
     * than said one by one; a trade that is a problem is still said at once.
     */
    val summary: Boolean = false,
    /** Quiet until this moment (epoch milliseconds): a notification's "Mute 1 h". */
    val mutedUntil: Long? = null,
) {
    /** What the screens call it. */
    val name: String get() = label.ifBlank { broker.label }

    /** "Alpaca · paper", "Fidelity": the broker and, when known, paper money. */
    val brokerLine: String get() = if (paper == true) "${broker.label} · paper" else broker.label

    /** Whether the account is quiet at [now]: muted, or muted for a while that has not run out. */
    fun mutedAt(now: Long): Boolean = muted || mutedFor(now)

    /** Muted for a while (and not for good) at [now]. */
    fun mutedFor(now: Long): Boolean = mutedUntil != null && now < mutedUntil

    /**
     * Whether [notification] is worth a phone notification at [now]. A test
     * always is: the app asked for it, to see that notifications get through.
     */
    fun alerts(notification: Notification, now: Long): Boolean = notification.isTest || (
        !mutedAt(now) &&
            notification.kind !in mutedKinds &&
            !(summary && notification.kind in EventKind.TRADES && notification.severity == Severity.INFO)
        )

    /** Whether losing or regaining this account's listener, or a refused key, is said at [now]. */
    fun alertsLinks(now: Long): Boolean = !mutedAt(now)

    /** This account, with what a hello said about it. A bridge that said nothing changes nothing. */
    fun learned(info: AccountInfo?): Account = if (info == null) {
        this
    } else {
        copy(label = info.label ?: label, broker = info.broker, paper = info.paper ?: paper)
    }
}

/** The account list as the app keeps it: one JSON array. */
object Accounts {
    /** The trader notifier's port: an account there is Alpaca until its hello says otherwise. */
    const val NOTIFIER_PORT = 8767

    fun guessBroker(url: String): Broker = try {
        if (URI(url).port == NOTIFIER_PORT) Broker.ALPACA else Broker.FIDELITY
    } catch (_: Exception) {
        Broker.FIDELITY
    }

    /** An id no account in [existing] has: a1, a2, ... */
    fun newId(existing: List<Account>): String {
        val taken = existing.map { it.id }.toSet()
        return generateSequence(1) { it + 1 }.map { "a$it" }.first { it !in taken }
    }

    fun encode(accounts: List<Account>): String = buildJsonArray {
        for (account in accounts) {
            add(
                buildJsonObject {
                    put("id", account.id)
                    put("url", account.url)
                    put("apiKey", account.apiKey)
                    put("label", account.label)
                    put("broker", account.broker.name)
                    account.paper?.let { put("paper", it) }
                    if (account.muted) put("muted", true)
                    if (account.mutedKinds.isNotEmpty()) {
                        put("mutedKinds", buildJsonArray { account.mutedKinds.sorted().forEach { add(JsonPrimitive(it)) } })
                    }
                    if (account.summary) put("summary", true)
                    account.mutedUntil?.let { put("mutedUntil", it) }
                },
            )
        }
    }.toString()

    /** What [encode] wrote; anything unreadable is left out rather than failing. */
    fun decode(text: String?): List<Account> {
        val array = text?.let { runCatching { Json.parseToJsonElement(it) }.getOrNull() }
            as? JsonArray ?: return emptyList()
        return array.mapNotNull { element ->
            val obj = element as? JsonObject ?: return@mapNotNull null
            val id = obj.string("id") ?: return@mapNotNull null
            val url = obj.string("url") ?: return@mapNotNull null
            val key = obj.string("apiKey") ?: return@mapNotNull null
            Account(
                id = id,
                url = url,
                apiKey = key,
                label = obj.string("label").orEmpty(),
                broker = Broker.entries.firstOrNull { it.name == obj.string("broker") } ?: guessBroker(url),
                paper = obj.bool("paper"),
                muted = obj.bool("muted") ?: false,
                mutedKinds = (obj["mutedKinds"] as? JsonArray)
                    ?.mapNotNull { (it as? JsonPrimitive)?.takeIf { p -> p.isString }?.content }
                    ?.toSet()
                    .orEmpty(),
                summary = obj.bool("summary") ?: false,
                mutedUntil = obj.long("mutedUntil"),
            )
        }.distinctBy { it.id }
    }
}
