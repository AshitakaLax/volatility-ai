#!/usr/bin/env bash
set -u

# Probe: does the new dd_throttle_start/full/floor lever
# (src/high_frequency_sizing.py) help, hurt, or do nothing? See
# config/probe_dd_throttle.yaml for the full rationale.
#
# 12 combinations, ~2000-2100s each based on the smoketest combo
# (start=0.20, full=0.65, floor=0.0 -> 2067s, 38.605179% CAGR --
# essentially indistinguishable from the untrailed baseline's
# 38.605871%). ETA ~6.9h total.
#
# Same memory-safety note as run_trailing_v3.sh: check for other
# running python processes before launching this, and do not run it
# alongside another heavy sweep.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/probe_dd_throttle_$(date +%Y%m%d_%H%M).log"

echo "===== PROBE DD THROTTLE =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

python -u run_hf_sweep.py \
    --config config/probe_dd_throttle.yaml \
    --data "$DATA" \
    --search grid --n-jobs 1 \
    --output output/probe_dd_throttle.csv \
    >> "$LOG" 2>&1

echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== PROBE DD THROTTLE COMPLETE =====" >> "$LOG"
