from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .models import FindMyAsset

DEFAULT_CACHE_DIR = Path.home() / ".local" / "state" / "findmypipe"
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "asset_cache.json"


def _cache_path() -> Path:
    override = os.getenv("FINDMY_CACHE_FILE")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CACHE_FILE


def _cache_ttl() -> int:
    raw = os.getenv("FINDMY_CACHE_TTL", "0")
    try:
        return max(0, int(raw))
    except (ValueError, TypeError):
        return 0


def _now() -> float:
    return time.time()


def load_assets() -> list[FindMyAsset] | None:
    """Load cached assets if a fresh cache exists. Returns None if no valid cache."""
    path = _cache_path()
    ttl = _cache_ttl()

    if ttl <= 0:
        return None

    if not path.is_file():
        return None

    try:
        cached = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    cached_at = cached.get("_cached_at", 0)
    age = _now() - cached_at
    if age > ttl:
        return None

    raw_assets = cached.get("assets")
    if not isinstance(raw_assets, list):
        return None

    return [_asset_from_dict(a) for a in raw_assets if isinstance(a, dict)]


def save_assets(assets: list[FindMyAsset]) -> None:
    """Save assets to cache file with current timestamp."""
    ttl = _cache_ttl()
    if ttl <= 0:
        return

    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)

    payload: dict[str, Any] = {
        "_cached_at": _now(),
        "_ttl": ttl,
        "assets": [asset.to_dict(include_raw=False) for asset in assets],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    path.chmod(0o600)


def cache_info() -> dict[str, object]:
    """Return cache status for doctor output."""
    path = _cache_path()
    ttl = _cache_ttl()

    info: dict[str, object] = {
        "enabled": ttl > 0,
        "ttl_seconds": ttl,
        "path": str(path),
    }

    if not path.is_file():
        info["state"] = "empty"
        return info

    try:
        cached = json.loads(path.read_text())
        cached_at = cached.get("_cached_at", 0)
        age = _now() - cached_at
        info["state"] = "fresh" if age <= ttl else "stale"
        info["age_seconds"] = round(age, 1)
        info["asset_count"] = len(cached.get("assets", []))
    except (json.JSONDecodeError, OSError):
        info["state"] = "corrupt"

    return info


def _asset_from_dict(d: dict[str, Any]) -> FindMyAsset:
    """Reconstruct a FindMyAsset from its to_dict() representation."""
    return FindMyAsset(
        id=str(d.get("id", "")),
        name=str(d.get("name", "")),
        kind=str(d.get("kind", "unknown")),  # type: ignore[arg-type]
        provider=str(d.get("provider", "")),
        latitude=_opt_float(d.get("latitude")),
        longitude=_opt_float(d.get("longitude")),
        accuracy_m=_opt_float(d.get("accuracy_m")),
        battery=_opt_float(d.get("battery")),
        battery_status=str(d.get("battery_status", "unknown")),
        last_seen=_opt_str(d.get("last_seen")),
        location_is_old=_opt_bool(d.get("location_is_old")),
    )


def _opt_float(v: object) -> float | None:
    if v is None:
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def _opt_str(v: object) -> str | None:
    if v is None:
        return None
    return str(v)


def _opt_bool(v: object) -> bool | None:
    if v is None:
        return None
    return bool(v)
