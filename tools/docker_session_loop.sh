#!/bin/sh
# Run one trading session, wait, run the next. The container's whole job.
#
# WHY A LOOP AND NOT `restart: unless-stopped` ALONE
#
# The supervisor is built to run ONE session and exit -- it asks Alpaca
# when the market opens, sleeps until then, trades until the close, and
# returns. Docker's restart policy would happily start it again, which
# is right on a trading day and a hot loop on every other one: on a
# Saturday the supervisor works out that the next open is more than
# max-wait-hours away and exits in about two seconds, so a bare restart
# policy spins it hundreds of times an hour for a day and a half.
#
# So the wait lives here, explicitly, where its length is visible and
# tunable rather than buried in a daemon's backoff heuristics.
#
# WHY IT NEVER EXITS ON A FAILING SESSION
#
# A crashed session must not take the deployment down until someone
# notices -- tomorrow's session is still worth running. The exit code is
# logged and the loop continues. `restart: unless-stopped` in compose
# then covers only the cases this script cannot: the container being
# killed, the daemon restarting, the host rebooting.
#
# HOW `docker stop` REACHES THE TRADING LOOP
#
# docker stop signals PID 1 -- this shell -- and a shell forwards nothing
# by itself, so the loop used to be killed mid-tick when the grace period
# ran out. The trap below passes SIGTERM to the supervisor, which stops
# the trading loop the way it does at the close (it finishes its tick and
# settles what is in flight), then exits. The children run in the
# background so the trap can fire while they do; compose's
# stop_grace_period leaves the settle window room.
set -u

CONFIG="${VAI_CONFIG:-/app/config/paper_aggressive.yaml}"
STATE_DB="${VAI_STATE_DB:-/app/state/paper_ledger.db}"
IDLE_SECONDS="${VAI_IDLE_SECONDS:-900}"
# How often a missing config, or one a session failed on, is looked at again.
CONFIG_POLL_SECONDS="${VAI_CONFIG_POLL_SECONDS:-30}"

echo "[loop] config=${CONFIG}"
echo "[loop] state=${STATE_DB}"
echo "[loop] idle between sessions: ${IDLE_SECONDS}s"

# Fail loudly and immediately if the timezone database is missing.
# Every session decision reads through ZoneInfo("America/New_York"), and
# without tzdata that raises at import -- far enough from here that the
# traceback does not obviously mean "the image is missing a package".
python -c "from zoneinfo import ZoneInfo; ZoneInfo('America/New_York')" || {
    echo "[loop] FATAL: no IANA time-zone database in this image."
    echo "[loop] Install tzdata (it is in requirements.txt and the Dockerfile)."
    exit 1
}

stopping=""
child=""
trap 'stopping=1; echo "[loop] stop requested"; [ -n "$child" ] && kill -TERM "$child" 2>/dev/null' TERM INT

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

# What the config holds, cheaply compared: its checksum, or "missing".
config_stamp() {
    cksum "${CONFIG}" 2>/dev/null || echo missing
}

# WHY IT WAITS FOR A MISSING CONFIG
#
# A deployment can be started before its config is written. The Fidelity
# one's names the account, so it is never committed; it is written by hand
# on the host. The supervisor used to fail on the missing file with a
# traceback every IDLE_SECONDS, which reads like a container restarting
# over and over. So the loop says once what it is waiting for, and starts
# as soon as the file is there: config/ is the host's directory, mounted
# in, so the file appears in here the moment it is saved.
wait_for_config() {
    [ -f "${CONFIG}" ] && return 0
    echo "[loop] ${CONFIG} does not exist yet; waiting for it (looking every ${CONFIG_POLL_SECONDS}s)."
    echo "[loop] Write it on the host: docs/DEPLOY.md says what goes in it."
    while [ -z "$stopping" ] && [ ! -f "${CONFIG}" ]; do
        run sleep "${CONFIG_POLL_SECONDS}"
    done
    [ -z "$stopping" ] && echo "[loop] ${CONFIG} is there; starting."
    return 0
}

# After a failed session: wait IDLE_SECONDS, but go again as soon as the
# config changes. A config being written for the first time fails on its
# mistakes, and the fix should not then wait a quarter of an hour.
wait_after_failure() {
    stamp=$(config_stamp)
    deadline=$(($(date +%s) + IDLE_SECONDS))
    while [ -z "$stopping" ] && [ "$(date +%s)" -lt "$deadline" ]; do
        run sleep "${CONFIG_POLL_SECONDS}"
        if [ "$(config_stamp)" != "$stamp" ]; then
            echo "[loop] ${CONFIG} changed; trying again now"
            return 0
        fi
    done
    return 0
}

# The wait between sessions happens INSIDE the supervisor (--linger), so the
# Live page's commands -- pause, disable, switch -- are answered during it,
# with $VAI_CONTROL_DIR naming where they arrive. Only a failed run waits out
# here (wait_after_failure), so a supervisor that cannot start does not spin.
while [ -z "$stopping" ]; do
    wait_for_config
    [ -n "$stopping" ] && break
    echo "[loop] === starting session at $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
    run python tools/market_hours_supervisor.py \
        --config "${CONFIG}" \
        --state-db "${STATE_DB}" \
        --linger "${IDLE_SECONDS}"
    code=$?
    [ -n "$stopping" ] && break
    if [ "$code" -ne 0 ]; then
        echo "[loop] supervisor exited with ${code}; trying again in ${IDLE_SECONDS}s, or as soon as ${CONFIG} changes"
        wait_after_failure
    fi
done
echo "[loop] stopped"
