"""risk.overlay and live.control.risk_reports (engine/core/config.py): frozen
and validated up front, and invisible to every config written before them."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.core.config import BacktestConfig, LiveControlConfig, RiskOverlayConfig
from engine.core.exceptions import ConfigurationError

ROOT = Path(__file__).resolve().parents[2]


def load(path: str = "config/paper_aggressive.yaml", **overlay) -> dict:
    data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    if overlay is not None:
        data.setdefault("risk", {})["overlay"] = overlay
    return data


def build(data: dict) -> BacktestConfig:
    config = BacktestConfig.from_dict(data)
    config.validate()
    return config


class TestParsing:
    def test_the_plans_example(self):
        config = build(
            load(
                mode="advisory",
                mapping="v1",
                exposure_floor=0.1,
                exempt=["reversal"],
                supersedes=["governor", "event_boosts"],
                spacing={"enabled": True, "exponent": 1.0, "max_multiplier": 4.0},
                weekly={"horizon": "next_month", "slope": 0.5, "reset": "monday"},
            )
        )
        overlay = config.risk.overlay
        assert overlay.mode == "advisory" and overlay.exempt == ("reversal",)
        assert overlay.supersedes == ("governor", "event_boosts")
        assert overlay.spacing.max_multiplier == 4.0 and overlay.weekly.horizon == "next_month"

    def test_defaults(self):
        assert build(load()).risk.overlay == RiskOverlayConfig()

    def test_no_section_takes_no_reports(self):
        data = load()
        del data["risk"]["overlay"]
        assert build(data).risk.overlay is None

    @pytest.mark.parametrize(
        "overlay, message",
        [
            ({"mood": "calm"}, "no setting"),
            ({"spacing": {"width": 2}}, "spacing has no setting"),
            ({"mode": "aggressive"}, "risk.overlay.mode"),
            ({"daily": "false"}, "true or false"),
            ({"exposure_floor": 0}, "exposure_floor"),
            ({"spacing": {"max_multiplier": 0.5}}, "never narrows"),
            ({"supersedes": ["regime"]}, "supersedes"),
            ({"exempt": "reversal"}, "LIST"),
            ({"weekly": {"horizon": "next_year"}}, "weekly.horizon"),
            ({"source": "proxy"}, "backtest sources"),
        ],
    )
    def test_refused_up_front(self, overlay, message):
        with pytest.raises(ConfigurationError, match=message):
            build(load(**overlay))

    def test_real_money_stays_advisory(self):
        with pytest.raises(ConfigurationError, match="real-money"):
            build(load("config/production.yaml", mode="enforce"))
        assert (
            build(load("config/production.yaml", mode="advisory")).risk.overlay.mode == "advisory"
        )

    def test_paper_may_enforce(self):
        assert build(load(mode="enforce")).risk.overlay.mode == "enforce"

    def test_a_backtest_schedule_needs_its_file(self):
        data = load(source="schedule")
        data.pop("live")
        with pytest.raises(ConfigurationError, match=r"needs risk\.overlay\.path"):
            build(data)


class TestTheGrant:
    def test_risk_reports_is_a_grant_like_the_others(self):
        data = load()
        data["live"].setdefault("control", {})["risk_reports"] = True
        assert build(data).live.control.risk_reports is True
        data["live"]["control"]["risk_reports"] = "yes"
        with pytest.raises(ConfigurationError, match="risk_reports must be true or false"):
            build(data)

    def test_it_is_written_only_when_set(self):
        assert "risk_reports" not in LiveControlConfig().to_dict()
        assert LiveControlConfig(risk_reports=True).to_dict()["risk_reports"] is True
        assert LiveControlConfig().grants()["risk_reports"] is False


class TestHashStability:
    def test_a_config_without_an_overlay_writes_none(self):
        data = load()
        del data["risk"]["overlay"]
        assert "overlay" not in build(data).to_dict()["risk"]

    def test_an_overlay_round_trips(self):
        config = build(load(mode="enforce", spacing={"target_follows": True}))
        again = BacktestConfig.from_dict(config.to_dict())
        assert again.risk.overlay == config.risk.overlay
