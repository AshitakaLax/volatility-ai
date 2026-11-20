"""
The nightly risk report as a session's risk overlay (docs/daily_risk_report_plan.md).

  mapping.py   a report in, a session's overlay out: pure, versioned, monotone
  baselines.py each fund's frozen baselines, the scale the mappings measure against
  inputs.py    what a mapping reads besides the report: the implied move, the
               proxy's move, the engine's own FOMC and earnings calendars
  archive.py   the trader's risk_reports/ directory, and the week's exposure cap
  control.py   apply_risk_report and clear_risk_report, as the trader applies them

engine/core/risk_report.py parses and audits a report; engine/core/risk_overlay.py
is the overlay the engine reads. Nothing here places, sizes or sells anything.
"""
