"""
Canonical warehouse queries.

Kept as named constants rather than f-strings assembled at the call
site so that the ASOF join in particular exists exactly once. It has
three details that are easy to get subtly wrong, and getting any of
them wrong produces a plausible-looking answer rather than an error.
"""

from __future__ import annotations

from typing import Any

# WHY EVERY CLAUSE HERE IS THE WAY IT IS
#
# ASOF LEFT JOIN, not ASOF JOIN. An inner ASOF silently DROPS an
# execution that has no bar at-or-before it. That case is real -- the
# first bar of a dataset, or a fill on a symbol whose bars were never
# ingested -- and dropping it would understate the trade count while
# looking perfectly healthy. LEFT surfaces it as a NULL row instead.
#
# b.ticker = e.ticker is an equality predicate carried alongside the
# inequality. DuckDB uses it to prune Hive partitions before the
# ordered match runs; without it the join considers every ticker's
# bars and then discards them.
#
# b.timestamp <= e.timestamp is the point-in-time guarantee: the most
# recent bar at or before the fill. Flipping it to >= would match the
# NEXT bar, which is lookahead -- the same class of bug src/ml/'s
# causal-transform rule exists to prevent, and just as silent.
#
# Both sides are TIMESTAMPTZ. Measured on DuckDB 1.5.5: casting one
# side to naive TIMESTAMP does NOT raise -- it shifts the instant by
# the session timezone and joins anyway. connection.py pins
# TimeZone='UTC' for exactly this reason; do not add a ::TIMESTAMP here.
EXECUTIONS_AT_MARKET_PRICE = """
SELECT
    e.simulation_id,
    e.lot_id,
    e.side,
    e.timestamp                                  AS execution_time,
    e.price                                      AS fill_price,
    e.qty,
    b.timestamp                                  AS bar_time,
    b.close                                      AS market_close,
    b.volume                                     AS bar_volume,
    e.price - b.close                            AS slippage_abs,
    CASE WHEN b.close > 0
         THEN (e.price - b.close) / b.close * 10000.0
    END                                          AS slippage_bps,
    e.sell_reason,
    e.profit_realized
FROM sim.trade_executions AS e
ASOF LEFT JOIN market_data.ohlcv AS b
      ON b.ticker = e.ticker
     AND b.timestamp <= e.timestamp
WHERE e.simulation_id = ?
ORDER BY e.timestamp
"""

# Same join, aggregated: how far the simulated fills sat from the bar
# they were filled against, per simulation. This is the query the ASOF
# join actually earns its keep on -- it is the cost-model validation
# that src/analysis/cost_models.py has no way to check against
# recorded executions today.
SLIPPAGE_SUMMARY = """
SELECT
    e.simulation_id,
    count(*)                                            AS executions,
    count(*) FILTER (WHERE b.timestamp IS NULL)         AS unmatched,
    avg(abs(e.price - b.close) / nullif(b.close, 0)) * 10000.0
                                                        AS mean_abs_slippage_bps,
    max(abs(e.price - b.close) / nullif(b.close, 0)) * 10000.0
                                                        AS max_abs_slippage_bps,
    max(epoch(e.timestamp - b.timestamp))               AS worst_staleness_seconds
FROM sim.trade_executions AS e
ASOF LEFT JOIN market_data.ohlcv AS b
      ON b.ticker = e.ticker
     AND b.timestamp <= e.timestamp
GROUP BY e.simulation_id
ORDER BY mean_abs_slippage_bps DESC NULLS LAST
"""

# Point-in-time universe. The whole reason assets carries active_from /
# active_through: filtering on them is what keeps a delisted fund in a
# 2016 backtest's universe instead of quietly excluding everything that
# did not survive to today.
UNIVERSE_AS_OF = """
SELECT ticker, sector, is_leveraged, leverage_ratio, active_from, active_through
FROM market_data.assets
WHERE active_from <= ?
  AND (active_through IS NULL OR active_through >= ?)
ORDER BY ticker
"""

# Events in force for a bar window, without leaking the future:
# event_timestamp is when the market LEARNED the fact.
EVENTS_IN_WINDOW = """
SELECT ticker, event_timestamp, event_type, value, source
FROM market_data.market_events
WHERE ticker = ?
  AND event_timestamp BETWEEN ? AND ?
ORDER BY event_timestamp
"""

# One external series' value as of an arbitrary instant: the most
# recent observation at or before it. This mirrors
# src/data/external_index_series.py's ExternalIndexSeries.scalar()
# exactly -- same "at-or-before" rule -- but as a set operation over
# the lake rather than a per-call Python lookup. NOTE: this is the RAW
# observation timestamp, not the publication time; for anything feeding
# a backtest use EXTERNAL_SERIES_AT_BARS below, which applies the lag.
EXTERNAL_VALUE_AT = """
SELECT x.series_key, x.timestamp AS observed_at, x.close AS value
FROM market_data.external AS x
WHERE x.series_key = ?
  AND x.timestamp <= ?
ORDER BY x.timestamp DESC
LIMIT 1
"""

# The point-in-time-correct version: one external series joined to a
# ticker's bars, matched to the value that had actually been PUBLISHED
# by each bar.
#
# WHY THE INNER SUBQUERY AND THE lag_days SHIFT
#
# A FRED macro print observed within month M is released weeks later.
# Its row in the lake is dated inside M, so an ASOF join on
# x.timestamp <= b.timestamp would hand a March bar the March CPI print
# that did not exist until mid-April -- lookahead, and silent, exactly
# what src/ml/'s causal-transform rule exists to stop. external_series
# carries lag_days per series (from the manifest); the subquery shifts
# every observation forward by it to get known_at, and the ASOF matches
# on THAT. A series with lag_days = 0 (most CBOE/Yahoo daily closes)
# is unaffected.
#
# ASOF LEFT JOIN, not inner: a bar earlier than the series' first
# published value surfaces as NULL rather than being dropped.
EXTERNAL_SERIES_AT_BARS = """
SELECT
    b.ticker,
    b.timestamp                          AS bar_time,
    b.close                              AS bar_close,
    x.observed_at,
    x.known_at,
    x.value                              AS series_value
FROM market_data.ohlcv AS b
ASOF LEFT JOIN (
    SELECT
        v.timestamp                                       AS observed_at,
        v.timestamp + (s.lag_days * INTERVAL 1 DAY)       AS known_at,
        v.close                                           AS value
    FROM market_data.external        AS v
    JOIN market_data.external_series AS s USING (series_key)
    WHERE v.series_key = ?
) AS x
  ON x.known_at <= b.timestamp
WHERE b.ticker = ?
ORDER BY b.timestamp
"""

EXTERNAL_SERIES_CATALOG = """
SELECT series_key, provider, category, description, lag_days,
       first_date, last_date, row_count
FROM market_data.external_series
ORDER BY provider, series_key
"""

TOP_SIMULATIONS = """
SELECT
    s.simulation_id,
    s.status,
    s.total_return,
    s.sharpe_ratio,
    s.max_drawdown,
    s.trade_count,
    s.execution_time_ms,
    w.algorithm,
    b.label AS broker,
    s.parameters_json ->> '$.strategy'    AS strategy,
    s.parameters_json ->  '$.grid_step'   AS grid_step,
    s.parameters_json ->  '$.profit_target' AS profit_target
FROM sim.simulations   AS s
JOIN sim.sweeps        AS w ON w.sweep_id  = s.sweep_id
JOIN sim.broker_environments AS b ON b.broker_id = w.broker_id
WHERE s.status = 'COMPLETED'
ORDER BY s.total_return DESC NULLS LAST
LIMIT ?
"""


def executions_at_market_price(con: Any, simulation_id: str):
    """Run the ASOF join for one simulation, as an Arrow-backed frame."""
    return con.execute(EXECUTIONS_AT_MARKET_PRICE, [simulation_id]).pl()


def slippage_summary(con: Any):
    return con.execute(SLIPPAGE_SUMMARY).pl()


def universe_as_of(con: Any, as_of):
    return con.execute(UNIVERSE_AS_OF, [as_of, as_of]).pl()


def top_simulations(con: Any, limit: int = 20):
    return con.execute(TOP_SIMULATIONS, [limit]).pl()


def external_value_at(con: Any, series_key: str, as_of):
    """Raw most-recent value of one series at-or-before `as_of`."""
    return con.execute(EXTERNAL_VALUE_AT, [series_key, as_of]).pl()


def external_series_at_bars(con: Any, series_key: str, ticker: str):
    """Lag-aware join of one external series onto a ticker's bars."""
    return con.execute(EXTERNAL_SERIES_AT_BARS, [series_key, ticker]).pl()


def external_series_catalog(con: Any):
    return con.execute(EXTERNAL_SERIES_CATALOG).pl()
