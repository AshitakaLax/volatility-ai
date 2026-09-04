"""
One trading loop per state store.

Two live loops on one account is not a degraded mode -- it is duplicate
orders, and DuplicateOrderGuard provably cannot catch it: its
decision_id is derived from symbol, side and bar timestamp, so both
loops compute the SAME id on the same bar and each believes it is the
one submitting it.

This nearly shipped. A manually started loop was running while a
scheduled supervisor waited to start another at the open, both pointed
at paper_ledger.db, and nothing in the system would have objected.
"""

from __future__ import annotations

import os

import pytest

from src.process_lock import LockHeldError, StateStoreLock, _process_alive


def test_a_second_loop_on_the_same_store_is_refused(tmp_path):
    db = str(tmp_path / "live.db")
    first = StateStoreLock(db).acquire()
    try:
        with pytest.raises(LockHeldError, match="DUPLICATE"):
            StateStoreLock(db).acquire()
    finally:
        first.release()


def test_the_refusal_names_the_holding_pid(tmp_path):
    """An operator needs to know WHICH process to look at, not that
    'something' holds it."""
    db = str(tmp_path / "live.db")
    first = StateStoreLock(db).acquire()
    try:
        with pytest.raises(LockHeldError) as caught:
            StateStoreLock(db).acquire()
        assert str(os.getpid()) in str(caught.value)
    finally:
        first.release()


def test_two_different_stores_are_two_deployments(tmp_path):
    """The lock is keyed on the STORE, because the store is what two
    processes would actually corrupt. Separate stores are separate
    deployments and must both run."""
    a = StateStoreLock(str(tmp_path / "a.db")).acquire()
    b = StateStoreLock(str(tmp_path / "b.db")).acquire()
    a.release()
    b.release()


def test_releasing_lets_the_next_process_in(tmp_path):
    db = str(tmp_path / "live.db")
    StateStoreLock(db).acquire().release()
    StateStoreLock(db).acquire().release()


# --- staleness: a crash must not wedge the system ---


def test_a_lock_from_a_dead_process_is_taken_over(tmp_path):
    """A machine that loses power mid-session leaves a lock behind. If
    that blocked every future start, the lock would cause more downtime
    than the problem it prevents -- and an operator who must delete a
    file to trade will delete it reflexively, including on the day it
    was right."""
    db = str(tmp_path / "live.db")
    lock_file = tmp_path / "live.db.lock"
    lock_file.write_text("999999999", encoding="utf-8")  # a pid that cannot exist

    taken = StateStoreLock(db).acquire()
    assert lock_file.read_text(encoding="utf-8") == str(os.getpid())
    taken.release()


@pytest.mark.parametrize("junk", ["", "   ", "not-a-pid", "\x00"])
def test_an_unreadable_lock_is_treated_as_stale_not_as_a_holder(tmp_path, junk):
    """An empty file is exactly what a crash mid-write leaves. Refusing
    forever over it is the wedge this class exists to avoid."""
    db = str(tmp_path / "live.db")
    (tmp_path / "live.db.lock").write_text(junk, encoding="utf-8")
    StateStoreLock(db).acquire().release()


def test_liveness_errs_toward_alive(tmp_path):
    """A lock wrongly judged stale lets a second loop trade; one wrongly
    judged live only asks a human to look. Those costs are not
    symmetric, so the check leans one way on purpose."""
    assert _process_alive(os.getpid()) is True
    assert _process_alive(0) is False
    assert _process_alive(-1) is False


def test_release_does_not_remove_a_lock_this_process_does_not_own(tmp_path):
    """Otherwise a stale-takeover race would have one process deleting
    the other's live claim on the way out."""
    db = str(tmp_path / "live.db")
    lock = StateStoreLock(db)
    lock.acquire()
    (tmp_path / "live.db.lock").write_text("999999999", encoding="utf-8")
    lock.release()
    assert (tmp_path / "live.db.lock").exists(), "someone else's lock survived"


def test_it_works_as_a_context_manager(tmp_path):
    db = str(tmp_path / "live.db")
    with StateStoreLock(db), pytest.raises(LockHeldError):
        StateStoreLock(db).acquire()
    StateStoreLock(db).acquire().release()


def test_release_is_idempotent(tmp_path):
    lock = StateStoreLock(str(tmp_path / "live.db")).acquire()
    lock.release()
    lock.release()


# --- wiring ---


def test_cmd_live_takes_the_lock_before_opening_the_store():
    """Ordering matters: a refusal must cost nothing and leave no
    partial state behind."""
    import inspect
    from pathlib import Path

    source = Path("cli.py").read_text(encoding="utf-8")
    body = source[source.index("def cmd_live") :]
    assert body.index("lock.acquire()") < body.index("store = LedgerStore(db_path)")
    assert inspect  # keep the import meaningful if the check above changes


def test_every_exit_path_from_cmd_live_releases_the_lock():
    """Three ways out: not-ready, --check-only, and the trading loop.
    The last releases in a `finally`, because a loop that raises must
    not leave a lock naming a PID that is about to not exist."""
    from pathlib import Path

    source = Path("cli.py").read_text(encoding="utf-8")
    body = source[source.index("def cmd_live") : source.index("def _run_trading_loop")]
    assert body.count("lock.release()") == 3
    assert "finally:" in body
