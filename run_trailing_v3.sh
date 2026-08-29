#!/usr/bin/env bash
set -u

# Re-tune v3: corrected trailing-target sweep. See
# config/retune_trailing_v3_target*.yaml for the confound this fixes
# (trail_min_profit_target=0.10 in v2 sat below every swept profit_target,
# so every lot converged to the same floor regardless of its original
# target). Split into one config per target, each with a floor scaled to
# that target instead of one shared absolute floor.
#
# Waits for run_lotcap_test.sh to finish first -- same reasoning as that
# script's own gate on v2: this box has measured as low as ~1.9-2.6GB free
# with one heavy sweep plus the live trading process running, and running
# two heavy sweeps at once already caused a real incident once (see
# run_lotcap_test.sh's comment). Gating on the log's one-time final line,
# not the CSV's existence, for the same reason documented there.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/retune_trailing_v3_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== RETUNE TRAILING V3 =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

LOTCAP_LOG="output/lotcap_test_20260829_0951.log"
LOTCAP_DONE_MARKER="===== LOT CAP TEST COMPLETE ====="
if ! grep -qF "$LOTCAP_DONE_MARKER" "$LOTCAP_LOG" 2>/dev/null; then
    say "Waiting for run_lotcap_test.sh to finish (checking $LOTCAP_LOG for completion)..."
    while ! grep -qF "$LOTCAP_DONE_MARKER" "$LOTCAP_LOG" 2>/dev/null; do
        sleep 60
    done
    sleep 10
fi

for target in 030 050 075 100; do
    say "target=0.$target"
    python -u run_hf_sweep.py \
        --config "config/retune_trailing_v3_target${target}.yaml" \
        --data "$DATA" \
        --search grid --n-jobs 1 \
        --output "output/retune_trailing_v3_target${target}.csv" \
        >> "$LOG" 2>&1
done

say "===== RETUNE TRAILING V3 COMPLETE ====="
