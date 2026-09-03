#!/usr/bin/env bash
set -u

# First RSP sweep. See config/probe_rsp_scaled.yaml for why every
# parameter differs from the TQQQ champion -- briefly, TQQQ moves 4-6x
# more per bar, so the grid step and profit target are scaled down, and
# RSP's extended-hours grid is 60.9% fabricated bars against 6.1% for
# regular hours, so this runs on the RTH-uniform dataset at 390
# bars/day rather than 960.
#
# 12 combinations on a 1.04M-bar dataset (41% the size of the TQQQ
# extuniform file), so expect materially less than the ~2000s/combo
# those runs took -- though trade count, not bar count, dominates.
#
# Memory note, as in the other run_*.sh here: check for other running
# python processes first. Two heavy sweeps overlapping has caused a real
# incident on this box (see run_lotcap_test.sh).

DATA="data/RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv"
LOG="output/probe_rsp_$(date +%Y%m%d_%H%M).log"

echo "===== PROBE RSP (scaled parameters) =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

python -u run_hf_sweep.py \
    --config config/probe_rsp_scaled.yaml \
    --data "$DATA" \
    --search grid --n-jobs 1 \
    --output output/probe_rsp_scaled.csv \
    >> "$LOG" 2>&1

echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== PROBE RSP COMPLETE =====" >> "$LOG"
