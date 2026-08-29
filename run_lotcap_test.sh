#!/usr/bin/env bash
set -u

# Enhancement 4/5: isolate whether max_concurrent_lots=6000 is the
# binding constraint behind every sweep result to date. Waits for
# retune_uniform_extended_v2's sweep to finish first -- both are
# CPU/memory-heavy on a machine with the live trading process also
# running, and this box measured only ~2.6-3.2GB free while v2 ran.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/lotcap_test_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== LOT CAP TEST =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

# run_hf_sweep.py only writes its output CSV on completion (or on the
# periodic checkpoint it takes mid-run for a multi-hour sweep -- see
# README's "Running the HF parameter sweeps" section), so this file's
# presence is a more reliable completion signal on this environment
# than a process-name match: this Git Bash install has no pgrep, and
# `ps aux` here does not expose command-line arguments to grep against
# (verified: every python process shows only the bare interpreter
# path, config filenames included).
V2_OUTPUT="output/retune_uniform_extended_v2.csv"
if [ ! -f "$V2_OUTPUT" ]; then
    say "Waiting for retune_uniform_extended_v2 to write $V2_OUTPUT (memory contention otherwise)..."
    while [ ! -f "$V2_OUTPUT" ]; do
        sleep 60
    done
    # The sweep driver writes the file, prints a results table, THEN
    # exits -- give it a few seconds' margin so this doesn't race a
    # still-running process for the same CPU/memory it's trying to wait for.
    sleep 10
fi

for cap in 6000 12000 20000 unlimited; do
    say "cap=$cap"
    python -u run_hf_sweep.py \
        --config "config/lotcap_test_${cap}.yaml" \
        --data "$DATA" \
        --search grid --n-jobs 1 \
        --output "output/lotcap_test_${cap}.csv" \
        >> "$LOG" 2>&1
done

say "===== LOT CAP TEST COMPLETE ====="
