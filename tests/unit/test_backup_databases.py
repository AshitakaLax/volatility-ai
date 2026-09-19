"""tools/backup_databases.py -- snapshot correctness, retention, guards.

The push path (ssh/scp) is not exercised here: it needs a real remote
and non-interactive keys. What is pinned is everything that decides
whether a restored archive is actually usable.
"""

from __future__ import annotations

import sqlite3
import tarfile

import pytest

from tools.backup_databases import (
    build_archive,
    extract_archive,
    prune_local,
    resolve_databases,
    restore_databases,
    snapshot_all,
    snapshot_sqlite,
    verify_archive,
)


def _make_sqlite(path, rows: int) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE lots (id INTEGER PRIMARY KEY, qty REAL)")
    con.executemany("INSERT INTO lots (qty) VALUES (?)", [(float(i),) for i in range(rows)])
    con.commit()
    con.close()


def test_sqlite_snapshot_is_a_faithful_copy(tmp_path):
    src = tmp_path / "ledger.db"
    _make_sqlite(src, 25)
    dest = tmp_path / "snap.db"
    snapshot_sqlite(src, dest)

    con = sqlite3.connect(dest)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT count(*) FROM lots").fetchone()[0] == 25
    con.close()


def test_sqlite_snapshot_survives_a_concurrent_writer(tmp_path):
    """The live loop writes every tick; a plain file copy could tear.
    .backup() cannot."""
    src = tmp_path / "ledger.db"
    _make_sqlite(src, 10)
    writer = sqlite3.connect(src)
    writer.execute("BEGIN")
    writer.execute("INSERT INTO lots (qty) VALUES (999)")  # uncommitted
    try:
        dest = tmp_path / "snap.db"
        snapshot_sqlite(src, dest)
    finally:
        writer.rollback()
        writer.close()

    con = sqlite3.connect(dest)
    # The uncommitted row must not be in the snapshot.
    assert con.execute("SELECT count(*) FROM lots").fetchone()[0] == 10
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    con.close()


def test_duckdb_snapshot_round_trips(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    from tools.backup_databases import snapshot_duckdb

    src = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(src))
    con.execute("CREATE TABLE t AS SELECT range AS n FROM range(100)")
    con.close()

    dest = tmp_path / "snap.duckdb"
    snapshot_duckdb(src, dest)

    v = duckdb.connect(str(dest), read_only=True)
    assert v.execute("SELECT count(*), sum(n) FROM t").fetchone() == (100, 4950)
    v.close()


def test_duckdb_snapshot_refuses_while_a_writer_holds_the_file(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    from tools.backup_databases import snapshot_duckdb

    src = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(src))
    con.execute("CREATE TABLE t (n INTEGER)")
    # con stays open read-write
    try:
        with pytest.raises(RuntimeError, match="read-write elsewhere"):
            snapshot_duckdb(src, tmp_path / "snap.duckdb")
    finally:
        con.close()


def test_resolve_databases_skips_absent_defaults_but_errors_on_explicit(tmp_path, monkeypatch):
    import tools.backup_databases as mod

    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
    _make_sqlite(tmp_path / "paper_ledger.db", 1)
    # default candidate list: only the one that exists comes back
    found = resolve_databases(None)
    assert [p.name for p in found] == ["paper_ledger.db"]
    # an explicitly named missing db is a hard error
    with pytest.raises(FileNotFoundError):
        resolve_databases(["state/nope.db"])


def test_archive_carries_a_manifest_and_reopens(tmp_path):
    src = tmp_path / "ledger.db"
    _make_sqlite(src, 5)
    work = tmp_path / "work"
    work.mkdir()
    entries, errors = snapshot_all([src], work)
    assert not errors and len(entries) == 1

    out = tmp_path / "backups"
    archive = build_archive(work, entries, [], out)
    assert archive.exists()

    with tarfile.open(archive) as tar:
        names = tar.getnames()
        assert "MANIFEST.json" in names
        assert "ledger.db" in names
        import json

        manifest = json.loads(tar.extractfile("MANIFEST.json").read())
    assert manifest["databases"][0]["name"] == "ledger.db"
    assert manifest["databases"][0]["sha256"]


def test_prune_local_keeps_the_newest_n(tmp_path):
    for stamp in ("2026-01-01_000000Z", "2026-01-02_000000Z", "2026-01-03_000000Z"):
        (tmp_path / f"volatility-ai-db_host_{stamp}.tar.gz").write_bytes(b"x")
    # an unrelated file must be left alone
    (tmp_path / "notes.txt").write_text("keep me")

    prune_local(tmp_path, keep=2)

    remaining = sorted(p.name for p in tmp_path.glob("volatility-ai-db_*.tar.gz"))
    assert remaining == [
        "volatility-ai-db_host_2026-01-02_000000Z.tar.gz",
        "volatility-ai-db_host_2026-01-03_000000Z.tar.gz",
    ]
    assert (tmp_path / "notes.txt").exists()


def test_prune_local_keep_zero_is_a_noop(tmp_path):
    (tmp_path / "volatility-ai-db_host_2026-01-01_000000Z.tar.gz").write_bytes(b"x")
    prune_local(tmp_path, keep=0)
    assert list(tmp_path.glob("volatility-ai-db_*.tar.gz"))


# --------------------------------------------------------------------
# restore: extract / verify / restore_databases
# --------------------------------------------------------------------


def _make_archive(tmp_path, rows=5):
    """A real backup archive built the same way build_archive makes one,
    for the restore-side tests below to extract/verify/restore."""
    src = tmp_path / "ledger.db"
    _make_sqlite(src, rows)
    work = tmp_path / "work"
    work.mkdir()
    entries, errors = snapshot_all([src], work)
    assert not errors
    out = tmp_path / "backups"
    return build_archive(work, entries, [], out)


def test_extract_archive_returns_the_manifest(tmp_path):
    archive = _make_archive(tmp_path)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    assert manifest["databases"][0]["name"] == "ledger.db"
    assert (extract_dir / "ledger.db").exists()
    assert (extract_dir / "MANIFEST.json").exists()


def test_extract_archive_rejects_a_non_backup_tarball(tmp_path):
    fake = tmp_path / "fake.tar.gz"
    import tarfile

    with tarfile.open(fake, "w:gz") as tar:
        info = tarfile.TarInfo("hello.txt")
        data = b"not a backup"
        info.size = len(data)
        import io

        tar.addfile(info, io.BytesIO(data))

    with pytest.raises(RuntimeError, match=r"MANIFEST\.json"):
        extract_archive(fake, tmp_path / "extracted")


def test_verify_archive_passes_on_an_untampered_extraction(tmp_path):
    archive = _make_archive(tmp_path)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    assert verify_archive(manifest, extract_dir) == []


def test_verify_archive_catches_a_corrupted_snapshot(tmp_path):
    archive = _make_archive(tmp_path)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    (extract_dir / "ledger.db").write_bytes(b"tampered")

    problems = verify_archive(manifest, extract_dir)
    assert len(problems) == 1
    assert "sha256 mismatch" in problems[0]


def test_verify_archive_catches_a_missing_entry(tmp_path):
    archive = _make_archive(tmp_path)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    (extract_dir / "ledger.db").unlink()

    problems = verify_archive(manifest, extract_dir)
    assert len(problems) == 1
    assert "missing from archive" in problems[0]


def test_restore_databases_writes_into_target_dir_and_keeps_a_pre_restore_copy(tmp_path):
    archive = _make_archive(tmp_path, rows=5)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    target = tmp_path / "restored"
    target.mkdir()
    existing = target / "ledger.db"
    existing.write_bytes(b"old contents that should be preserved, not deleted")

    results = restore_databases(manifest, extract_dir, target, dry_run=False)

    assert results == [
        {"name": "ledger.db", "status": "restored", "dest": str(target / "ledger.db")}
    ]
    con = sqlite3.connect(target / "ledger.db")
    assert con.execute("SELECT count(*) FROM lots").fetchone()[0] == 5
    con.close()

    pre_restore = list(target.glob("ledger.db.pre-restore-*"))
    assert len(pre_restore) == 1
    assert pre_restore[0].read_bytes() == b"old contents that should be preserved, not deleted"


def test_restore_databases_dry_run_changes_nothing(tmp_path):
    archive = _make_archive(tmp_path)
    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    target = tmp_path / "restored"
    target.mkdir()
    existing = target / "ledger.db"
    existing.write_bytes(b"untouched")

    results = restore_databases(manifest, extract_dir, target, dry_run=True)

    assert results[0]["status"] == "dry-run"
    assert existing.read_bytes() == b"untouched"
    assert not list(target.glob("*.pre-restore-*"))


def test_restore_databases_skips_a_duckdb_open_read_write_elsewhere(tmp_path):
    duckdb = pytest.importorskip("duckdb")

    src = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(src))
    con.execute("CREATE TABLE t AS SELECT range AS n FROM range(5)")
    con.close()
    work = tmp_path / "work"
    work.mkdir()
    entries, errors = snapshot_all([src], work)
    assert not errors
    archive = build_archive(work, entries, [], tmp_path / "backups")

    extract_dir = tmp_path / "extracted"
    manifest = extract_archive(archive, extract_dir)

    target = tmp_path / "restored"
    target.mkdir()
    dest = target / "wh.duckdb"
    import shutil

    shutil.copy2(src, dest)
    holder = duckdb.connect(str(dest))  # stays open read-write
    try:
        results = restore_databases(manifest, extract_dir, target, dry_run=False)
    finally:
        holder.close()

    assert len(results) == 1
    assert results[0]["name"] == "wh.duckdb"
    assert results[0]["status"] == "skipped"
    assert not list(target.glob("*.pre-restore-*"))
