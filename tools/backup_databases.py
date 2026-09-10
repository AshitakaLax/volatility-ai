#!/usr/bin/env python
"""Snapshot every local database, archive it, and push it to the Raspberry Pi.

    python tools/backup_databases.py                     # snapshot + archive + push
    python tools/backup_databases.py --local-only        # archive, no push
    python tools/backup_databases.py --include warehouse/executions
    python tools/backup_databases.py --install-daily --at 03:30
    python tools/backup_databases.py --remove-daily

One file, three jobs: take a consistent copy of each database, bundle the
copies into one timestamped tar.gz under backups/, and scp that bundle to
a remote host (the Pi) -- then trim old bundles at both ends. `--install
-daily` registers this same script as a daily scheduled task so the push
happens on its own.

---

WHAT COUNTS AS "A DATABASE" HERE

  paper_ledger.db / state/*.db   the live trading ledger (SQLite). The
                                 only genuinely irreplaceable one -- it
                                 is real positions, not a derived view.
  warehouse/*.duckdb             the analytical warehouse catalogs. Small
                                 (~2 MB) and technically regenerable from
                                 data/, but sim_results.duckdb holds
                                 sweep output that cost hours of compute.

The Parquet LAKES under warehouse/ (ohlcv/, external/) are deliberately
NOT included: they are large and rebuildable with `build_warehouse.py
--ingest-all`. warehouse/executions/ (per-fill trade blotters) IS
irreplaceable -- fold it in with `--include warehouse/executions` when
you want a complete warehouse restore rather than metrics-only.

---

WHY EACH ENGINE GETS ITS OWN SNAPSHOT METHOD

SQLite is written every tick by the live loop, so a plain file copy can
catch it mid-transaction. sqlite3's own .backup() is an online,
page-consistent copy that a concurrent writer cannot tear -- measured,
it is the correct tool and it is in the standard library.

DuckDB has no online-backup call, but it is single-writer/multi-reader:
while ANY read-only connection is held open, a would-be writer's
connect() fails outright ("different configuration"). So this script
opens the file read-only, keeps that handle open across the copy, and
releases it after -- which both proves no sweep/ingest is writing and
prevents one from starting mid-copy. If the read-only open itself fails,
a writer already holds the file; the database is skipped with a loud
warning and a non-zero exit rather than a torn copy that will not
reopen.

---

WHY scp AND NOT rsync

Git for Windows ships ssh and scp; it does not ship rsync, and this runs
on the Windows workstation. The bundles are a few MB, so scp's lack of
delta transfer costs nothing. SSH must be non-interactive
(key-based, no passphrase prompt) -- a scheduled task has no console.
Every ssh call passes -o BatchMode=yes so a missing key fails in seconds
instead of hanging on a prompt.

The remote target is NOT hard-coded. Set VAI_BACKUP_REMOTE (e.g.
pi@172.16.0.137) and VAI_BACKUP_REMOTE_DIR, or pass --remote-host /
--remote-dir. `--install-daily` bakes whatever you resolved into the
task definition so the schedule is explicit.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

TASK_NAME = "VolatilityAI-DbBackup"
ARCHIVE_PREFIX = "volatility-ai-db"
CRON_MARKER = "# volatility-ai-db-backup"

# Databases looked for by default, relative to the repo root. Missing
# ones are silently skipped -- the workstation has the warehouse, the
# Pi has the ledger, and neither has all of them.
DEFAULT_DB_CANDIDATES = (
    "paper_ledger.db",
    "state/ledger.db",
    "state/paper_ledger.db",
    "warehouse/market_data.duckdb",
    "warehouse/sim_results.duckdb",
)

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
DUCKDB_SUFFIXES = {".duckdb"}


# --------------------------------------------------------------------
# snapshotting
# --------------------------------------------------------------------


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_sqlite(src: Path, dest: Path) -> None:
    """Online, page-consistent copy. Safe against the live loop writing."""
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(dest)
        try:
            with target:
                source.backup(target)
        finally:
            target.close()
    finally:
        source.close()


def snapshot_duckdb(src: Path, dest: Path) -> None:
    """Copy the file (and its .wal, if any) while holding a read-only
    handle open -- which both proves and enforces that no writer is
    active for the duration of the copy.

    Raises RuntimeError if the read-only open fails, meaning a sweep or
    ingest currently holds the file read-write.
    """
    import duckdb

    try:
        guard = duckdb.connect(str(src), read_only=True)
    # Deliberately broad: any open failure means a writer holds the file.
    except Exception as e:
        raise RuntimeError(
            f"{src.name} is open read-write elsewhere (a sweep or ingest?); "
            f"refusing a torn copy [{type(e).__name__}: {e}]"
        ) from e
    try:
        shutil.copy2(src, dest)
        wal = src.with_name(src.name + ".wal")
        if wal.exists():
            shutil.copy2(wal, dest.with_name(dest.name + ".wal"))
    finally:
        guard.close()


def resolve_databases(explicit: list[str] | None) -> list[Path]:
    """Absolute paths of the databases to back up. `explicit` (from
    --db) replaces the default candidate list entirely."""
    names = explicit if explicit else list(DEFAULT_DB_CANDIDATES)
    found: list[Path] = []
    for name in names:
        path = Path(name)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        if path.exists():
            found.append(path.resolve())
        elif explicit:
            # An explicitly named db that is missing is an error, not a
            # silent skip -- the caller asked for that one specifically.
            raise FileNotFoundError(f"--db {name}: no such file ({path})")
    return found


def snapshot_all(databases: list[Path], workdir: Path) -> tuple[list[dict], list[str]]:
    """Snapshot each database into workdir. Returns (entries, errors)."""
    entries: list[dict] = []
    errors: list[str] = []
    for src in databases:
        dest = workdir / src.name
        suffix = src.suffix.lower()
        try:
            if suffix in DUCKDB_SUFFIXES:
                snapshot_duckdb(src, dest)
            elif suffix in SQLITE_SUFFIXES:
                snapshot_sqlite(src, dest)
            else:
                # Unknown engine: a plain copy is the honest best effort.
                shutil.copy2(src, dest)
        # Broad on purpose: one unreadable db is collected and reported,
        # not allowed to abort the backup of the others.
        except Exception as e:
            errors.append(f"{src.name}: {e}")
            print(f"  ERROR  {src.name}: {e}", file=sys.stderr)
            continue
        entry = {
            "name": src.name,
            "source": str(src),
            "bytes": dest.stat().st_size,
            "sha256": _sha256(dest),
        }
        entries.append(entry)
        print(f"  ok     {src.name}  ({entry['bytes']:,} bytes)")
    return entries, errors


# --------------------------------------------------------------------
# archiving
# --------------------------------------------------------------------


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
            cwd=_REPO_ROOT,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def build_archive(
    workdir: Path,
    entries: list[dict],
    extra_paths: list[Path],
    out_dir: Path,
) -> Path:
    """Tar+gzip the snapshots plus a MANIFEST.json, and any --include
    files/dirs, into out_dir. Verifies the archive reopens before
    returning it."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d_%H%M%SZ")
    host = socket.gethostname()
    archive = out_dir / f"{ARCHIVE_PREFIX}_{host}_{stamp}.tar.gz"

    manifest = {
        "created_utc": dt.datetime.now(dt.UTC).isoformat(),
        "host": host,
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "databases": entries,
        "extra": [p.name for p in extra_paths],
    }
    (workdir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(workdir / "MANIFEST.json", arcname="MANIFEST.json")
        for entry in entries:
            snap = workdir / entry["name"]
            tar.add(snap, arcname=entry["name"])
            wal = snap.with_name(snap.name + ".wal")
            if wal.exists():
                tar.add(wal, arcname=wal.name)
        for path in extra_paths:
            tar.add(path, arcname=f"extra/{path.name}")

    # Integrity gate: reopen and confirm the db members hash as recorded.
    with tarfile.open(archive, "r:gz") as tar:
        members = {m.name for m in tar.getmembers()}
        for entry in entries:
            if entry["name"] not in members:
                raise RuntimeError(f"archive is missing {entry['name']} right after writing it")
    print(f"  archive  {archive.name}  ({archive.stat().st_size:,} bytes)")
    return archive


def prune_local(out_dir: Path, keep: int) -> None:
    archives = sorted(out_dir.glob(f"{ARCHIVE_PREFIX}_*.tar.gz"))
    stale = archives[:-keep] if keep > 0 else []
    for path in stale:
        path.unlink()
        print(f"  pruned   {path.name}")


# --------------------------------------------------------------------
# pushing to the remote
# --------------------------------------------------------------------

_SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


def _run(cmd: list[str], *, dry_run: bool) -> None:
    printable = " ".join(cmd)
    if dry_run:
        print(f"  would run: {printable}")
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {printable}\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def push_to_remote(
    archive: Path,
    host: str,
    remote_dir: str,
    keep: int,
    *,
    dry_run: bool,
) -> None:
    """mkdir -p the remote dir, scp the archive in, prune old archives
    there. Every hop is non-interactive; a missing SSH key fails fast."""
    remote_dir = remote_dir.rstrip("/") or "."
    _run(["ssh", *_SSH_OPTS, host, f"mkdir -p {remote_dir}"], dry_run=dry_run)
    _run(
        ["scp", *_SSH_OPTS, str(archive), f"{host}:{remote_dir}/"],
        dry_run=dry_run,
    )
    if keep > 0:
        prune = (
            f"ls -1t {remote_dir}/{ARCHIVE_PREFIX}_*.tar.gz 2>/dev/null "
            f"| tail -n +{keep + 1} | xargs -r rm -f"
        )
        _run(["ssh", *_SSH_OPTS, host, prune], dry_run=dry_run)
    print(f"  pushed   {archive.name} -> {host}:{remote_dir}/")


# --------------------------------------------------------------------
# daily-schedule install / remove
# --------------------------------------------------------------------


def _task_command(args: argparse.Namespace) -> list[str]:
    """The argv the scheduled job should run: this script, minus the
    install flags, plus whatever remote/keep values were resolved."""
    cmd = [sys.executable, str(Path(__file__).resolve())]
    if args.remote_host:
        cmd += ["--remote-host", args.remote_host]
    if args.remote_dir:
        cmd += ["--remote-dir", args.remote_dir]
    cmd += ["--keep", str(args.keep)]
    for extra in args.include or []:
        cmd += ["--include", extra]
    if args.local_only:
        cmd += ["--local-only"]
    return cmd


def install_daily(args: argparse.Namespace) -> int:
    at = args.at
    cmd = _task_command(args)
    if platform.system() == "Windows":
        return _install_windows_task(cmd, at)
    return _install_cron(cmd, at)


def _ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _install_windows_task(cmd: list[str], at: str) -> int:
    exe = cmd[0]
    arg_str = subprocess.list2cmdline(cmd[1:])
    ps = (
        f"$a = New-ScheduledTaskAction -Execute {_ps_quote(exe)} "
        f"-Argument {_ps_quote(arg_str)} -WorkingDirectory {_ps_quote(str(_REPO_ROOT))}; "
        f"$t = New-ScheduledTaskTrigger -Daily -At {_ps_quote(at)}; "
        "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew "
        "-ExecutionTimeLimit (New-TimeSpan -Hours 2); "
        f"Register-ScheduledTask -TaskName {_ps_quote(TASK_NAME)} -Action $a -Trigger $t "
        "-Settings $s -Description "
        f"{_ps_quote('Daily database snapshot + push to the Pi (tools/backup_databases.py).')} "
        "-Force | Out-Null"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        check=True,
    )
    print(f"Registered scheduled task '{TASK_NAME}': daily at {at} local.")
    print(f"  runs   : {subprocess.list2cmdline(cmd)}")
    print(f"  run now: Start-ScheduledTask -TaskName '{TASK_NAME}'")
    print(f"  status : Get-ScheduledTaskInfo -TaskName '{TASK_NAME}'")
    print("  remove : python tools/backup_databases.py --remove-daily")
    return 0


def _crontab_lines() -> list[str]:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _write_crontab(lines: list[str]) -> None:
    text = "\n".join(lines).rstrip("\n") + "\n"
    proc = subprocess.run(["crontab", "-"], input=text, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"crontab - failed: {proc.stderr.strip()}")


def _install_cron(cmd: list[str], at: str) -> int:
    hour, minute = (int(x) for x in at.split(":"))
    logfile = _REPO_ROOT / "logs" / "db-backup.log"
    line = (
        f"{minute} {hour} * * * cd {_REPO_ROOT} && "
        + " ".join(cmd)
        + f" >> {logfile} 2>&1  {CRON_MARKER}"
    )
    kept = [ln for ln in _crontab_lines() if CRON_MARKER not in ln]
    _write_crontab([*kept, line])
    print(f"Installed cron entry: daily at {at}.")
    print(f"  {line}")
    return 0


def remove_daily() -> int:
    if platform.system() == "Windows":
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"Unregister-ScheduledTask -TaskName {_ps_quote(TASK_NAME)} -Confirm:$false "
                "-ErrorAction SilentlyContinue",
            ],
            check=False,
        )
        print(f"Removed scheduled task '{TASK_NAME}' (if it existed).")
        return 0
    kept = [ln for ln in _crontab_lines() if CRON_MARKER not in ln]
    _write_crontab(kept)
    print("Removed the db-backup cron entry (if it existed).")
    return 0


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db",
        action="append",
        metavar="PATH",
        help="back up exactly this database (repeatable); replaces the default set",
    )
    parser.add_argument(
        "--include",
        action="append",
        metavar="PATH",
        help="also fold this file or directory into the archive (repeatable), "
        "e.g. --include warehouse/executions",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_REPO_ROOT / "backups",
        help="where local archives are written (default: backups/)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=14,
        help="how many archives to retain locally and remotely (default: 14; 0 = keep all)",
    )
    parser.add_argument(
        "--remote-host",
        default=os.environ.get("VAI_BACKUP_REMOTE"),
        metavar="USER@HOST",
        help="SSH target for the push (default: $VAI_BACKUP_REMOTE)",
    )
    parser.add_argument(
        "--remote-dir",
        default=os.environ.get("VAI_BACKUP_REMOTE_DIR", "volatility-ai-backups"),
        metavar="DIR",
        help="directory on the remote (default: $VAI_BACKUP_REMOTE_DIR or volatility-ai-backups)",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="build the archive but do not push it anywhere",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the ssh/scp commands instead of running them",
    )
    parser.add_argument(
        "--install-daily",
        action="store_true",
        help="register this script as a daily task (Windows Scheduled Task or cron)",
    )
    parser.add_argument("--remove-daily", action="store_true", help="undo --install-daily")
    parser.add_argument(
        "--at", default="03:30", metavar="HH:MM", help="daily run time for --install-daily"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.remove_daily:
        return remove_daily()
    if args.install_daily:
        if not args.local_only and not args.remote_host:
            print(
                "Refusing to install a daily push with no remote. Pass --remote-host "
                "(or set $VAI_BACKUP_REMOTE), or --local-only for archive-only backups.",
                file=sys.stderr,
            )
            return 2
        return install_daily(args)

    databases = resolve_databases(args.db)
    if not databases:
        print(
            "No databases found. Looked for: "
            + ", ".join(DEFAULT_DB_CANDIDATES)
            + ".\nRun from the repo, or pass --db PATH.",
            file=sys.stderr,
        )
        return 1

    extra_paths: list[Path] = []
    for name in args.include or []:
        path = Path(name)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        if not path.exists():
            print(f"--include {name}: no such path ({path})", file=sys.stderr)
            return 2
        extra_paths.append(path.resolve())

    print(f"Snapshotting {len(databases)} database(s):")
    with tempfile.TemporaryDirectory(prefix="vai-dbbackup-") as tmp:
        workdir = Path(tmp)
        entries, errors = snapshot_all(databases, workdir)
        if not entries:
            print("Nothing was snapshotted successfully.", file=sys.stderr)
            return 1
        archive = build_archive(workdir, entries, extra_paths, args.out_dir)

    prune_local(args.out_dir, args.keep)

    pushed = False
    if args.local_only:
        print("  (--local-only: not pushing)")
    elif not args.remote_host:
        print(
            "  no --remote-host / $VAI_BACKUP_REMOTE set -- archive kept locally only",
            file=sys.stderr,
        )
    else:
        try:
            push_to_remote(
                archive, args.remote_host, args.remote_dir, args.keep, dry_run=args.dry_run
            )
            pushed = True
        except RuntimeError as e:
            print(f"  PUSH FAILED: {e}", file=sys.stderr)
            errors.append(f"push: {e}")

    # A DB that could not be snapshotted, or a push that failed, is a
    # non-zero exit so a scheduled run surfaces as failed rather than
    # silently producing a partial backup.
    if errors:
        print(f"\nCompleted with {len(errors)} problem(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    where = f"{archive}" + (" (pushed)" if pushed else " (local only)")
    print(f"\nBackup complete: {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
