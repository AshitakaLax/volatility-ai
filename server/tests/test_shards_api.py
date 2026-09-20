"""Distributed sweeps over HTTP: server/shards.py and server/shard_client.py.

A private JobQueue is swapped into server.backtest for each test (the
same approach as test_queue_api.py) with its local shard paused, so every
run is claimed by the shard under test. Bars come from the regression
fixture through the same monkeypatch the engine tests use; the real
warehouse has no such ticker, so the shard routes fall back to hashing
the fixture for its fingerprint.
"""

from __future__ import annotations

import io
import json
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import server.backtest as backtest
import server.shards as shards
from server.app import app
from server.jobs import LOCAL_SHARD, JobQueue, QueueStore
from server.shard_client import (
    Link,
    RemoteBars,
    ShardProcess,
    ShardRefused,
    UnknownToMain,
    main_url,
)

TIMEOUT = 30.0
FIXTURE = "tests/fixtures/regression_ohlcv.csv"
REQUEST = {
    "name": "shard sweep",
    "tickers": ["TESTQ"],
    "grid_steps": [0.005, 0.01],
    "targets": [0.003, 0.005],
    "model": "fixed",
    "params": {"allocation_pct": 0.05},
}


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, parse_dates=["timestamp"]).set_index("timestamp")


@pytest.fixture
def fixture_bars(monkeypatch, frame):
    monkeypatch.setattr(backtest, "available_tickers", lambda: {"TESTQ"})
    monkeypatch.setattr(
        backtest, "load_frame", lambda ticker: frame.copy() if ticker == "TESTQ" else frame.iloc[:0]
    )
    return frame


@pytest.fixture
def archived() -> list[str]:
    return []


@pytest.fixture
def queue(tmp_path, monkeypatch, archived) -> JobQueue:
    private = JobQueue(
        runner=backtest.run_backtest,
        on_complete=lambda job: archived.append(job.run_id),
        store=QueueStore(lambda: tmp_path / "queue"),
    )
    private.pause_shard(LOCAL_SHARD)
    monkeypatch.setattr(backtest, "queue", private)
    return private


@pytest.fixture
def client(queue) -> TestClient:
    return TestClient(app)


def register(client: TestClient, name: str, instance: str = "i1", **fields) -> dict:
    response = client.post(
        f"/api/backtest/shards/{name}/register", json={"instance": instance, **fields}
    )
    assert response.status_code == 200, response.text
    return response.json()


def wait_for(predicate, timeout: float = TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("condition never held")


class TestBarCodec:
    def test_round_trips_an_aware_frame_exactly(self, frame):
        decoded = shards.decode_bars(shards.encode_bars(frame))
        pd.testing.assert_frame_equal(decoded, frame[list(shards.BAR_COLUMNS)], check_freq=False)
        assert str(decoded.index.tz) == "UTC"

    def test_round_trips_a_naive_frame_as_naive(self, frame):
        naive = frame.copy()
        naive.index = naive.index.tz_localize(None)
        decoded = shards.decode_bars(shards.encode_bars(naive))
        assert decoded.index.tz is None
        assert (decoded.index == naive.index).all()

    def test_a_payload_cannot_carry_pickled_objects(self):
        buffer = io.BytesIO()
        np.savez(
            buffer,
            aware=np.array([1], dtype="int8"),
            unit=np.array(["ns"]),
            timestamp=np.array([object()], dtype=object),
        )
        with pytest.raises(ValueError, match="allow_pickle"):
            shards.decode_bars(buffer.getvalue())

    def test_garbage_is_a_value_error(self):
        with pytest.raises(ValueError):
            shards.decode_bars(b"not an archive")


class TestUiRoutes:
    def test_the_local_shard_is_listed_with_the_main_build(self, client, monkeypatch):
        monkeypatch.setattr(shards, "_main_commit", {"commit": "abc1234", "dirty": False})
        body = client.get("/api/backtest/shards").json()
        assert body["commit"] == "abc1234"
        assert body["shards"][0]["name"] == LOCAL_SHARD
        assert body["shards"][0]["commit"] == "abc1234"
        assert body["timeout_s"] > body["stale_s"] > 0

    def test_pause_resume_and_pause_all(self, client):
        register(client, "fast")
        assert client.post("/api/backtest/shards/fast", json={"op": "pause"}).json()["state"] == (
            "paused"
        )
        assert client.post("/api/backtest/shards/fast", json={"op": "resume"}).json()["state"] == (
            "idle"
        )
        assert client.post("/api/backtest/shards", json={"paused": True}).json() == {"paused": True}
        listing = client.get("/api/backtest/shards").json()
        assert listing["paused"] is True
        assert {s["state"] for s in listing["shards"]} == {"paused"}

    def test_unknown_shard_is_404_and_a_refused_op_is_409(self, client):
        assert client.post("/api/backtest/shards/nope", json={"op": "pause"}).status_code == 404
        response = client.post(f"/api/backtest/shards/{LOCAL_SHARD}", json={"op": "forget"})
        assert response.status_code == 409

    def test_a_bad_shard_name_is_rejected_by_the_route(self, client):
        response = client.post("/api/backtest/shards/-bad/register", json={"instance": "i"})
        assert response.status_code == 422

    def test_a_running_run_names_its_shard(self, client, queue):
        register(client, "fast")
        run = client.post("/api/backtest/runs", json=REQUEST).json()
        client.post("/api/backtest/shards/fast/claim", json={"instance": "i1"})
        assert client.get(f"/api/backtest/runs/{run['id']}").json()["shard"] == "fast"
        assert client.get("/api/backtest/shards").json()["shards"][1]["run"]["id"] == run["id"]

    def test_set_and_clear_a_lockout_schedule(self, client):
        register(client, "fast")
        response = client.post(
            "/api/backtest/shards/fast/schedule",
            json={"enabled": True, "start": "07:00", "end": "19:00"},
        )
        assert response.status_code == 200, response.text
        assert response.json() == {
            "name": "fast",
            "schedule": {"enabled": True, "start": "07:00", "end": "19:00"},
        }

        listed = next(
            s for s in client.get("/api/backtest/shards").json()["shards"] if s["name"] == "fast"
        )
        assert listed["schedule"] == {"enabled": True, "start": "07:00", "end": "19:00"}

        cleared = client.post("/api/backtest/shards/fast/schedule", json={"enabled": False})
        assert cleared.json()["schedule"] is None

    def test_a_bad_schedule_is_400_not_a_server_error(self, client):
        register(client, "fast")
        missing_end = client.post(
            "/api/backtest/shards/fast/schedule", json={"enabled": True, "start": "07:00"}
        )
        assert missing_end.status_code == 400
        bad_format = client.post(
            "/api/backtest/shards/fast/schedule",
            json={"enabled": True, "start": "not-a-time", "end": "19:00"},
        )
        assert bad_format.status_code == 400

    def test_a_schedule_can_be_set_before_the_shard_ever_registers(self, client):
        response = client.post(
            "/api/backtest/shards/never-connected/schedule",
            json={"enabled": True, "start": "22:00", "end": "06:00"},
        )
        assert response.status_code == 200, response.text


class TestProtocolRoutes:
    def test_a_different_commit_is_refused_unless_allowed(self, client, monkeypatch):
        monkeypatch.setattr(shards, "_main_commit", {"commit": "aaaaaaa", "dirty": False})
        response = client.post(
            "/api/backtest/shards/fast/register", json={"instance": "i", "commit": "bbbbbbb"}
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "version_mismatch"
        register(client, "fast", commit="bbbbbbb", allow_version_mismatch=True)

    def test_an_unknown_commit_is_not_a_mismatch(self, client, monkeypatch):
        monkeypatch.setattr(shards, "_main_commit", {"commit": None, "dirty": None})
        register(client, "fast", commit="bbbbbbb")

    def test_claim_sync_finish(self, client, queue, archived):
        register(client, "fast")
        assert client.post("/api/backtest/shards/fast/claim", json={"instance": "i1"}).json() == {
            "run": None
        }

        run_id = client.post("/api/backtest/runs", json=REQUEST).json()["id"]
        claimed = client.post("/api/backtest/shards/fast/claim", json={"instance": "i1"}).json()
        assert claimed["run"]["id"] == run_id
        assert claimed["run"]["request"]["tickers"] == ["TESTQ"]
        assert claimed["run"]["rows"] == {}

        # NaN is what engine rows can carry; it must survive the trip.
        body = json.dumps(
            {
                "instance": "i1",
                "run": run_id,
                "progress": 0.25,
                "msg": "TESTQ: 1/4",
                "rows": [{"ticker": "TESTQ", "row": {"Grid Step": 0.005, "Sharpe": float("nan")}}],
            }
        )
        synced = client.post(
            "/api/backtest/shards/fast/sync",
            content=body,
            headers={"content-type": "application/json"},
        )
        assert synced.json() == {"paused": False, "locked_out": False, "owned": True, "stop": False}
        assert client.get(f"/api/backtest/runs/{run_id}").json()["progress"] == 0.25

        # Released, then claimed again: the checkpoint comes back, NaN intact.
        client.post(
            f"/api/backtest/shards/fast/runs/{run_id}/finish",
            json={"instance": "i1", "outcome": "released", "error": "test"},
        )
        again = client.post("/api/backtest/shards/fast/claim", json={"instance": "i1"})
        row = json.loads(again.content)["run"]["rows"]["TESTQ"][0]
        assert row["Grid Step"] == 0.005 and row["Sharpe"] != row["Sharpe"]

        done = client.post(
            f"/api/backtest/shards/fast/runs/{run_id}/finish",
            json={"instance": "i1", "outcome": "complete", "report": {"id": "", "funds": {}}},
        )
        assert done.status_code == 200
        assert client.get(f"/api/backtest/runs/{run_id}").json()["status"] == "complete"
        assert archived == [run_id]

    def test_refusals_carry_a_code_the_shard_can_act_on(self, client, queue):
        register(client, "fast", instance="old")
        register(client, "fast", instance="new")
        stale = client.post("/api/backtest/shards/fast/sync", json={"instance": "old"})
        assert (stale.status_code, stale.json()["detail"]["code"]) == (409, "superseded")

        gone = client.post("/api/backtest/shards/ghost/sync", json={"instance": "x"})
        assert (gone.status_code, gone.json()["detail"]["code"]) == (404, "unknown_shard")

        run_id = client.post("/api/backtest/runs", json=REQUEST).json()["id"]
        foreign = client.post(
            f"/api/backtest/shards/fast/runs/{run_id}/finish",
            json={"instance": "new", "outcome": "complete", "report": {}},
        )
        assert (foreign.status_code, foreign.json()["detail"]["code"]) == (409, "not_owner")

    def test_bar_data_routes(self, client, fixture_bars):
        assert client.get("/api/backtest/shard-data/tickers").json() == {"tickers": ["TESTQ"]}
        fingerprint = client.get("/api/backtest/shard-data/bars/TESTQ/fingerprint").json()
        payload = client.get("/api/backtest/shard-data/bars/TESTQ")
        assert payload.headers[shards.FINGERPRINT_HEADER] == fingerprint["fingerprint"]
        assert len(shards.decode_bars(payload.content)) == len(fixture_bars)
        assert client.get("/api/backtest/shard-data/bars/NOPE").status_code == 404
        assert client.get("/api/backtest/shard-data/bars/NOPE/fingerprint").status_code == 404


class TestShardProcess:
    def test_a_shard_runs_a_sweep_and_matches_a_local_run(
        self, tmp_path, client, queue, fixture_bars
    ):
        local = backtest.run_backtest(dict(REQUEST), lambda fraction, note: None)
        run_id = client.post("/api/backtest/runs", json=REQUEST).json()["id"]

        process = ShardProcess(
            "worker",
            "http://testserver",
            cache_dir=tmp_path / "cache",
            client=TestClient(app),
            claim_wait=0.2,
            sync_interval=0.05,
            retry_seconds=0.05,
            log=lambda message: None,
        )
        results: list[int] = []
        thread = threading.Thread(
            target=lambda: results.append(process.run_forever(max_runs=1)), daemon=True
        )
        thread.start()
        thread.join(TIMEOUT)
        assert results == [0], "the shard did not finish its one sweep"

        run = client.get(f"/api/backtest/runs/{run_id}").json()
        assert run["status"] == "complete", run
        remote = run["report"]["funds"]["TESTQ"]
        assert remote["cells"] == json.loads(json.dumps(local["funds"]["TESTQ"]["cells"]))
        assert remote["fills"] == json.loads(json.dumps(local["funds"]["TESTQ"]["fills"]))
        # Downloaded once, cached under the fingerprint.
        assert (tmp_path / "cache" / "TESTQ.npz").exists()
        assert (tmp_path / "cache" / "TESTQ.fingerprint").read_text()

    def test_pausing_the_shard_hands_the_sweep_back(self, tmp_path, client, queue, fixture_bars):
        """Paused from the UI while the engine is running: the shard stops,
        the run returns to the queue with its finished configurations, and
        the shard claims nothing more until resumed."""
        started = threading.Event()
        proceed = threading.Event()

        def runner(request, report, control, bars):
            control.record_row("TESTQ", {"Grid Step": 0.005})
            started.set()
            assert proceed.wait(TIMEOUT)
            deadline = time.monotonic() + TIMEOUT
            while not control.should_stop():
                assert time.monotonic() < deadline, "the stop never arrived"
                time.sleep(0.02)
            from server.jobs import RunStopped

            raise RunStopped("paused")

        process = ShardProcess(
            "pausable",
            "http://testserver",
            cache_dir=tmp_path / "cache",
            client=TestClient(app),
            runner=runner,
            claim_wait=0.2,
            sync_interval=0.05,
            retry_seconds=0.05,
            log=lambda message: None,
        )
        thread = threading.Thread(target=process.run_forever, daemon=True)
        thread.start()
        run_id = client.post("/api/backtest/runs", json=REQUEST).json()["id"]
        assert started.wait(TIMEOUT)

        client.post("/api/backtest/shards/pausable", json={"op": "pause"})
        proceed.set()
        wait_for(lambda: queue.get(run_id).status == "queued")
        assert "paused shard pausable" in queue.get(run_id).message
        assert queue._store.load_rows(run_id) == {"TESTQ": [{"Grid Step": 0.005}]}
        wait_for(lambda: process.link.paused)

        process.request_stop()
        thread.join(TIMEOUT)
        assert not thread.is_alive()
        # Still queued: a paused shard claimed nothing more.
        assert queue.get(run_id).status == "queued"

    def test_a_version_mismatch_exits_with_2(self, tmp_path, client, monkeypatch):
        monkeypatch.setattr(shards, "_main_commit", {"commit": "0000000", "dirty": False})
        process = ShardProcess(
            "skewed",
            "http://testserver",
            cache_dir=tmp_path / "cache",
            client=TestClient(app),
            log=lambda message: None,
        )
        monkeypatch.setattr(
            "server.deployment.describe", lambda: {"build": {"commit": "1111111", "dirty": False}}
        )
        assert process.run_forever() == 2

    def test_a_second_process_with_the_same_name_retires_the_first(
        self, tmp_path, client, queue, fixture_bars
    ):
        first = ShardProcess(
            "twin",
            "http://testserver",
            cache_dir=tmp_path / "a",
            client=TestClient(app),
            claim_wait=0.2,
            sync_interval=0.05,
            retry_seconds=0.05,
            log=lambda message: None,
        )
        results: list[int] = []
        thread = threading.Thread(target=lambda: results.append(first.run_forever()), daemon=True)
        thread.start()
        wait_for(lambda: any(s["name"] == "twin" for s in queue.shards()))
        register(client, "twin", instance="someone-else")
        thread.join(TIMEOUT)
        assert results == [1]
        assert first.link.superseded


class FakeMain:
    """MainClient's shape, scripted, for the Link's own rules."""

    base_url = "http://fake"

    def __init__(self) -> None:
        self.answers: list = []
        self.synced: list = []
        self.finished: list = []
        self.lock = threading.Lock()

    def sync(self, run, progress, msg, rows):
        with self.lock:
            answer = self.answers.pop(0) if self.answers else {"paused": False, "owned": True}
        if isinstance(answer, Exception):
            raise answer
        self.synced.append((run, list(rows)))
        return {"stop": False, **answer}

    def finish(self, run_id, body):
        self.finished.append((run_id, body["outcome"]))


class TestLink:
    def _link(self, main: FakeMain) -> Link:
        link = Link(main, sync_interval=0.02, retry_seconds=0.02, log=lambda message: None)
        link.start()
        return link

    def test_rows_are_delivered_in_order_before_the_finish(self):
        main = FakeMain()
        link = self._link(main)
        link.begin("r1")
        for step in range(3):
            link.record_row("r1", "T", {"step": step})
        link.finish("r1", {"outcome": "complete"})
        assert link.wait_drained(timeout=TIMEOUT)
        link.close()
        delivered = [row["row"]["step"] for run, rows in main.synced if run == "r1" for row in rows]
        assert delivered == [0, 1, 2]
        assert main.finished == [("r1", "complete")]

    def test_a_transport_failure_keeps_the_rows_and_retries(self):
        import httpx

        main = FakeMain()
        main.answers = [httpx.ConnectError("down"), httpx.ConnectError("down")]
        link = self._link(main)
        link.begin("r1")
        link.record_row("r1", "T", {"step": 0})
        assert link.wait_drained(timeout=TIMEOUT)
        link.close()
        assert ("r1", [{"ticker": "T", "row": {"step": 0}}]) in main.synced

    def test_losing_ownership_stops_the_run_and_drops_its_rows(self):
        main = FakeMain()
        main.answers = [{"paused": False, "owned": False}]
        link = self._link(main)
        link.begin("r1")
        link.record_row("r1", "T", {"step": 0})
        link.record_row("r1", "T", {"step": 1})
        assert link.wait_drained(timeout=TIMEOUT)
        assert link.should_stop("r1")
        assert not link.owns("r1")
        link.record_row("r1", "T", {"step": 2})  # ignored once lost
        link.close()
        assert all(not rows or rows[0]["row"]["step"] == 0 for _, rows in main.synced)

    def test_a_restarted_main_server_is_detected(self):
        main = FakeMain()
        main.answers = [UnknownToMain("restarted")]
        link = self._link(main)
        link.begin("r1")
        link.record_row("r1", "T", {"step": 0})
        assert link.wait_drained(timeout=TIMEOUT)
        link.close()
        assert link.unknown
        assert link.should_stop("r1")

    def test_a_stop_asked_by_the_main_server_reaches_should_stop(self):
        main = FakeMain()
        main.answers = [{"paused": True, "owned": True, "stop": True}]
        link = self._link(main)
        link.begin("r1")
        wait_for(lambda: link.should_stop("r1"))
        link.close()
        assert link.paused


class TestRemoteBars:
    class Main:
        def __init__(self, frame, fingerprint="fp1"):
            self.frame = frame
            self.fp = fingerprint
            self.downloads = 0

        def tickers(self):
            return {"TESTQ"}

        def fingerprint(self, ticker):
            return self.fp if ticker == "TESTQ" else None

        def download_bars(self, ticker, dest):
            self.downloads += 1
            dest.write_bytes(shards.encode_bars(self.frame))
            return self.fp

    def test_downloads_once_then_reads_the_cache(self, tmp_path, frame):
        main = self.Main(frame)
        RemoteBars(main, tmp_path, log=lambda m: None).load_frame("TESTQ")
        # A fresh process (no memo) reads the disk cache.
        loaded = RemoteBars(main, tmp_path, log=lambda m: None).load_frame("TESTQ")
        assert main.downloads == 1
        assert len(loaded) == len(frame)

    def test_a_new_fingerprint_downloads_again(self, tmp_path, frame):
        main = self.Main(frame)
        bars = RemoteBars(main, tmp_path, log=lambda m: None)
        bars.load_frame("TESTQ")
        main.fp = "fp2"
        bars.load_frame("TESTQ")
        assert main.downloads == 2
        assert (tmp_path / "TESTQ.fingerprint").read_text() == "fp2"

    def test_a_corrupt_cache_is_replaced(self, tmp_path, frame):
        main = self.Main(frame)
        (tmp_path / "TESTQ.npz").write_bytes(b"not an archive")
        (tmp_path / "TESTQ.fingerprint").write_text("fp1")
        assert len(RemoteBars(main, tmp_path, log=lambda m: None).load_frame("TESTQ")) == len(frame)
        assert main.downloads == 1

    def test_two_shards_sharing_a_cache_dir_do_not_collide(self, tmp_path, frame, monkeypatch):
        """REGRESSION: both wrote "<ticker>.npz.part", and on Windows the
        loser of that race raised PermissionError out of load_frame and
        failed a whole sweep. A cache it cannot install is used where it
        landed instead."""
        main = self.Main(frame)
        bars = RemoteBars(main, tmp_path, log=lambda m: None)

        real_replace = Path.replace

        def busy(self, target):
            if self.name.endswith(".part"):
                raise PermissionError(32, "being used by another process")
            return real_replace(self, target)

        monkeypatch.setattr(Path, "replace", busy)
        loaded = bars.load_frame("TESTQ")

        assert len(loaded) == len(frame)
        # Nothing half-written is left behind for the next download.
        assert not list(tmp_path.glob("*.part"))

    def test_an_unknown_ticker_is_an_empty_frame(self, tmp_path, frame):
        empty = RemoteBars(self.Main(frame), tmp_path, log=lambda m: None).load_frame("NOPE")
        assert empty.empty and list(empty.columns) == list(shards.BAR_COLUMNS)


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("1.2.3.4", "http://1.2.3.4:8000"),
        ("1.2.3.4:9000", "http://1.2.3.4:9000"),
        ("workstation", "http://workstation:8000"),
        ("http://host:81/", "http://host:81"),
        ("https://host", "https://host"),
        ("::1", None),
        ("[::1]:8001", "http://[::1]:8001"),
        ("", None),
        ("ftp://host", None),
    ],
)
def test_main_url(given, expected):
    if expected is None:
        with pytest.raises(ValueError):
            main_url(given)
    else:
        assert main_url(given) == expected


def test_shard_refused_is_raised_for_422():
    from server.shard_client import MainClient

    response = __import__("httpx").Response(422, json={"detail": [{"msg": "bad"}]})
    with pytest.raises(ShardRefused):
        MainClient._decode(response)
