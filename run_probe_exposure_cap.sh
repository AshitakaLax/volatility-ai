#!/usr/bin/env bash
set -u

# Probe: the static max_total_exposure cap, never once turned on in
# this repo (null in all 30+ configs). See
# config/probe_exposure_cap_30.yaml for the full rationale -- briefly,
# the champion config's worst calendar year (-78.96%) is the same
# number as TQQQ buy-and-hold's 2022 (-79.09%), meaning the strategy
# offers essentially no downside protection in its worst year, and
# capital held as cash is the most direct fix available.
#
# 4 configs, ONE combination each, run sequentially. ~2000-2100s each
# based on prior runs of this exact strategy/data pair -> ETA ~2.3h.
#
# GATED on the dd_exposure probe finishing first. Both are CPU/memory
# heavy and this box has measured as low as ~1.9GB free with two
# sweeps overlapping -- which has already caused one real incident
# (see run_lotcap_test.sh's own comment for the details).
#
# Gating on the LOG's final marker, not the output CSV's existence:
# run_hf_sweep.py checkpoints its CSV every 10 combos mid-run with no
# accompanying log line, so the file can exist hours before a sweep
# actually finishes. That exact mistake caused the incident above. The
# marker below is written once, by run_probe_dd_exposure.sh, only after
# its final config returns.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/probe_exposure_cap_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== PROBE EXPOSURE CAP =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

DD_LOG="output/probe_dd_exposure_20260831_0652.log"
DD_DONE_MARKER="===== PROBE DD EXPOSURE COMPLETE ====="
if ! grep -qF "$DD_DONE_MARKER" "$DD_LOG" 2>/dev/null; then
    say "Waiting for the dd_exposure probe to finish (checking $DD_LOG)..."
    while ! grep -qF "$DD_DONE_MARKER" "$DD_LOG" 2>/dev/null; do
        sleep 60
    done
    sleep 10
fi

for cap in 30 50 70 90; do
    say "max_total_exposure=0.${cap}"
    python -u run_hf_sweep.py \
        --config "config/probe_exposure_cap_${cap}.yaml" \
        --data "$DATA" \
        --search grid --n-jobs 1 \
        --output "output/probe_exposure_cap_${cap}.csv" \
        >> "$LOG" 2>&1
done

say "===== PROBE EXPOSURE CAP COMPLETE ====="
