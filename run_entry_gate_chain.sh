#!/usr/bin/env bash
# Entry-gate probes, one after another, then the year-by-year breakdown.
#
# Sequential on purpose, like the other run_*_chain.sh scripts: --n-jobs
# workers already peak near 1.7GB each at the champion's settings.
#
# Uses `python -m` from the repo root, which works without PYTHONPATH --
# invoking research/run_hf_sweep.py by path does not.
#
#   bash run_entry_gate_chain.sh             # all five probes
#   PY=.venv/bin/python bash run_entry_gate_chain.sh
#   N_JOBS=2 bash run_entry_gate_chain.sh
#   FILL=causal bash run_entry_gate_chain.sh          # see execution.intrabar_fill
set -u
cd "$(dirname "$0")"

if [ -z "${PY:-}" ]; then
    if [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
    elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
    else PY=python; fi
fi
N_JOBS="${N_JOBS:-4}"
FILL="${FILL:-level}"   # level = how every recorded result was booked
mkdir -p output
LOG="output/entry_gates_${FILL}_$(date +%Y%m%d_%H%M).log"
say() { echo "" | tee -a "$LOG"; echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"; }

# Control first: if it does not reproduce best_known_2026-08-24.yaml
# (25.38% CAGR, 45.57% max drawdown), nothing after it is interpretable.
PROBES="control dual_thrust opening_range prior_low shooting_star intraday_momentum rsi_head_shoulders"
n=0; total=$(echo $PROBES | wc -w)
for probe in $PROBES; do
    n=$((n + 1))
    say "STEP $n/$((total + 1))  probe_entry_gate_$probe"
    "$PY" -m research.run_hf_sweep \
        --config "config/probe_entry_gate_$probe.yaml" \
        --search grid --n-jobs "$N_JOBS" --intrabar-fill "$FILL" \
        --output "output/probe_entry_gate_${probe}_${FILL}.csv" >>"$LOG" 2>&1
done

say "STEP $((total + 1))/$((total + 1))  year-by-year, best under a 50% drawdown cap"
# Reads EVERY csv in output/, not only these five -- the top rows may be
# earlier sweeps. That is the comparison you want; each row prints its
# parameters, so a gated row shows breakdown_gate= / pattern_gate=.
"$PY" -m research.analysis.analyze_annual --cap 50 --top 5 >>"$LOG" 2>&1
say "ENTRY GATE CHAIN COMPLETE -- see $LOG"
