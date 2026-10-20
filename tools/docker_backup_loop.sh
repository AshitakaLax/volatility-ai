#!/bin/sh
# Back up the trading ledgers and the warehouse catalogs once a day, at
# VAI_BACKUP_AT (local time, TZ). The `backup` service's whole job.
#
# tools/backup_databases.py does the work: an online SQLite copy that the
# live loop keeps writing through, a DuckDB copy taken under a read-only
# handle (a sweep holding the warehouse read-write is skipped and reported,
# never torn), one timestamped archive in backups/, the oldest pruned to
# VAI_BACKUP_KEEP. With VAI_BACKUP_REMOTE (user@host) it is also copied off
# the machine over ssh -- which needs a key mounted into the container;
# see docs/DEPLOY.md, "Backups".
#
# Ledgers are found, not listed: every *.db in the mounted state volumes,
# so a second paper loop's ledger is backed up without editing this.
set -u

AT="${VAI_BACKUP_AT:-03:30}"
KEEP="${VAI_BACKUP_KEEP:-14}"
REMOTE="${VAI_BACKUP_REMOTE:-}"

stopping=""
child=""
trap 'stopping=1; [ -n "$child" ] && kill -TERM "$child" 2>/dev/null' TERM INT

# Run "$@" in the background and wait for it, through any trapped signal.
run() {
    "$@" &
    child=$!
    wait "$child"
    code=$?
    while kill -0 "$child" 2>/dev/null; do
        wait "$child"
        code=$?
    done
    child=""
    return "$code"
}

backup() {
    set --
    for db in /app/state*/*.db /app/warehouse/market_data.duckdb /app/warehouse/sim_results.duckdb; do
        [ -f "$db" ] && set -- "$@" --db "$db"
    done
    if [ "$#" -eq 0 ]; then
        echo "[backup] nothing to back up yet"
        return 0
    fi
    if [ -n "$REMOTE" ]; then
        set -- "$@" --remote-host "$REMOTE"
    else
        set -- "$@" --local-only
    fi
    run python tools/backup_databases.py "$@" --out-dir /app/backups --keep "$KEEP"
}

echo "[backup] daily at ${AT} (${TZ:-UTC}), keeping ${KEEP}, remote: ${REMOTE:-none}"
while [ -z "$stopping" ]; do
    now=$(date +%s)
    next=$(date -d "${AT}" +%s)
    [ "$next" -le "$now" ] && next=$((next + 86400))
    echo "[backup] next run $(date -d "@${next}" '+%Y-%m-%d %H:%M %Z')"
    run sleep $((next - now))
    [ -n "$stopping" ] && break
    backup || echo "[backup] FAILED with $? -- see above; trying again tomorrow"
done
echo "[backup] stopped"
