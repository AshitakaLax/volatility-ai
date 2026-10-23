#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../.."
VENV="${PY:-.venv/bin/python}"
LOG="output/frontier_$(date +%Y%m%d_%H%M).log"
say() { echo "" | tee -a "$LOG"; echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"; }
say "STEP 1/3 target x lot-size frontier, exhaustive (64 combos)"
"$VENV" -m research.run_hf_sweep --config config/search_hf_targets_frontier.yaml \
    --search grid --n-jobs 4 --output output/search_hf_targets_frontier.csv >>"$LOG" 2>&1
say "STEP 2/3 annualized + regime breakdown, best under a 50% drawdown cap"
"$VENV" -m research.analysis.analyze_annual --cap 50 --top 2 >>"$LOG" 2>&1
say "STEP 3/3 annualized + regime breakdown, best unconstrained"
"$VENV" -m research.analysis.analyze_annual --top 2 >>"$LOG" 2>&1
say "FRONTIER CHAIN COMPLETE"
