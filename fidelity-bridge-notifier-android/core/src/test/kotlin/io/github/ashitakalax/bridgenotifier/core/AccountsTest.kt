package io.github.ashitakalax.bridgenotifier.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AccountsTest {
    private fun obj(text: String): JsonObject = Json.parseToJsonElement(text).jsonObject

    private fun note(kind: String, severity: Severity = Severity.INFO) = Notification(
        id = 1, stream = "s", kind = kind, severity = severity, title = "t", body = "b",
        at = "2026-11-18T15:00:00Z", data = JsonObject(emptyMap()),
    )

    private fun hello(text: String): Hello =
        (BridgeMessage.parse(obj(text)) as BridgeMessage.HelloMessage).hello

    @Test
    fun aHelloSaysWhichAccountItsStreamIsAbout() {
        val hello = hello(
            """{"type":"hello","stream":"s","events":[],"status":{},
            "account":{"id":"paper-ultimate","label":"Ultimate (paper)","broker":"alpaca",
            "paper":true,"symbol":"TQQQ"}}""",
        )
        assertEquals(
            AccountInfo("paper-ultimate", "Ultimate (paper)", Broker.ALPACA, true, "TQQQ"),
            hello.account,
        )
    }

    @Test
    fun aBridgeOlderThanThatSaysNothingAndAnUnknownBrokerIsOther() {
        assertNull(hello("""{"type":"hello","stream":"s","status":{}}""").account)
        assertNull(hello("""{"type":"hello","stream":"s","status":{}}""").backlog)
        assertEquals(3, hello("""{"type":"hello","stream":"s","status":{},"backlog":3}""").backlog)
        val other = hello("""{"type":"hello","stream":"s","status":{},"account":{"broker":"ibkr"}}""")
        assertEquals(Broker.OTHER, other.account?.broker)
        assertEquals(Broker.FIDELITY, Broker.parse(null))
        assertEquals(Broker.ALPACA, Broker.parse("Alpaca"))
    }

    @Test
    fun theTraderNotifiersStatusCarriesTheTradersOwnReport() {
        val status = BridgeStatus.parse(
            obj(
                """{"engine":null,"trader":{"state":"waiting_for_open","process":"supervisor",
                "stale":false,"running":false,"nextOpen":"2026-11-19T14:30:00+00:00",
                "detail":null}}""",
            ),
        )
        val trader = status.trader!!
        assertEquals("waiting_for_open", trader.state)
        assertEquals("supervisor", trader.process)
        assertFalse(trader.stale)
        assertFalse(trader.running)
        assertEquals("2026-11-19T14:30:00+00:00", trader.nextOpen)
        assertNull(status.engine)
        assertNull(status.extension)
        assertNull(BridgeStatus.parse(obj("""{"trader":null}""")).trader)
        // A report that does not say it is fresh is not believed to be.
        assertTrue(TraderStatus.parse(obj("""{"state":"trading"}"""))!!.stale)
    }

    @Test
    fun anAccountLearnsWhatItsHelloSaysAndKeepsWhatItDoesNot() {
        val saved = Account("a1", "ws://h:8766/notifications", "k".repeat(40))
        assertEquals("Fidelity", saved.name)
        val learned = saved.learned(AccountInfo(null, "Ultimate (paper)", Broker.ALPACA, true, "TQQQ"))
        assertEquals("Ultimate (paper)", learned.name)
        assertEquals(Broker.ALPACA, learned.broker)
        assertEquals("Alpaca · paper", learned.brokerLine)
        assertEquals(learned, learned.learned(AccountInfo(null, null, Broker.ALPACA, null, null)))
        assertEquals(saved, saved.learned(null))
    }

    @Test
    fun theNotifiersPortIsAlpacaUntilItsHelloSays() {
        assertEquals(Broker.ALPACA, Accounts.guessBroker("ws://192.168.1.10:8767/notifications/live"))
        assertEquals(Broker.FIDELITY, Accounts.guessBroker("ws://192.168.1.10:8766/notifications"))
        assertEquals(Broker.FIDELITY, Accounts.guessBroker("not a url"))
    }

    @Test
    fun theListRoundTripsAndANewIdIsOneNotTaken() {
        val accounts = listOf(
            Account("a1", "ws://h:8766/notifications", "k1".repeat(20), "Fidelity", Broker.FIDELITY, false),
            Account("a3", "ws://h:8767/notifications", "k2".repeat(20), "", Broker.ALPACA, null),
        )
        assertEquals(accounts, Accounts.decode(Accounts.encode(accounts)))
        assertEquals("a2", Accounts.newId(accounts))
        assertEquals("a1", Accounts.newId(emptyList()))
    }

    @Test
    fun eachAccountMutesForItself() {
        val alpaca = Account("a2", "ws://h:8767/notifications", "k".repeat(40), broker = Broker.ALPACA)
            .copy(mutedKinds = setOf(EventKind.BUY, EventKind.SELL))
        assertFalse(alpaca.alerts(note(EventKind.BUY), NOW))
        assertTrue(alpaca.alerts(note(EventKind.ORDER_PROBLEM), NOW))
        // A kind this app does not know yet is shown, as before.
        assertTrue(alpaca.alerts(note("margin_call"), NOW))
        assertTrue(alpaca.alertsLinks(NOW))

        val silent = alpaca.copy(muted = true)
        assertFalse(silent.alerts(note(EventKind.ORDER_PROBLEM), NOW))
        assertFalse(silent.alertsLinks(NOW))
        // The test asked for from the Connect page gets through regardless.
        assertTrue(silent.alerts(note(EventKind.TEST), NOW))

        assertEquals(listOf(silent), Accounts.decode(Accounts.encode(listOf(silent))))
        // Saved before there was muting: nothing muted.
        val old = Accounts.decode("""[{"id":"a1","url":"ws://h:8766/n","apiKey":"k"}]""").single()
        assertFalse(old.muted)
        assertEquals(emptySet<String>(), old.mutedKinds)
    }

    @Test
    fun mutedForAnHourIsQuietUntilTheHourIsUp() {
        val account = Account("a1", "ws://h:8766/notifications", "k".repeat(40))
            .copy(mutedUntil = NOW + 3_600_000)
        val problem = note(EventKind.ORDER_PROBLEM, Severity.WARNING)
        assertTrue(account.mutedFor(NOW))
        assertFalse(account.alerts(problem, NOW))
        assertFalse(account.alertsLinks(NOW + 3_599_999))
        assertTrue(account.alerts(problem, NOW + 3_600_000))
        assertTrue(account.alertsLinks(NOW + 3_600_000))
        assertFalse(account.mutedAt(NOW + 3_600_000))
        assertEquals(listOf(account), Accounts.decode(Accounts.encode(listOf(account))))
    }

    @Test
    fun anAccountSummingUpItsDaySaysOnlyTheTradesThatAreProblems() {
        val account = Account("a1", "ws://h:8767/notifications", "k".repeat(40), broker = Broker.ALPACA)
            .copy(summary = true)
        for (kind in EventKind.TRADES) assertFalse(kind, account.alerts(note(kind), NOW))
        // A sale below cost (a regime exit) is a warning: still said at once.
        assertTrue(account.alerts(note(EventKind.SELL, Severity.WARNING), NOW))
        assertTrue(account.alerts(note(EventKind.WINDOW, Severity.CRITICAL), NOW))
        // Everything that is not a trade is as before.
        assertTrue(account.alerts(note(EventKind.ENGINE), NOW))
        assertTrue(account.alerts(note(EventKind.ORDER_PROBLEM), NOW))
        assertTrue(account.copy(summary = false).alerts(note(EventKind.BUY), NOW))
        assertEquals(listOf(account), Accounts.decode(Accounts.encode(listOf(account))))
        val old = Accounts.decode("""[{"id":"a1","url":"ws://h:8766/n","apiKey":"k"}]""").single()
        assertFalse(old.summary)
        assertNull(old.mutedUntil)
    }

    @Test
    fun whatCannotBeReadIsLeftOut() {
        assertEquals(emptyList<Account>(), Accounts.decode(null))
        assertEquals(emptyList<Account>(), Accounts.decode("not json"))
        assertEquals(emptyList<Account>(), Accounts.decode("""{"id":"a1"}"""))
        val kept = Accounts.decode(
            """[{"id":"a1","url":"ws://h:8767/n","apiKey":"k"},{"url":"x"},7,
            {"id":"a1","url":"ws://dup:1/n","apiKey":"k"}]""",
        )
        assertEquals(1, kept.size)
        // No broker saved: guessed from the address.
        assertEquals(Broker.ALPACA, kept.single().broker)
    }

    private companion object {
        const val NOW = 1_800_000_000_000L
    }
}
