"""Shared filesystem locations and timestamped artifact lookup."""

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
VIZ = ROOT / "visualizations"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def stage_dir(name: str) -> Path:
    directory = DATA / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def latest(dir_name: str, prefix: str) -> Path:
    """Return the newest file in data/<dir_name> beginning with <prefix>."""
    candidates = sorted(stage_dir(dir_name).glob(f"{prefix}*"))
    if not candidates:
        raise FileNotFoundError(
            f"no {prefix}* in data/{dir_name} — run earlier stage first"
        )
    return candidates[-1]
