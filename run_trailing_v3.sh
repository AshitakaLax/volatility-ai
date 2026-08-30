#!/usr/bin/env bash
set -u

# Re-tune v3: the trailing sweep, run against the corrected
# TrailingTargetPolicy (floor as a bound, not an attractor). See
# config/retune_trailing_v3.yaml for the full history -- this is the
# third attempt, and the first two produced results that looked fine and
# measured nothing.
#
# 12 combinations, ~1400-9700s each depending on trade count.
#
# NOTE ON CONCURRENCY: this box has measured as low as ~1.9GB free with
# one heavy sweep plus the live trading process running, and starting a
# second sweep alongside an unfinished one has already caused one real
# incident (see run_lotcap_test.sh). Do not run this while another sweep
# is active. There is no gate here because nothing is queued ahead of it
# -- check first.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/retune_trailing_v3_$(date +%Y%m%d_%H%M).log"

echo "===== RETUNE TRAILING V3 =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

python -u run_hf_sweep.py \
    --config config/retune_trailing_v3.yaml \
    --data "$DATA" \
    --search grid --n-jobs 1 \
    --output output/retune_trailing_v3.csv \
    >> "$LOG" 2>&1

echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== RETUNE TRAILING V3 COMPLETE =====" >> "$LOG"
