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

# CORRECTED (this script's first version checked for the OUTPUT CSV's
# existence, which was wrong and caused a real incident: run_hf_sweep.py
# checkpoints that file every 10 combos mid-run -- see its own `done %
# 10 == 0` block -- with no accompanying log line, so the file existed
# hours before the sweep actually finished. This script then started
# its first combo while v2 still had 6 of 16 left, taking free memory
# from 2.6GB to 1.9GB alongside the live trading process. Caught by
# checking memory directly, not by a test -- there is no automated test
# for "does this script's gate actually gate.")
#
# The real, provably-once signal is run_hf_sweep.py's own final line,
# printed exactly once (run_hf_sweep.py:403, `print(f"Wrote {args.output}")`)
# after its main loop is fully exhausted -- never at a mid-run
# checkpoint. Grepping the LOG for this, not the CSV's existence.
V2_LOG="output/retune_uniform_extended_v2_20260828_2223.log"
V2_DONE_MARKER="Wrote output/retune_uniform_extended_v2.csv"
if ! grep -qF "$V2_DONE_MARKER" "$V2_LOG" 2>/dev/null; then
    say "Waiting for retune_uniform_extended_v2 to finish (checking $V2_LOG for completion)..."
    while ! grep -qF "$V2_DONE_MARKER" "$V2_LOG" 2>/dev/null; do
        sleep 60
    done
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
