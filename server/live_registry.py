"""The live deployments this server shows and controls, by id.

config/deployments.yaml ($VAI_DEPLOYMENTS overrides it, for tests) names each
deployment's config, ledger and control directory AS THIS PROCESS SEES THEM:
in the compose deployment, the paths of the web container's mounts. A browser
names a deployment by its id and by nothing else. No route takes a path, so
no request can point the server at a file the registry does not name -- the
old routes took one, and the halt would open any writable file it was given
as a SQLite ledger.

Paper or real money comes from each deployment's own config
(live.paper_trading), not from the shape of a file name.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

import yaml

from engine.core.config import BacktestConfig, LiveControlConfig
from engine.trading.control_inbox import ControlInbox

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = _REPO_ROOT / "config" / "deployments.yaml"
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")


class UnknownDeployment(KeyError):
    """No deployment has this id."""


def _resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else _REPO_ROOT / path


@dataclass(frozen=True)
class Deployment:
    """One entry of the registry."""

    id: str
    label: str
    service: str | None
    config_path: Path
    state_db: Path
    control_dir: Path | None
    # "alpaca" or "fidelity", for the page to place a deployment whose
    # config does not exist yet; the config's own live.broker wins once it
    # does. How to run one that no compose service runs.
    broker: str | None = None
    runs: str | None = None

    def config(self) -> BacktestConfig:
        """The deployment's config, validated -- re-read when the file
        changes, so an edited grant takes effect without a server restart."""
        return _load_config(self.config_path)

    @property
    def paper(self) -> bool:
        return self.config().live.paper_trading

    @property
    def caps(self) -> LiveControlConfig:
        """What the Live page may do here: the config's grants with the
        real-money rules applied (LiveControlConfig.effective)."""
        config = self.config()
        return config.live.control.effective(config.live.paper_trading)

    def inbox(self) -> ControlInbox | None:
        return ControlInbox(self.control_dir) if self.control_dir is not None else None


_config_cache: dict[Path, tuple[float, BacktestConfig]] = {}
_registry_cache: dict[Path, tuple[float, dict[str, Deployment]]] = {}
_lock = threading.Lock()


def _load_config(path: Path) -> BacktestConfig:
    mtime = path.stat().st_mtime
    with _lock:
        cached = _config_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
    config = BacktestConfig.from_yaml(str(path))
    config.validate()
    with _lock:
        _config_cache[path] = (mtime, config)
    return config


def registry_path() -> Path:
    configured = os.environ.get("VAI_DEPLOYMENTS")
    return Path(configured) if configured else DEFAULT_REGISTRY


def registry() -> dict[str, Deployment]:
    """Every deployment, in the file's order. Empty when there is no file."""
    path = registry_path()
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return {}
    with _lock:
        cached = _registry_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("deployments") or {}
    if not isinstance(entries, dict):
        raise ValueError(f"{path}: `deployments` must be a mapping of id -> entry")
    deployments: dict[str, Deployment] = {}
    for deployment_id, entry in entries.items():
        if not _ID.match(str(deployment_id)):
            raise ValueError(f"{path}: deployment id {deployment_id!r} is not a-z, 0-9 and -")
        config_path = _resolve(entry.get("config"))
        state_db = _resolve(entry.get("state_db"))
        if config_path is None or state_db is None:
            raise ValueError(f"{path}: {deployment_id} needs config and state_db")
        broker = entry.get("broker")
        if broker not in (None, "alpaca", "fidelity"):
            raise ValueError(f"{path}: {deployment_id}'s broker must be alpaca or fidelity")
        deployments[deployment_id] = Deployment(
            id=deployment_id,
            label=str(entry.get("label") or deployment_id),
            service=entry.get("service"),
            config_path=config_path,
            state_db=state_db,
            control_dir=_resolve(entry.get("control_dir")),
            broker=broker,
            runs=entry.get("runs"),
        )
    with _lock:
        _registry_cache[path] = (mtime, deployments)
    return deployments


def get(deployment_id: str) -> Deployment:
    try:
        return registry()[deployment_id]
    except KeyError:
        raise UnknownDeployment(deployment_id) from None


def setup_hint(deployment: Deployment) -> str:
    """What to do for a deployment whose config does not exist yet."""
    try:
        shown = deployment.config_path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        shown = str(deployment.config_path)
    example = deployment.config_path.with_name(deployment.config_path.name + ".example")
    hint = f"{shown} does not exist yet"
    if example.exists():
        hint += f": copy {shown}.example to it and fill it in"
    return hint


__all__ = ["Deployment", "UnknownDeployment", "get", "registry", "registry_path", "setup_hint"]
