"""Option-market readings read live: the session's GET and its allowlist, the
bridge page's `get` command, the collector (fidelity_gateway/options_live.py)
and the bridge host's once-a-day schedule for it. No network and no browser:
the page, the session and the bridge are stand-ins. The real extension runs
the same path in test_bridge_extension.py."""

from __future__ import annotations

import json
import threading
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from engine.core.config import BacktestConfig, FidelityBridgeConfig, FidelityOptionsConfig
from engine.core.exceptions import ConfigurationError
from fidelity_gateway import options_live as L
from fidelity_gateway.bridge.host import (
    COLLECT_ATTEMPTS,
    COLLECT_RETRY_SECONDS,
    COLLECT_WINDOW_SECONDS,
    BridgeHost,
    _extension_side,
    last_close,
)
from fidelity_gateway.bridge.page import BridgePage
from fidelity_gateway.bridge.server import BridgeRefusal
from fidelity_gateway.session import (
    FETCH_SCRIPT,
    GET_SCRIPT,
    ORDER_ENDPOINTS,
    READ_ONLY_ENDPOINTS,
    READ_ONLY_GET_ENDPOINTS,
    FidelitySession,
    FidelitySessionError,
    FidelitySessionExpired,
)

EASTERN = ZoneInfo("America/New_York")
STATISTICS = "/ftgw/digital/traderplus-api/api/key-statistics/v1"
EXPIRATIONS = "/ftgw/digital/traderplus-api/api/option-expirations/v1"
CHAIN = "/ftgw/digital/traderplus-api/api/slo-chain/v1"
PLACE = "/ftgw/digital/trade-equity/placeOrder"
NOW = datetime(2026, 11, 12, 21, 10, tzinfo=UTC)


# -- the session's GET -------------------------------------------------------------


class Page:
    """What FidelitySession needs of a page; answers every evaluate with `reply`."""

    def __init__(self, reply=None, url="https://digital.fidelity.com/ftgw/digital/traderplus"):
        self.url = url
        self.calls: list[tuple[str, list]] = []
        self.reply = reply or {"status": 200, "url": "https://digital.fidelity.com/x", "body": "{}"}

    def on(self, _event, _handler) -> None:
        pass

    def evaluate(self, script, arg=None):
        self.calls.append((script, arg))
        return self.reply(arg) if callable(self.reply) else self.reply


def test_the_pages_a_get_may_read_are_none_a_post_may_reach():
    assert set(READ_ONLY_GET_ENDPOINTS) == {STATISTICS, EXPIRATIONS, CHAIN}
    assert not set(READ_ONLY_GET_ENDPOINTS) & (set(READ_ONLY_ENDPOINTS) | set(ORDER_ENDPOINTS))
    assert L.API + L.STATISTICS_PATH == STATISTICS
    assert L.API + L.EXPIRATIONS_PATH == EXPIRATIONS
    assert L.API + L.CHAIN_PATH == CHAIN


def test_a_get_is_the_fixed_script_with_the_path_and_its_query():
    page = Page({"status": 200, "url": "https://digital.fidelity.com/x", "body": '{"a": 1}'})
    session = FidelitySession(page)
    # No token has been seen: these are the page's cookie-only reads.
    assert session.get_json(STATISTICS, {"underlying": "TQQQ"}) == {"a": 1}
    script, (path, query, timeout_ms) = page.calls[0]
    assert script == GET_SCRIPT and script != FETCH_SCRIPT
    assert (path, query) == (STATISTICS, {"underlying": "TQQQ"}) and timeout_ms > 0
    assert '"GET"' in GET_SCRIPT and "JSON.stringify" not in GET_SCRIPT


@pytest.mark.parametrize(
    ("path", "query", "match"),
    [
        (PLACE, {}, "not a Fidelity page"),
        ("/ftgw/digital/activityapi/api/v1/transactions/pending", {}, "not a Fidelity page"),
        (STATISTICS + "?underlying=TQQQ", {}, "not a Fidelity page"),
        (STATISTICS, {"account": "Z1"}, "not a parameter"),
        (EXPIRATIONS, {"symbol": "TQQQ&acct=Z1"}, "not one this session sends"),
        (EXPIRATIONS, {"symbol": 7}, "not one this session sends"),
        (EXPIRATIONS, {"symbol": "x" * 2001}, "not one this session sends"),
    ],
)
def test_a_get_outside_the_allowlist_is_refused_before_the_page_is_asked(path, query, match):
    page = Page()
    with pytest.raises(ConfigurationError, match=match):
        FidelitySession(page).get_json(path, query)
    assert page.calls == []


def test_a_get_reads_failures_as_a_post_does():
    signin = "https://digital.fidelity.com/prgw/digital/signin/retail"
    with pytest.raises(FidelitySessionExpired, match="GET"):
        FidelitySession(Page({"status": 200, "url": signin, "body": ""})).get_json(EXPIRATIONS)
    with pytest.raises(FidelitySessionError, match=r"GET .* returned 500"):
        FidelitySession(Page({"status": 500, "url": "", "body": "boom"})).get_json(EXPIRATIONS)
    with pytest.raises(FidelitySessionExpired):
        FidelitySession(Page(url=signin)).get_json(EXPIRATIONS)


# -- the bridge page ---------------------------------------------------------------


class Server:
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict, float]] = []

    def request(self, command, args, *, timeout=45.0):
        self.requests.append((command, args, timeout))
        return {"status": 200, "url": "u", "body": "{}", "tabUrl": "https://digital.fidelity.com/t"}

    def next_event(self, _timeout=0.0):
        return None


def test_the_bridge_sends_a_get_as_the_extensions_get_command_and_runs_no_other_script():
    server = Server()
    page = BridgePage(server)
    page.evaluate(GET_SCRIPT, [CHAIN, {"symbol": "TQQQ"}, 30_000])
    page.evaluate(FETCH_SCRIPT, ["/p", {"a": 1}, {"accept": "x"}, 30_000])
    get, fetch = server.requests
    assert get[:2] == ("get", {"path": CHAIN, "query": {"symbol": "TQQQ"}, "timeoutMs": 30_000})
    assert fetch[0] == "fetch" and set(fetch[1]) == {"path", "body", "headers", "timeoutMs"}
    assert page.url == "https://digital.fidelity.com/t"
    with pytest.raises(BridgeRefusal):
        page.evaluate(GET_SCRIPT + " ", [CHAIN, {}, 1])


# -- the chain's query -------------------------------------------------------------

LISTED = {
    "expirations": [
        {"date": "2026-11-11", "optionPeriodicity": "W"},  # already past on NOW's date
        {"date": "2026-11-13", "optionPeriodicity": "W"},
        {"date": "2026-11-20", "optionPeriodicity": "M"},
        {"date": "2026-12-04", "optionPeriodicity": "W"},
        {"date": "not a date"},
        {"date": "2027-01-15", "optionPeriodicity": "M"},
    ]
}


def test_the_nearest_expirations_still_ahead():
    nearest = L.nearest_expirations(LISTED, 3, NOW.date())
    assert nearest == [
        (date(2026, 11, 13), "W"),
        (date(2026, 11, 20), "M"),
        (date(2026, 12, 4), "W"),
    ]
    assert L.nearest_expirations({}, 3, NOW.date()) == []


def test_the_query_is_the_one_trader_plus_was_seen_to_send():
    seen = [(date(2026, 11, 11), "W"), (date(2026, 11, 20), "M")]
    assert L.chain_query("TQQQ", seen, 10, padded=True) == {
        "strikes": "10",
        "expirationDates": "11/11/2026,11/20/2026",
        "settlementTypes": "Nov 11 2026|W,Nov 20 2026|M",
        "symbol": "TQQQ",
        "adjustedOptionsData": "true",
    }
    early = [(date(2026, 12, 4), "W")]
    assert L.chain_query("TQQQ", early, 10, padded=True)["settlementTypes"] == "Dec 04 2026|W"
    unpadded = L.chain_query("TQQQ", [(date(2027, 1, 8), "W")], 10, padded=False)
    assert (
        unpadded["expirationDates"] == "1/8/2027" and unpadded["settlementTypes"] == "Jan 8 2027|W"
    )
    for query in (L.chain_query("TQQQ", seen, 10, padded=True), unpadded):
        assert set(query) == READ_ONLY_GET_ENDPOINTS[CHAIN]


# -- collecting --------------------------------------------------------------------

STATS = {
    "underlyingsymbol": "TQQQ",
    "iv30percentile": 56,
    "hv30percentile": 100,
    "callVolume": 40000,
    "putVolume": 30000,
    "avgCallVolume": 150000,
    "avgPutVolume": 150000,
    "callOpenInterest": 1000000,
    "putOpenInterest": 650000,
}


def rows(dates: str) -> list[dict]:
    out = []
    for n, _day in enumerate(dates.split(",")):
        for strike, delta in ((54, 0.75), (56, 0.5), (58, 0.25)):
            out.append(
                {
                    "expirationData": {"date": f"exp {n}", "daysToExpiration": 1 + 6 * n},
                    "strike": strike,
                    "callImpliedVolatility": 0.8,
                    "putImpliedVolatility": 0.9,
                    "callDelta": delta,
                    "putDelta": delta - 1,
                    "callGamma": 0.04,
                    "putGamma": 0.04,
                    "callOpenInterest": 1000,
                    "putOpenInterest": 400,
                    "callIntrinsicValue": max(0.0, 56.0 - strike),
                    "putIntrinsicValue": max(0.0, strike - 56.0),
                }
            )
    return out


class Session:
    """get_json over canned replies; `accepts(query)` says whether the chain
    answers with strikes."""

    def __init__(self, accepts=lambda query: True, listed=LISTED, statistics=STATS) -> None:
        self.asked: list[tuple[str, dict]] = []
        self.accepts, self.listed, self.statistics = accepts, listed, statistics

    def attach(self) -> None:
        pass

    def get_json(self, path, query=None):
        self.asked.append((path, dict(query or {})))
        if path == STATISTICS:
            if isinstance(self.statistics, Exception):
                raise self.statistics
            return self.statistics
        if path == EXPIRATIONS:
            return self.listed
        found = rows(query["expirationDates"]) if self.accepts(query) else []
        return {"underlyingSymbol": query["symbol"], "callsAndPuts": found}


def test_one_fund_is_three_reads_and_a_capture_stamped_when_it_was_taken():
    session = Session()
    capture, how = L.collect(session, "tqqq", strikes=10, expirations=2, now=NOW)
    assert [path for path, _ in session.asked] == [STATISTICS, EXPIRATIONS, CHAIN]
    assert session.asked[0][1] == {"underlying": "TQQQ"}
    assert session.asked[2][1]["expirationDates"] == "11/13/2026,11/20/2026"
    assert (capture.symbol, capture.at, how) == ("TQQQ", NOW, "padded dates")
    assert capture.expirations == ["2026-11-13", "2026-11-20"]
    assert len(capture.chain["callsAndPuts"]) == 6 and capture.statistics == STATS


def test_a_single_digit_day_is_asked_padded_and_then_unpadded():
    session = Session(accepts=lambda query: "12/4/2026" in query["expirationDates"])
    capture, how = L.collect(session, "TQQQ", expirations=3, now=NOW)
    chains = [query["expirationDates"] for path, query in session.asked if path == CHAIN]
    assert chains == ["11/13/2026,11/20/2026,12/04/2026", "11/13/2026,11/20/2026,12/4/2026"]
    assert how == "unpadded dates" and capture.chain is not None
    # With no day or month below ten there is one way to write it, asked once.
    plain = Session(accepts=lambda query: False)
    capture, how = L.collect(plain, "TQQQ", expirations=2, now=NOW)
    assert sum(path == CHAIN for path, _ in plain.asked) == 1
    assert capture.chain is None and how == "the chain came back empty"
    assert capture.statistics == STATS  # the statistics' readings are still kept


def test_the_collector_appends_each_funds_readings(tmp_path, monkeypatch):
    options = FidelityOptionsConfig(symbols=("TQQQ", "QQQ"), expirations=2)
    session = Session()
    monkeypatch.setattr("fidelity_gateway.session.FidelitySession", lambda page: session)
    run = L.options_collector(lambda: options, lambda: tmp_path, lambda: NOW)
    detail = run(object())
    assert detail == "TQQQ: 10 reading(s) (padded dates); QQQ: 10 reading(s) (padded dates)"
    text = (tmp_path / "fidelity_TQQQ_IV30_PCTL.csv").read_text()
    assert text == "timestamp,close\n2026-11-12 21:10:00+00:00,56.0\n"
    assert (tmp_path / "fidelity_QQQ_SKEW_25D.csv").exists()
    # The same instant again adds nothing.
    assert "0 reading(s)" in run(object())


def test_an_extension_too_old_to_get_is_said_so_and_one_fund_failing_keeps_the_rest(
    tmp_path, monkeypatch
):
    old = Session(statistics=BridgeRefusal('"get" is not a command', code="unknown_command"))
    monkeypatch.setattr("fidelity_gateway.session.FidelitySession", lambda page: old)
    run = L.options_collector(
        lambda: FidelityOptionsConfig(symbols=("TQQQ",)), lambda: tmp_path, lambda: NOW
    )
    with pytest.raises(RuntimeError, match=r"0\.8\.0 or newer"):
        run(object())
    assert list(tmp_path.iterdir()) == []

    class Flaky(Session):
        def get_json(self, path, query=None):
            if (query or {}).get("underlying") == "QQQ":
                raise FidelitySessionError("GET returned 500")
            return super().get_json(path, query)

    flaky = Flaky()
    monkeypatch.setattr("fidelity_gateway.session.FidelitySession", lambda page: flaky)
    run = L.options_collector(
        lambda: FidelityOptionsConfig(symbols=("QQQ", "TQQQ")), lambda: tmp_path, lambda: NOW
    )
    detail = run(object())
    assert "TQQQ: 10 reading(s)" in detail and "QQQ: FidelitySessionError" in detail


def test_with_no_funds_named_nothing_is_asked(monkeypatch):
    def refuse(_page):
        raise AssertionError("no session should be built")

    monkeypatch.setattr("fidelity_gateway.session.FidelitySession", refuse)
    run = L.options_collector(lambda: FidelityOptionsConfig())
    assert "no funds are named" in run(object())


def test_the_series_go_beside_the_ones_the_refresh_keeps(monkeypatch, tmp_path):
    monkeypatch.setenv("VAI_EXTERNAL_DIR", str(tmp_path))
    assert L.external_directory() == tmp_path
    monkeypatch.delenv("VAI_EXTERNAL_DIR")
    assert L.external_directory().parts[-2:] == ("data", "external")


# -- the host's schedule -----------------------------------------------------------


def at(text: str) -> float:
    return datetime.fromisoformat(text).replace(tzinfo=EASTERN).timestamp()


class Bridge:
    """A BridgeServer as far as a host that only collects can tell."""

    connected = True

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


def host(tmp_path, clock, collect, minutes=10) -> BridgeHost:
    built = BridgeHost(
        make_server=lambda settings, on_event: Bridge(),
        settings=lambda: (type("F", (), {"bridge": FidelityBridgeConfig()})(), "RSP"),
        socket_path=tmp_path / "bridge.sock",
        clock=clock,
        log=lambda _message: None,
        collect=collect,
        collect_after=lambda: minutes,
    )
    built._replay = lambda: []
    # Run what the host would spawn at once, on this thread.
    built._spawn = lambda target, _name, *args: target(*args) or threading.current_thread()
    return built


def test_the_close_that_has_passed_today():
    assert last_close(at("2026-11-12 15:59")) is None
    assert last_close(at("2026-11-12 16:00")).isoformat() == "2026-11-12T16:00:00-05:00"
    assert last_close(at("2026-11-14 18:00")) is None  # a Saturday
    assert last_close(at("2026-11-26 18:00")) is None  # Thanksgiving


def test_the_readings_are_collected_once_a_day_after_the_close(tmp_path):
    now = [at("2026-11-12 15:30")]
    ran: list[str] = []
    bridge_host = host(
        tmp_path, lambda: now[0], lambda page: ran.append("x") or "TQQQ: 10 reading(s)"
    )
    for moment in ("2026-11-12 15:30", "2026-11-12 16:05"):  # open, then not yet due
        now[0] = at(moment)
        bridge_host._auto_collect(now[0])
    assert ran == []
    now[0] = at("2026-11-12 16:10")
    bridge_host._auto_collect(now[0])
    assert ran == ["x"]
    assert bridge_host.last_collect["ok"] and bridge_host.last_collect["day"] == "2026-11-12"
    now[0] = at("2026-11-12 17:00")
    bridge_host._auto_collect(now[0])
    assert ran == ["x"]  # once
    now[0] = at("2026-11-13 16:10")
    bridge_host._auto_collect(now[0])
    assert ran == ["x", "x"]  # and again the next trading day


def test_nothing_is_collected_while_a_trading_loop_is_attached_or_no_extension_is(tmp_path):
    now = [at("2026-11-12 16:10")]
    ran: list[str] = []
    bridge_host = host(tmp_path, lambda: now[0], lambda page: ran.append("x") or "ok")
    bridge_host._attached = object()
    bridge_host._auto_collect(now[0])
    bridge_host._attached, bridge_host.server.connected = None, False
    bridge_host._auto_collect(now[0])
    assert ran == [] and bridge_host.last_collect is None
    bridge_host.server.connected = True
    bridge_host._auto_collect(now[0])
    assert ran == ["x"]


def test_a_failed_collection_is_tried_again_a_few_times_and_then_left(tmp_path):
    now = [at("2026-11-12 16:10")]
    tries: list[float] = []

    def failing(_page):
        tries.append(now[0])
        raise FidelitySessionError("signed out")

    bridge_host = host(tmp_path, lambda: now[0], failing)
    bridge_host._auto_collect(now[0])
    now[0] += 60
    bridge_host._auto_collect(now[0])  # too soon to try again
    assert len(tries) == 1 and not bridge_host.last_collect["ok"]
    for _ in range(COLLECT_ATTEMPTS + 2):
        now[0] += COLLECT_RETRY_SECONDS
        bridge_host._auto_collect(now[0])
    assert len(tries) == COLLECT_ATTEMPTS
    assert "signed out" in bridge_host.last_collect["detail"]


def test_a_host_started_long_after_the_close_does_not_collect_stale_readings(tmp_path):
    late = at("2026-11-12 16:00") + COLLECT_WINDOW_SECONDS + 60
    ran: list[str] = []
    bridge_host = host(tmp_path, lambda: late, lambda page: ran.append("x") or "ok")
    bridge_host._auto_collect(late)
    assert ran == []


def test_collection_is_off_unless_funds_are_named(tmp_path):
    now = at("2026-11-12 16:10")
    ran: list[str] = []
    off = host(tmp_path, lambda: now, lambda page: ran.append("x") or "ok", minutes=None)
    off._auto_collect(now)
    assert ran == []


# -- the config --------------------------------------------------------------------


def test_the_settings_are_off_by_default_and_checked():
    assert FidelityOptionsConfig().symbols == ()
    for bad in (
        FidelityOptionsConfig(symbols=("TQQQ&x",)),
        FidelityOptionsConfig(symbols=("TQQQ",), strikes=1),
        FidelityOptionsConfig(symbols=("TQQQ",), expirations=0),
        FidelityOptionsConfig(symbols=("TQQQ",), after_close_minutes=True),
    ):
        with pytest.raises(ConfigurationError, match=r"live\.fidelity\.bridge\.options"):
            BacktestConfig._validate_fidelity_options(bad)
    BacktestConfig._validate_fidelity_options(FidelityOptionsConfig(symbols=("TQQQ", "BRK.B")))


def test_an_edit_to_the_options_does_not_restart_the_extensions_bridge():
    a = FidelityBridgeConfig()
    b = FidelityBridgeConfig(options=FidelityOptionsConfig(symbols=("TQQQ",)))
    assert a != b and _extension_side(a) == _extension_side(b)
    assert json.dumps(b.options.to_dict())  # serialisable, for the config's own to_dict
