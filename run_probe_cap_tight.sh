#!/usr/bin/env bash
set -u
# Tight exposure caps, bracketing a -25% worst calendar year.
#
# The measured curve stops at cap=0.30 (worst year -38.51%), and a
# linear fit over caps <= 0.70 puts -25% near cap 0.085 -- but that is a
# long extrapolation below everything measured, and the relationship
# flattens at the high end so it plausibly bends at the low end too.
# These four measure it instead.
#
# Now ~2 min/combo rather than ~33, after today's optimisations.
DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/probe_cap_tight_$(date +%Y%m%d_%H%M).log"
echo "===== TIGHT EXPOSURE CAPS =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"
for cap in 10 15 20 25; do
    echo "" >> "$LOG"; echo "### $(date '+%H:%M:%S')  max_total_exposure=0.${cap}" >> "$LOG"
    python -u run_hf_sweep.py --config "config/probe_exposure_cap_${cap}.yaml" \
        --data "$DATA" --search grid --n-jobs 1 \
        --output "output/probe_exposure_cap_${cap}.csv" >> "$LOG" 2>&1
done
echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== TIGHT EXPOSURE CAPS COMPLETE =====" >> "$LOG"
