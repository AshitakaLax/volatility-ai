#!/usr/bin/env bash
# Extended-target sweep, then an annualized/regime breakdown of whatever
# it finds. Sequential -- four workers already peak near 1.7GB each.
set -u
VENV="C:/workspace/volatility-ai/.venv/Scripts/python.exe"
LOG="output/extended_$(date +%Y%m%d_%H%M).log"
say() { echo "" | tee -a "$LOG"; echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"; }

say "STEP 1/2 extended profit targets 0.05-0.30, exhaustive (120 combos)"
"$VENV" run_hf_sweep.py --config config/search_hf_targets_extended.yaml \
    --search grid --n-jobs 4 \
    --output output/search_hf_targets_extended.csv >>"$LOG" 2>&1

say "STEP 2/2 annualized + regime breakdown of the new best configurations"
"$VENV" analyze_annual.py --top 3 >>"$LOG" 2>&1

say "EXTENDED CHAIN COMPLETE"
