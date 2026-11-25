"""The ported pre-market forecast generator (research/forecast_generator/),
offline: a fake market source with synthetic bars stands in for Yahoo and
Cboe, a fake pipeline for Chronos-2, and the clock is injected. Every report
it makes must pass engine/core/risk_report.py's audit -- the same parser the
Live page's Check and the forecast database use."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.risk_report import DEGRADED, MAX_REPORT_BYTES, canonical_json, parse_report
from engine.core.trading_calendar import EASTERN, previous_session
from research.forecast_generator import generator, model
from research.forecast_generator.generator import ForecastRefused, generate, rounded_horizon
from research.forecast_generator.market_data import (
    MarketData,
    MarketDataUnavailable,
    parse_cboe_daily_csv,
    parse_yahoo_daily,
    parse_yahoo_minutes,
)
from research.forecast_generator.market_inputs import overnight_futures_change
from research.forecast_generator.scenarios import QUANTILE_LEVELS
from research.risk_overlay.mapping import MIN_CONFIDENCE

# Tuesday 2026-11-24 04:20 ET: a pre-market run for that session.
PRE_MARKET = datetime(2026, 11, 24, 9, 20, tzinfo=UTC)
SESSION = date(2026, 11, 24)
BASE = date(2026, 11, 23)


def sessions_through(last: date, count: int) -> list[date]:
    days = [last]
    while len(days) < count:
        days.append(previous_session(days[-1]))
    return days[::-1]


def daily_frame(days: list[date], start: float, vol: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = start * np.exp(np.cumsum(rng.normal(0.0004, vol, len(days))))
    open_ = close * np.exp(rng.normal(0, vol / 3, len(days)))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, vol / 2, len(days))))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, vol / 2, len(days))))
    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": rng.integers(1e6, 5e6, len(days)).astype(float),
        },
        index=pd.DatetimeIndex([pd.Timestamp(d) for d in days]),
    )


def minute_frame(start: datetime, minutes: int, price: float, step: float = 0.0) -> pd.DataFrame:
    index = pd.DatetimeIndex([start + timedelta(minutes=i) for i in range(minutes)])
    closes = price + step * np.arange(minutes)
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes + 0.05,
            "Low": closes - 0.05,
            "Close": closes,
            "Volume": np.full(minutes, 100.0),
        },
        index=index,
    )


class FakeMarket:
    """Synthetic bars for every ticker the generator asks for."""

    def __init__(self, last: date = BASE, sessions: int = 1500) -> None:
        days = sessions_through(last, sessions)
        self.days = days
        self._daily = {
            "TQQQ": daily_frame(days, 20.0, 0.035, 1),
            "QQQ": daily_frame(days, 300.0, 0.012, 2),
            "SPY": daily_frame(days, 450.0, 0.010, 3),
            "NQ=F": daily_frame(days, 20000.0, 0.012, 4),
            "^VIX": daily_frame(days, 18.0, 0.05, 5),
            "^VXN": daily_frame(days, 22.0, 0.05, 6),
            "^TNX": daily_frame(days, 4.2, 0.01, 7),
            "DX-Y.NYB": daily_frame(days, 104.0, 0.004, 8),
            "CL=F": daily_frame(days, 75.0, 0.02, 9),
        }
        close_et = datetime.combine(last, datetime.min.time(), tzinfo=EASTERN).replace(
            hour=15, minute=55
        )
        overnight = datetime.combine(SESSION, datetime.min.time(), tzinfo=EASTERN).replace(hour=4)
        self._minutes = {
            # 20,000 at the close, 20,100 by 04:19: +0.5%.
            "NQ=F": pd.concat(
                [minute_frame(close_et, 5, 20000.0), minute_frame(overnight, 20, 20100.0)]
            ),
            "^VIX": minute_frame(overnight.replace(hour=3, minute=15), 50, 21.5),
            "TQQQ": minute_frame(overnight, 20, 50.0, step=0.01),
        }
        self._cboe = {
            name: pd.Series(np.linspace(low, high, 300), index=sessions_through(last, 300))
            for name, low, high in (
                ("VIX9D", 14.0, 20.0),
                ("VIX3M", 17.0, 21.0),
                ("VXN", 15.0, 30.0),
            )
        }
        self.calls: list[str] = []

    def daily(self, ticker: str) -> pd.DataFrame:
        self.calls.append(f"daily:{ticker}")
        if ticker not in self._daily:
            raise MarketDataUnavailable(f"no {ticker}")
        return self._daily[ticker].copy()

    def minutes(self, ticker: str) -> pd.DataFrame:
        self.calls.append(f"minutes:{ticker}")
        return self._minutes.get(ticker, pd.DataFrame()).copy()

    def cboe(self, symbol: str) -> pd.Series:
        self.calls.append(f"cboe:{symbol}")
        if symbol not in self._cboe:
            raise MarketDataUnavailable(f"no {symbol}")
        return self._cboe[symbol].copy()


class FakeChronos:
    """predict_quantiles in Chronos-2's shape: a list of (variates, steps, 9)."""

    model_prediction_length = 64

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def predict_quantiles(
        self, inputs, prediction_length, quantile_levels, context_length, limit_prediction_length
    ):
        self.calls.append(
            {
                "inputs": inputs,
                "prediction_length": prediction_length,
                "context_length": context_length,
            }
        )
        row = np.asarray([-4.0, -2.5, -1.4, -0.6, 0.1, 0.8, 1.6, 2.7, 4.2])
        return [np.tile(row, (1, prediction_length, 1))], None


def bootstrap(**overrides):
    return generate(
        "TQQQ", "bootstrap", now=PRE_MARKET, data=FakeMarket(), simulations=2000, **overrides
    )


# --------------------------------------------------------------------
# The report


def test_a_pre_market_report_passes_the_audit_and_is_for_that_session():
    made = bootstrap()
    audit = parse_report(made.report)
    assert audit.ok, audit.to_dict()["errors"]
    assert audit.report.session == SESSION
    assert made.report["target_session"] == "2026-11-24"
    assert made.audit["ok"] is True and made.audit["session"] == "2026-11-24"
    assert made.audit["sha256"] == audit.report.sha256
    assert made.report["schema_version"] == "1.2.0"
    assert len(canonical_json(made.report).encode("utf-8")) <= MAX_REPORT_BYTES


def test_an_evening_report_is_for_the_next_session():
    # Monday 20:00 ET, after the close: for Tuesday, anchored to Monday.
    evening = datetime(2026, 11, 24, 1, 0, tzinfo=UTC)
    made = generate("TQQQ", "bootstrap", now=evening, data=FakeMarket(), simulations=2000)
    assert parse_report(made.report).report.session == SESSION
    assert made.snapshot["base_session_date"] == "2026-11-23"
    # No pre-market tape to read in the evening, and none reported missing.
    assert made.snapshot["pre_market_or_latest_price"] is None
    assert "pre_market_or_latest_price" not in made.snapshot["missing_inputs"]


def test_every_horizon_sums_to_one_with_a_chained_cdf():
    made = bootstrap()
    for name, horizon in made.report["horizons"].items():
        total = (
            horizon["underflow_prob"]
            + sum(b["prob"] for b in horizon["bins"])
            + horizon["overflow_prob"]
        )
        assert total == pytest.approx(1.0, abs=1e-9), name
        running = horizon["underflow_prob"]
        for entry in horizon["bins"]:
            running += entry["prob"]
            assert entry["cdf"] == pytest.approx(running, abs=1e-9)
        q = horizon["summary"]["quantiles_pct"]
        assert q["p01"] <= q["p05"] <= q["p25"] <= q["p75"] <= q["p95"] <= q["p99"]
        assert horizon["summary"]["expected_shortfall_5pct"] <= q["p05"]
        # Paths compound log returns: no simple return below -100%.
        assert q["p01"] >= -100.0


def test_the_bins_scale_with_leverage():
    made = bootstrap()
    assert made.report["horizons"]["tomorrow"]["bin_width_pct"] == 1.5
    assert made.report["horizons"]["next_year"]["bin_width_pct"] == 15.0


def test_a_rerun_for_the_same_session_reproduces_itself():
    assert bootstrap().report["horizons"] == bootstrap().report["horizons"]


def test_position_sizing_stays_off():
    signals = bootstrap().report["execution_signals"]
    assert signals["kelly_fraction_cap"] == 0.0
    assert signals["suggested_strategy_weights"]["cash_defensive"] == 1.0
    assert signals["expected_1d_move_pct"] > 0


def test_the_bootstrap_engine_says_so_in_the_report():
    made = bootstrap()
    assert made.report["model"].startswith("historical-bootstrap")
    assert made.diagnostics["engine"] == "bootstrap"


# --------------------------------------------------------------------
# The snapshot: the overnight inputs


def test_the_overnight_inputs_are_read_with_where_and_when():
    snapshot = bootstrap().snapshot
    assert snapshot["overnight_futures_change_pct"] == pytest.approx(0.5)
    assert snapshot["vix_overnight_level"] == pytest.approx(21.5)
    assert snapshot["vix9d_level"] == pytest.approx(20.0)
    assert snapshot["vix3m_level"] == pytest.approx(21.0)
    assert snapshot["iv_rank_pct"] == pytest.approx(100.0)
    # The 04:00-04:05 window, fully elapsed at 04:20.
    assert snapshot["premarket_open_4am"] == pytest.approx(50.0)
    assert snapshot["premarket_window_change_pct"] == pytest.approx((50.04 / 50.0 - 1) * 100)
    fields = {o["field"]: o for o in snapshot["input_observations"]}
    assert fields["overnight_futures_change_pct"]["kind"] == "intraday_bar"
    assert fields["overnight_futures_change_pct"]["observed_at"] == "2026-11-24T09:19:00Z"
    assert fields["overnight_futures_change_pct"]["reference_observed_at"] == "2026-11-23T20:59:00Z"
    assert fields["vix9d_level"] == {
        "field": "vix9d_level",
        "source": "cboe_daily_csv",
        "ticker": "VIX9D",
        "kind": "daily_close",
        "observed_at": None,
        "session_date": "2026-11-23",
        "reference_observed_at": None,
    }


def test_no_overnight_input_is_a_model_covariate():
    made = bootstrap()
    covariates = set(made.diagnostics["covariates_used"])
    assert not covariates & {
        "overnight_futures_change_pct",
        "vix_overnight_level",
        "iv_rank_pct",
        "premarket_window_change_pct",
    }


def test_a_failed_overnight_source_is_missing_not_fatal():
    market = FakeMarket()
    market._minutes.pop("NQ=F")
    market._cboe.pop("VXN")
    made = generate("TQQQ", "bootstrap", now=PRE_MARKET, data=market, simulations=2000)
    assert parse_report(made.report).ok
    assert made.snapshot["overnight_futures_change_pct"] is None
    assert "overnight_futures_change_pct" in made.snapshot["missing_inputs"]
    # VXN falls back to Yahoo's daily ^VXN.
    assert made.snapshot["iv_rank_pct"] is not None
    assert any(
        o["source"] == "yahoo_chart_1d" and o["field"] == "iv_rank_pct"
        for o in made.snapshot["input_observations"]
    )


def test_a_missing_covariate_history_is_listed():
    market = FakeMarket()
    market._daily.pop("CL=F")
    made = generate("TQQQ", "bootstrap", now=PRE_MARKET, data=market, simulations=2000)
    assert "wti_return_pct" in made.report["execution_signals"]["data_quality"]["missing_inputs"]
    assert made.snapshot["wti_crude_usd"] is None


def test_confidence_counts_only_the_outside_sources():
    made = bootstrap()
    assert made.report["execution_signals"]["data_quality"]["confidence_score"] == 1.0
    assert made.report["execution_signals"]["data_quality"]["source_coverage"] == "mixed"


def test_with_every_outside_source_down_the_mapping_would_abstain():
    """Calendar and fund-derived features are always there; they must not
    lift a report with no outside data over the mapping's abstain line."""
    market = FakeMarket()
    for ticker in ("QQQ", "SPY", "NQ=F", "^VIX", "^VXN", "^TNX", "DX-Y.NYB", "CL=F"):
        market._daily.pop(ticker)
    made = generate("TQQQ", "bootstrap", now=PRE_MARKET, data=market, simulations=2000)
    audit = parse_report(made.report)
    assert audit.ok
    assert audit.report.confidence < MIN_CONFIDENCE
    assert audit.report.coverage == DEGRADED


def test_losing_most_outside_sources_is_degraded():
    market = FakeMarket()
    for ticker in ("^VIX", "^VXN", "^TNX", "DX-Y.NYB", "CL=F"):
        market._daily.pop(ticker)
    quality = generate("TQQQ", "bootstrap", now=PRE_MARKET, data=market, simulations=2000).report[
        "execution_signals"
    ]["data_quality"]
    assert quality["confidence_score"] == pytest.approx(3 / 8, abs=0.01)
    assert quality["source_coverage"] == "degraded"


def test_a_source_the_fund_is_itself_is_not_asked_for():
    # QQQ's underlying is QQQ: four of its eight outside series remain asked.
    assert generator.data_confidence(["spy_return_pct"], [], 1000) == (1.0, "mixed")
    assert generator.data_confidence([], [], 1000) == (0.0, "degraded")
    assert generator.data_confidence(["vix_level"], ["wti_return_pct"], 400) == (0.5, "degraded")


# --------------------------------------------------------------------
# Chronos-2, through a fake pipeline


def test_chronos_gets_the_target_past_and_known_future_covariates():
    pipeline = FakeChronos()
    made = generate(
        "TQQQ", "chronos", now=PRE_MARKET, data=FakeMarket(), pipeline=pipeline, simulations=2000
    )
    assert parse_report(made.report).ok
    call = pipeline.calls[0]
    assert call["prediction_length"] == 64
    sent = call["inputs"][0]
    assert sent["target"].dtype == np.float32
    assert "vix_level" in sent["past_covariates"]
    # Only the calendar is known in advance; nothing market-driven is.
    assert set(sent["future_covariates"]) == {
        n for n in sent["past_covariates"] if n.startswith("calendar_")
    }
    assert all(len(v) == 64 for v in sent["future_covariates"].values())
    assert (
        made.diagnostics["engine"] == "chronos" and made.diagnostics["extension_steps"] == 252 - 64
    )
    assert "zero-shot" in made.report["model"]


def test_chronos_forecasts_at_most_the_direct_horizon_whatever_its_native_one():
    """chronos-forecasting 2.3 reports a native horizon of 1,024 sessions;
    the generator still forecasts 64 directly and extends the rest."""
    pipeline = FakeChronos()
    pipeline.model_prediction_length = 1024
    made = generate(
        "TQQQ", "chronos", now=PRE_MARKET, data=FakeMarket(), pipeline=pipeline, simulations=2000
    )
    assert pipeline.calls[0]["prediction_length"] == model.DIRECT_HORIZON == 64
    assert made.diagnostics["direct_steps"] == 64 and made.diagnostics["native_horizon"] == 1024
    assert made.diagnostics["extension_steps"] == 252 - 64


def test_chronos_unavailable_is_refused_with_how_to_install(monkeypatch):
    monkeypatch.setattr(model, "chronos_available", lambda: (False, "torch not installed"))
    with pytest.raises(ForecastRefused, match=r"requirements-dl|torch"):
        generate("TQQQ", "chronos", now=PRE_MARKET, data=FakeMarket())


def test_the_chronos_shape_is_unwrapped():
    quantiles = model.chronos_quantiles(np.zeros(400), {}, {}, 10, pipeline=FakeChronos())
    assert quantiles.values.shape == (10, len(QUANTILE_LEVELS))


# --------------------------------------------------------------------
# Refusals: when no honest report can be made


def test_a_run_inside_regular_hours_is_refused():
    with pytest.raises(ForecastRefused, match="regular"):
        generate(
            "TQQQ", "bootstrap", now=datetime(2026, 11, 24, 15, 0, tzinfo=UTC), data=FakeMarket()
        )


def test_a_run_while_closing_prints_settle_is_refused():
    with pytest.raises(ForecastRefused, match="16:15"):
        generate(
            "TQQQ", "bootstrap", now=datetime(2026, 11, 24, 21, 5, tzinfo=UTC), data=FakeMarket()
        )


def test_a_report_on_a_stale_close_is_refused():
    stale = FakeMarket(last=date(2026, 11, 20))
    with pytest.raises(ForecastRefused, match="has not posted"):
        generate("TQQQ", "bootstrap", now=PRE_MARKET, data=stale)


def test_a_short_history_is_refused():
    with pytest.raises(ForecastRefused, match="300"):
        generate("TQQQ", "bootstrap", now=PRE_MARKET, data=FakeMarket(sessions=200))


@pytest.mark.parametrize("symbol", ["", "tq qq", "../etc", "WAYTOOLONGSYMBOL"])
def test_a_bad_symbol_is_refused(symbol):
    with pytest.raises(ForecastRefused):
        generate(symbol, "bootstrap", now=PRE_MARKET, data=FakeMarket())


def test_an_unknown_engine_is_refused():
    with pytest.raises(ForecastRefused, match="engine"):
        generate("TQQQ", "oracle", now=PRE_MARKET, data=FakeMarket())


def test_todays_bar_is_never_read():
    """A bar stamped on the target session (Yahoo serves today's while it
    trades) must not anchor the report."""
    market = FakeMarket()
    frame = market._daily["TQQQ"]
    today = frame.iloc[[-1]].copy()
    today.index = pd.DatetimeIndex([pd.Timestamp(SESSION)])
    today["Close"] = 999.0
    market._daily["TQQQ"] = pd.concat([frame, today])
    made = generate("TQQQ", "bootstrap", now=PRE_MARKET, data=market, simulations=2000)
    assert made.report["base_price"] != 999.0
    assert made.snapshot["base_session_date"] == "2026-11-23"


# --------------------------------------------------------------------
# Pieces


def test_rounding_keeps_the_audit_sums_exact():
    horizon = {
        "label": "x",
        "trading_days": 1,
        "bin_width_pct": 1.0,
        "underflow_prob": 0.123456,
        "overflow_prob": 0.0000001,
        "bins": [
            {"min_pct": i - 5.0, "max_pct": i - 4.0, "prob": (1 - 0.1234561) / 10, "cdf": 0}
            for i in range(10)
        ],
        "summary": {
            "mean_pct": 0.123,
            "median_pct": 0.1,
            "std_pct": 1.234,
            "prob_positive": 0.51234,
            "expected_shortfall_5pct": -2.345,
            "quantiles_pct": {
                "p01": -3.0,
                "p05": -2.0,
                "p25": -0.5,
                "p75": 0.6,
                "p95": 2.1,
                "p99": 3.2,
            },
        },
    }
    rounded = rounded_horizon(horizon)
    shares = [
        rounded["underflow_prob"],
        *(b["prob"] for b in rounded["bins"]),
        rounded["overflow_prob"],
    ]
    assert round(sum(shares) * 10_000) == 10_000
    assert all(s >= 0 for s in shares)
    assert rounded["bins"][-1]["cdf"] == pytest.approx(1 - rounded["overflow_prob"])


def test_overnight_change_is_unavailable_without_a_close_bar():
    closes = pd.Series(
        [1.0, 2.0],
        index=pd.DatetimeIndex(
            [
                datetime(2026, 11, 24, 4, 0, tzinfo=EASTERN),
                datetime(2026, 11, 24, 4, 1, tzinfo=EASTERN),
            ]
        ),
    )
    result = overnight_futures_change(closes, BASE, datetime(2026, 11, 24, 4, 20, tzinfo=EASTERN))
    assert result["change_pct"] is None and "ten minutes before" in result["reason"]


def test_the_ten_year_yield_reads_either_yahoo_convention():
    assert generator.yield_pct(4.84) == 4.84
    assert generator.yield_pct(48.4) == pytest.approx(4.84)
    assert generator.yield_pct(None) is None
    snapshot = bootstrap().snapshot
    tnx = FakeMarket()._daily["^TNX"]["Close"]
    assert snapshot["us_10y_yield_pct"] == pytest.approx(float(tnx.iloc[-1]))


def test_window_check_names_the_session():
    assert generator.window_check(PRE_MARKET) == (SESSION, None)


def chart(timestamps, closes, adjclose=None, zone="America/New_York"):
    result = {
        "meta": {"exchangeTimezoneName": zone},
        "timestamp": timestamps,
        "indicators": {
            "quote": [
                {
                    "open": closes,
                    "high": closes,
                    "low": closes,
                    "close": closes,
                    "volume": [1] * len(closes),
                }
            ]
        },
    }
    if adjclose is not None:
        result["indicators"]["adjclose"] = [{"adjclose": adjclose}]
    return {"chart": {"result": [result], "error": None}}


def test_yahoo_daily_is_adjusted_and_dated_by_the_exchange_session():
    # 14:30 UTC = 09:30 ET on two sessions; the first bar's dividend halves it.
    stamps = [
        int(datetime(2026, 11, 20, 14, 30, tzinfo=UTC).timestamp()),
        int(datetime(2026, 11, 23, 14, 30, tzinfo=UTC).timestamp()),
    ]
    frame = parse_yahoo_daily(chart(stamps, [10.0, 20.0], adjclose=[5.0, 20.0]))
    assert [d.date() for d in frame.index] == [date(2026, 11, 20), date(2026, 11, 23)]
    assert frame["Close"].tolist() == [5.0, 20.0]
    assert frame["Open"].tolist() == [5.0, 20.0]


def test_yahoo_minutes_are_eastern_and_drop_empty_bars():
    stamps = [int(datetime(2026, 11, 24, 9, m, tzinfo=UTC).timestamp()) for m in range(3)]
    frame = parse_yahoo_minutes(chart(stamps, [1.0, None, 3.0]))
    assert len(frame) == 2
    assert str(frame.index.tz) == "America/New_York" and frame.index[0].hour == 4


def test_a_yahoo_error_is_unavailable():
    with pytest.raises(MarketDataUnavailable):
        parse_yahoo_daily({"chart": {"result": None, "error": {"code": "Not Found"}}}, "^RVX")


def test_cboe_csv_close_only():
    text = "DATE,OPEN,HIGH,LOW,CLOSE\n11/20/2026,20,22,15.39,21.0\n11/23/2026,21,23,19,22.5\n"
    series = parse_cboe_daily_csv(text)
    assert series.to_dict() == {date(2026, 11, 20): 21.0, date(2026, 11, 23): 22.5}


def test_market_data_caches_within_its_ttl():
    clock = {"t": 0.0}
    calls: list[str] = []

    def get(url: str) -> bytes:
        calls.append(url)
        return json.dumps(
            chart([int(datetime(2026, 11, 23, 14, 30, tzinfo=UTC).timestamp())], [1.0])
        ).encode()

    data = MarketData(get=get, ttl_seconds=600, clock=lambda: clock["t"])
    data.daily("TQQQ")
    data.daily("TQQQ")
    assert len(calls) == 1
    clock["t"] = 601.0
    data.daily("TQQQ")
    assert len(calls) == 2
