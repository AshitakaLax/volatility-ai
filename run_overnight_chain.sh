#!/usr/bin/env bash
# Overnight chain. Waits for the in-flight sweep to finish, then runs a
# sequence of experiments one at a time.
#
# STRICTLY SEQUENTIAL, and that is the point. Four workers already peak
# near 1.7GB of commit each on this 15GB machine; an earlier sweep was
# killed at trial 28 of 250 because other work was run alongside it.
# Nothing here overlaps with anything else.
#
# Ordered by value, so a truncated run still delivers the important
# parts:
#   1. annual breakdown of today's best configs   (the actual question)
#   2. wide profit targets, exhaustive            (never-tested axis)
#   3. wide profit targets, no-loss guard off     (paired comparison)
#   4. annual breakdown of whatever 2/3 found
#   5. volume-inclusive parameter sweep           (truncatable)
set -u

VENV="C:/workspace/volatility-ai/.venv/Scripts/python.exe"
LOG="output/overnight_$(date +%Y%m%d_%H%M).log"
IN_FLIGHT="$1"   # task output file of the sweep already running

say() { echo "" | tee -a "$LOG"; echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"; }

say "waiting for the in-flight sweep to finish"
# "evaluations in" is printed only on completion. Cap the wait at 6h so a
# dead sweep cannot hang the chain forever.
for _ in $(seq 1 360); do
    grep -q "evaluations in" "$IN_FLIGHT" 2>/dev/null && break
    sleep 60
done
say "in-flight sweep done (or timed out); starting chain"

say "STEP 1/5 annual breakdown of current best configurations"
"$VENV" analyze_annual.py --top 3 >>"$LOG" 2>&1

say "STEP 2/5 wide profit targets, exhaustive grid, guard ON"
"$VENV" run_hf_sweep.py --config config/search_hf_wide_targets.yaml \
    --search grid --n-jobs 4 \
    --output output/search_hf_wide_targets.csv >>"$LOG" 2>&1

say "STEP 3/5 wide profit targets, exhaustive grid, guard OFF"
"$VENV" run_hf_sweep.py --config config/search_hf_wide_targets_noguard.yaml \
    --search grid --n-jobs 4 \
    --output output/search_hf_wide_targets_noguard.csv >>"$LOG" 2>&1

say "STEP 4/5 annual breakdown, re-run now that steps 2-3 have landed"
"$VENV" analyze_annual.py --top 3 >>"$LOG" 2>&1

say "STEP 5/5 volume-inclusive sweep"
"$VENV" run_hf_sweep.py --config config/search_hf_volume_sweep.yaml \
    --search random --trials 220 --n-jobs 4 --max-drawdown 55 \
    --output output/search_hf_volume_sweep.csv >>"$LOG" 2>&1

say "CHAIN COMPLETE"
