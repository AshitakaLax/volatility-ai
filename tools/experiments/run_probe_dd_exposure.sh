#!/usr/bin/env bash
set -u

# Probe: the RiskManager-level drawdown exposure throttle
# (dd_exposure_start/full/floor_pct, src/risk_manager.py). See
# config/probe_dd_exposure_1.yaml for the full rationale -- this
# replaces the earlier per-strategy dd_throttle attempt
# (config/probe_dd_throttle.yaml), which measured as having no real
# effect because it shrank a fixed-dollar lot size rather than an
# equity-relative exposure cap.
#
# 4 configs, ONE combination each (single grid step, single target),
# run sequentially. ~2000-2100s each based on prior runs of this exact
# strategy/data combination -> ETA ~2.3h total.
#
# Same memory-safety note as the other run_*.sh scripts here: check for
# other running python processes before launching, and do not run this
# alongside another heavy sweep.

DATA="data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv"
LOG="output/probe_dd_exposure_$(date +%Y%m%d_%H%M).log"

echo "===== PROBE DD EXPOSURE (risk-manager level) =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"

for n in 1 2 3 4; do
    echo "" >> "$LOG"
    echo "--- config/probe_dd_exposure_${n}.yaml ---" >> "$LOG"
    python -u run_hf_sweep.py \
        --config "config/probe_dd_exposure_${n}.yaml" \
        --data "$DATA" \
        --search grid --n-jobs 1 \
        --output "output/probe_dd_exposure_${n}.csv" \
        >> "$LOG" 2>&1
done

echo "" >> "$LOG"
echo "### $(date '+%H:%M:%S')  ===== PROBE DD EXPOSURE COMPLETE =====" >> "$LOG"
