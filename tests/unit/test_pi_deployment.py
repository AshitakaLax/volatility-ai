"""The Pi deployment's moving parts, checked without a Pi.

None of this needs Docker. It pins the joins between files that are
edited independently and fail far from where they broke: a compose
entrypoint naming a script that was renamed, a session loop passing a
flag the supervisor dropped, or the timezone package going missing from
requirements and taking every session decision down with it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE = ROOT / "docker-compose.pi.yml"
LOOP = ROOT / "tools" / "docker_session_loop.sh"


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def test_the_pi_compose_file_parses(compose):
    assert set(compose["services"]) == {"paper", "dashboard"}


def test_the_entrypoint_script_the_compose_file_names_exists(compose):
    """A renamed script surfaces on the Pi as a container that exits
    immediately, which reads like a crash rather than a typo."""
    entrypoint = compose["services"]["paper"]["entrypoint"]
    script = next(part for part in entrypoint if part.endswith(".sh"))
    local = ROOT / script.removeprefix("/app/")
    assert local.exists(), f"{script} is the entrypoint but {local} does not exist"


def test_the_session_loop_only_passes_flags_the_supervisor_accepts():
    """THE JOIN MOST LIKELY TO ROT. The loop script and the supervisor
    are edited for different reasons, and a dropped flag fails inside a
    container on a machine nobody is watching.

    Asks the supervisor's own parser what it accepts rather than keeping
    a second list here, which could go stale in exactly the way this is
    meant to catch.
    """
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
        assert flag in help_text, (
            f"{flag} is passed by docker_session_loop.sh but the supervisor has no such flag"
        )


def test_the_state_paths_agree_between_the_two_services(compose):
    """The dashboard must read the ledger the loop writes. Two different
    paths would render an empty page that looks like a flat book."""
    loop_db = compose["services"]["paper"]["environment"]["VAI_STATE_DB"]
    dash = " ".join(compose["services"]["dashboard"]["entrypoint"])
    assert loop_db in dash, f"dashboard does not read {loop_db}"


def test_the_dashboards_state_mount_is_read_only(compose):
    """Belt to the application's own mode=ro braces. The dashboard is
    the one service exposed on the LAN."""
    mounts = compose["services"]["dashboard"]["volumes"]
    state = next(m for m in mounts if m.startswith("state:"))
    assert state.endswith(":ro"), f"{state} must be read-only"


def test_the_ledger_lives_on_a_named_volume_not_a_bind_mount(compose):
    """A bind mount onto the SD card invites someone to tidy up the
    directory holding every open lot."""
    assert "state" in compose["volumes"]
    for service in ("paper", "dashboard"):
        mounts = compose["services"][service]["volumes"]
        assert any(m.startswith("state:") for m in mounts), service


def test_both_services_restart_themselves(compose):
    """The Pi reboots. The loop survives a failing session on its own;
    this covers a killed container and a daemon restart."""
    for service in ("paper", "dashboard"):
        assert compose["services"][service]["restart"] == "unless-stopped"


def test_tzdata_is_a_declared_dependency():
    """NOT optional, and its absence is a hard failure rather than a
    degradation. src/fomc_calendar does ZoneInfo("America/New_York") at
    import; slim Debian images ship no /usr/share/zoneinfo, so without
    this package the container dies at import with a traceback that no
    market-hours logic ever reached.
    """
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "tzdata" in requirements

    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "tzdata" in dockerfile, "the image should also carry system tzdata"


def test_the_loop_checks_for_the_timezone_database_before_trading():
    """It fails with an explanation rather than letting the first
    session die on an import error 15 minutes later."""
    text = LOOP.read_text(encoding="utf-8")
    assert "ZoneInfo" in text
    assert "tzdata" in text


def test_the_loop_waits_between_sessions():
    """Without this the supervisor's two-second exit on a non-trading
    day becomes a hot restart loop for the whole weekend."""
    text = LOOP.read_text(encoding="utf-8")
    assert "sleep" in text
    assert "VAI_IDLE_SECONDS" in text


def test_the_pi_compose_does_not_reference_env_files_the_pi_lacks(compose):
    """docker-compose.yml names .env.staging and .env.production, which
    do not exist on the Pi and fail the whole file at parse time. That
    is why this is a separate file, and it must stay that way."""
    for name, service in compose["services"].items():
        for env_file in service.get("env_file", []):
            assert env_file == ".env", f"{name} references {env_file}"


def test_the_deployment_guide_leads_with_decommissioning():
    """Two hosts on one account diverge the ledger, and the ordering of
    the guide is the only thing preventing it."""
    guide = (ROOT / "docs" / "DEPLOY_RASPBERRY_PI.md").read_text(encoding="utf-8")
    assert guide.index("Decommission the old host") < guide.index("## 5. Verify")
