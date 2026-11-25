"""
The pre-market forecast generator, ported into this repository: free market
data in, one nightly / pre-market risk report out, in the schema the Live
page's RiskReportPanel takes (engine/core/risk_report.py).

  generator.py      the pipeline and the report (start here)
  market_data.py    Yahoo chart API and Cboe daily index files, over HTTP
  market_inputs.py  the overnight inputs' pure calculations
  model.py          Chronos-2 (optional, requirements-dl.txt) or the
                    historical baseline
  scenarios.py      daily quantiles -> correlated paths -> binned horizons

Served by server/forecast_generator.py and the web UI's Forecast tab. It
writes nothing: a report is kept only when the page's Check sends it to
server/risk_forecasts.py.
"""
