#!/usr/bin/env bash
set -u

# One-axis controlled A/B for implied_vol_exponent. See
# config/probe_implied_vol.yaml for why this signal earned a sweep when
# four calendar candidates did not.
#
# The 0.0 arm is the control and must reproduce the champion result
# exactly (38.605871% CAGR / 82.367648% max DD). If it does not, the
# wiring is not the no-op it claims and no other arm means anything.
#
# 6 combinations. Memory note as in the other run_*.sh here: check for
# other running python processes first.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
IV="data/VIXY_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"
LOG="output/probe_implied_vol_$(date +%Y%m%d_%H%M).log"

echo "===== PROBE IMPLIED VOL =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

python -u run_hf_sweep.py \
    --config config/probe_implied_vol.yaml \
    --data "$DATA" \
    --implied-vol "$IV" \
    --search grid --n-jobs 1 \
    --output output/probe_implied_vol.csv \
    >> "$LOG" 2>&1

echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== PROBE IMPLIED VOL COMPLETE =====" >> "$LOG"
