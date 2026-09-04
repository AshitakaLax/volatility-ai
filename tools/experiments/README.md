# One-off experiment runners

Each of these drove a single investigation and was kept for the record,
not for reuse. They lived in the repository root until the root had
fifteen of them and it was no longer obvious which scripts were entry
points and which were archaeology.

**These are not maintained.** They pin parameter values, dataset paths,
and config names as they were on the day they ran, so a script here may
well not run today — a config it names may have been renamed, and a
strategy it sweeps may take different parameters. That is fine, and it
is why they are here rather than in `tools/`: their value is as a record
of what was actually run to produce a number quoted somewhere, not as
something to invoke.

If you need to re-run one, read it first and expect to update paths.

The three chain scripts still in the repository root
(`run_extended_chain.sh`, `run_frontier_chain.sh`,
`run_overnight_chain.sh`) stayed there deliberately: `README.md`
documents them as things a person is meant to run.

| script | what it was investigating |
|---|---|
| `run_2strategy_retry2.sh` | strategy comparison, second retry |
| `run_4strategy_retry.sh` | four-way strategy comparison |
| `run_5strategy_comparison.sh` | five-way strategy comparison |
| `run_lotcap_test.sh` | lot-count cap |
| `run_probe_cap_tight.sh` | a tighter exposure cap |
| `run_probe_dd_exposure.sh` | drawdown vs exposure |
| `run_probe_dd_throttle.sh` | throttling on drawdown |
| `run_probe_exposure_cap.sh` | exposure cap sweep |
| `run_probe_implied_vol.sh` | implied-volatility input |
| `run_probe_rsp.sh` | RSP as a signal |
| `run_rsp_resample_after_sweep.sh` | RSP resampling after a sweep |
| `run_trailing_v3.sh` | trailing profit target, third revision |
