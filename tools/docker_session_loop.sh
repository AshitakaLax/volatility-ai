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
# killed, the daemon restarting, the Pi rebooting.
set -u

CONFIG="${VAI_CONFIG:-/app/config/paper_aggressive.yaml}"
STATE_DB="${VAI_STATE_DB:-/app/state/paper_ledger.db}"
IDLE_SECONDS="${VAI_IDLE_SECONDS:-900}"

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

while true; do
    echo "[loop] === starting session at $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
    python tools/market_hours_supervisor.py \
        --config "${CONFIG}" \
        --state-db "${STATE_DB}"
    code=$?
    echo "[loop] supervisor exited with ${code}; sleeping ${IDLE_SECONDS}s"
    sleep "${IDLE_SECONDS}"
done
