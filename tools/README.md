# tools/

One-off data-preparation scripts. These are **not** part of the trading
or backtesting path — nothing in `src/` imports them, and a run never
calls them. They exist to *produce* inputs that the rest of the project
then consumes.

They live here rather than in the repository root because the root is
for things you run routinely (`cli.py`, `run_hf_sweep.py`,
`analyze_annual.py`, `resample_uniform.py`, `analyze_har.py`,
`fidelity_recon.py`). These you run once, or once a year.

| Script | Produces | Notes |
|---|---|---|
| `build_earnings_calendar.py` | `data/earnings_releases_derived.csv` | **Load-bearing for a fresh checkout.** `data/` is git-ignored, so this file is absent after a clone and `src/event_calendar.py` needs it. Makes network requests; takes a while. |
| `pull_extended_history.py` | extended-hours minute datasets under `data/` | Bulk historical download. |
| `screen_instruments.py` | a ranked instrument shortlist | Exploratory; run when choosing what to trade. |

## Running them

Both forms work:

    python tools/build_earnings_calendar.py
    python -m tools.pull_extended_history

`pull_extended_history.py` and `screen_instruments.py` import from
`src/`, and Python puts the *script's* directory on `sys.path[0]` rather
than the working directory — so `python tools/x.py` would fail on
`from src...` while `python -m tools.x` succeeded. Each carries a small
repo-root bootstrap so neither invocation surprises anyone. It is the
same pattern `tests/fixtures/regression_baseline.py` uses, and the
reason is recorded at the top of each file rather than left to be
rediscovered.

All three guard their entry point with `if __name__ == "__main__"`, so
importing one is side-effect-free. That matters more than it sounds:
`build_earnings_calendar.py` starts issuing network requests as soon as
its `main()` runs, and it has no `--help`.
