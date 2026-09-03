#!/usr/bin/env bash
set -u

# Build the uniform-minute RSP dataset, but only once the exposure-cap
# sweep has finished. Resampling builds a ~2.6M-row frame, and this box
# has measured as low as ~1.9GB free with two heavy jobs overlapping --
# which has already caused one real incident (see run_lotcap_test.sh).
#
# Gating on the LOG's final marker, not the output CSV's existence:
# run_hf_sweep.py checkpoints its CSV mid-run with no accompanying log
# line, so the file can exist well before a sweep actually finishes.
# That exact mistake caused the incident above. The marker below is
# written once, by run_probe_exposure_cap.sh, only after its final
# config returns.

IN="data/RSP_1Min_sip_all_ext_2016-01-01_2026-08-30.csv"
LOG="output/rsp_resample_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== RSP UNIFORM RESAMPLE =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

SWEEP_LOG="output/probe_exposure_cap_20260831_0728.log"
SWEEP_DONE_MARKER="===== PROBE EXPOSURE CAP COMPLETE ====="
if ! grep -qF "$SWEEP_DONE_MARKER" "$SWEEP_LOG" 2>/dev/null; then
    say "Waiting for the exposure-cap sweep to finish (checking $SWEEP_LOG)..."
    while ! grep -qF "$SWEEP_DONE_MARKER" "$SWEEP_LOG" 2>/dev/null; do
        sleep 60
    done
    sleep 10
fi

say "Resampling $IN to a uniform 04:00-20:00 grid (960 bars/session)"
python -u resample_uniform.py --input "$IN" >> "$LOG" 2>&1
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
    say "===== RSP UNIFORM RESAMPLE FAILED (exit $STATUS) ====="
    exit "$STATUS"
fi

say "===== RSP UNIFORM RESAMPLE COMPLETE ====="
