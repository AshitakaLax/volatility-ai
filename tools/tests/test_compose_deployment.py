"""The single-host deployment's moving parts, checked without Docker.

docker-compose.yml, the session and backup loops, the supervisor and the
configs are edited independently and fail far from where they broke: a
compose entrypoint naming a renamed script, a loop passing a flag the
supervisor dropped, two trading services sharing one ledger. These pin
the joins.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE = ROOT / "docker-compose.yml"
LOOP = ROOT / "tools" / "docker_session_loop.sh"
BACKUP_LOOP = ROOT / "tools" / "docker_backup_loop.sh"
TRADERS = ("paper", "paper-ultimate", "live")


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _services(compose, *, profile=None) -> set:
    """Services `up` starts (profile=None), or those behind one profile."""
    names = set()
    for name, service in compose["services"].items():
        profiles = service.get("profiles", [])
        if (profile in profiles) if profile else not profiles:
            names.add(name)
    return names


def _env_files(service) -> list:
    return [e["path"] if isinstance(e, dict) else e for e in service.get("env_file", [])]


def _state_volume(service) -> str:
    return next(m.split(":")[0] for m in service["volumes"] if m.split(":")[1] == "/app/state")


def test_up_starts_what_must_keep_running_and_nothing_else(compose):
    """Real money and one-off tools are started only by name."""
    assert _services(compose) == {"web", "paper-ultimate", "backup"}
    assert _services(compose, profile="champion") == {"paper"}
    assert _services(compose, profile="production") == {"live"}
    assert _services(compose, profile="tools") == {
        "test",
        "preflight",
        "check",
        "fetch-data",
        "ingest",
        "backtest",
        "research",
    }


def test_each_trading_loop_has_its_own_ledger_and_its_own_account(compose):
    """Two loops on one ledger, or one Alpaca account, diverge from the venue
    while both believe they are authoritative."""
    services = compose["services"]
    volumes = [_state_volume(services[name]) for name in TRADERS]
    env_files = [tuple(_env_files(services[name])) for name in TRADERS]
    assert len(set(volumes)) == len(TRADERS), volumes
    assert len(set(env_files)) == len(TRADERS), env_files
    for volume in volumes:
        assert volume in compose["volumes"], f"{volume} must be a named volume"


def test_the_ui_reads_every_ledger_read_only(compose):
    """Belt to server/live.py's mode=ro braces."""
    mounts = compose["services"]["web"]["volumes"]
    for name in TRADERS[:2]:
        volume = _state_volume(compose["services"][name])
        mount = next(m for m in mounts if m.startswith(f"{volume}:"))
        assert mount.endswith(":ro"), mount


def test_the_ui_sees_the_backups_without_being_able_to_touch_them(compose):
    """The Warehouse tab reports the newest archive; only `backup` writes them."""
    web = compose["services"]["web"]
    (mount,) = [m for m in web["volumes"] if m.split(":")[-2:-1] == ["/app/backups"]]
    assert mount.endswith(":ro"), mount
    assert web["environment"]["VAI_BACKUP_DIR"] == "/app/backups"
    backup = compose["services"]["backup"]["volumes"]
    assert mount.removesuffix(":ro") in backup


def test_the_ui_is_published_on_loopback_unless_asked(compose):
    """It has no authentication and serves balances, cost bases and the halt."""
    (port,) = compose["services"]["web"]["ports"]
    assert port.startswith("${VAI_WEB_BIND:-127.0.0.1}:"), port


def test_trading_loops_restart_stop_gracefully_and_survive_memory_pressure(compose):
    for name in TRADERS:
        service = compose["services"][name]
        assert service["restart"] == "unless-stopped"
        # The supervisor waits up to 120s for the loop to settle.
        assert service["stop_grace_period"] in ("3m", "4m", "5m")
        assert service["oom_score_adj"] < 0


def test_the_scripts_and_configs_compose_names_exist(compose):
    """A renamed script surfaces as a container that exits at once, which
    reads like a crash rather than a typo."""
    for name, service in compose["services"].items():
        for part in service.get("entrypoint", []):
            if part.startswith("/app/"):
                assert (ROOT / part.removeprefix("/app/")).exists(), f"{name}: {part}"
        config = service.get("environment", {}).get("VAI_CONFIG")
        if config:
            assert (ROOT / config.removeprefix("/app/")).exists(), f"{name}: {config}"


def test_every_trading_config_builds_for_live(compose):
    """The live rules (live_algorithm.build_strategy) are checked at start-up;
    a config that breaks them would only surface as a loop that never starts."""
    from engine.core.config import BacktestConfig
    from research.strategies.live_algorithm import build_strategy
    from research.strategies.strategy_registry import STRATEGIES

    for name in TRADERS:
        path = compose["services"][name]["environment"]["VAI_CONFIG"]
        config = BacktestConfig.from_yaml(str(ROOT / path.removeprefix("/app/")))
        config.validate()
        assert config.live.enabled, name
        assert config.live.paper_trading is (name != "live"), name
        build_strategy(config, STRATEGIES)


def test_the_session_loop_only_passes_flags_the_supervisor_accepts():
    """THE JOIN MOST LIKELY TO ROT. Asks the supervisor's own parser rather
    than keeping a second list here that could go stale the same way."""
    import io
    from contextlib import redirect_stdout

    from tools.market_hours_supervisor import parse_args

    buffer = io.StringIO()
    with redirect_stdout(buffer), pytest.raises(SystemExit):
        parse_args(["--help"])
    help_text = buffer.getvalue()

    used = {word for word in LOOP.read_text(encoding="utf-8").split() if word.startswith("--")}
    assert used, "the loop passes no flags at all -- this test would prove nothing"
    for flag in sorted(used):
        assert flag in help_text, f"{flag} is passed by docker_session_loop.sh but not accepted"


def test_the_backup_loop_only_passes_flags_the_backup_tool_accepts():
    from tools.backup_databases import build_parser

    help_text = build_parser().format_help()
    used = {
        word.strip('"')
        for word in BACKUP_LOOP.read_text(encoding="utf-8").split()
        if word.startswith(("--", '"--'))
    }
    assert {"--db", "--out-dir", "--keep", "--local-only", "--remote-host"} <= used
    for flag in sorted(used):
        assert flag in help_text, f"{flag} is passed by docker_backup_loop.sh but not accepted"


def test_tzdata_is_a_declared_dependency():
    """NOT optional: engine/data/fomc_calendar does ZoneInfo("America/New_York")
    at import, and slim images ship no /usr/share/zoneinfo."""
    assert "tzdata" in (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "tzdata" in (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_the_loop_checks_for_the_timezone_database_and_waits_between_sessions():
    text = LOOP.read_text(encoding="utf-8")
    assert "ZoneInfo" in text and "tzdata" in text
    assert "sleep" in text and "VAI_IDLE_SECONDS" in text


def test_the_deployment_guide_leads_with_stopping_the_other_host():
    """Two hosts on one account diverge the ledger, and the ordering of the
    guide is the only thing preventing it."""
    guide = (ROOT / "docs" / "DEPLOY.md").read_text(encoding="utf-8")
    assert guide.index("Stop every other host") < guide.index("docker compose up")


# -- docker stop, end to end, with a stand-in supervisor --------------------

_STUB = """#!/bin/sh
[ "$1" = "-c" ] && exit 0
echo started > "$MARKERS/started"
trap 'echo graceful > "$MARKERS/stopped"; exit 0' TERM
while :; do sleep 0.05; done
"""


def _wait_for(path: Path, seconds: float = 10.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals and /bin/sh")
def test_docker_stop_reaches_the_supervisor_as_a_graceful_stop(tmp_path):
    """docker stop signals PID 1, the shell; a shell forwards nothing by
    itself, so the trading loop used to be killed mid-tick when the grace
    period ran out."""
    bin_dir, markers = tmp_path / "bin", tmp_path / "markers"
    bin_dir.mkdir()
    markers.mkdir()
    stub = bin_dir / "python"
    stub.write_text(_STUB)
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "MARKERS": str(markers)}
    loop = subprocess.Popen(
        ["/bin/sh", str(LOOP)], cwd=ROOT, env=env, stdout=subprocess.PIPE, text=True
    )
    try:
        assert _wait_for(markers / "started"), "the supervisor never started"
        loop.send_signal(signal.SIGTERM)
        out, _ = loop.communicate(timeout=10)
    finally:
        loop.kill()
    assert (markers / "stopped").read_text().strip() == "graceful"
    assert loop.returncode == 0
    assert "[loop] stop requested" in out and out.rstrip().endswith("[loop] stopped")


def test_sigterm_takes_the_supervisors_ctrl_c_path():
    """run_session stops the trading loop on KeyboardInterrupt; SIGTERM must
    arrive as one."""
    from tools.market_hours_supervisor import _interrupt

    with pytest.raises(KeyboardInterrupt):
        _interrupt(signal.SIGTERM, None)
