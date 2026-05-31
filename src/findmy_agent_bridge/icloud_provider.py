from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from typing import Any, Iterable, Protocol

from .models import FindMyAsset
from .redaction import REDACTED, redact_secrets

SENSITIVE_RAW_KEYS = {
    "account",
    "appleid",
    "apple_id",
    "auth",
    "authorization",
    "baucuid",
    "bauuid",
    "commandid",
    "commandlookupid",
    "cookie",
    "cookies",
    "device_id",
    "deviceid",
    "devicediscoveryid",
    "email",
    "encodeddeviceid",
    "id",
    "owner",
    "password",
    "secret",
    "session",
    "token",
}


class Provider(Protocol):
    name: str

    def list_assets(self) -> list[FindMyAsset]: ...


@dataclass(slots=True)
class MockProvider:
    name: str = "mock"

    def list_assets(self) -> list[FindMyAsset]:
        return []


@dataclass(slots=True)
class PyiCloudDevicesProvider:
    api: Any
    name: str = "icloud"

    def list_assets(self) -> list[FindMyAsset]:
        return [normalize_pyicloud_device(status) for status in _iter_device_statuses(self.api)]


def normalize_pyicloud_device(raw: dict[str, Any]) -> FindMyAsset:
    raw_location = raw.get("location")
    location: dict[str, Any] = raw_location if isinstance(raw_location, dict) else {}
    raw_id = raw.get("id") or raw.get("deviceId") or raw.get("device_id")
    return FindMyAsset(
        id=_public_asset_id(raw_id),
        name=str(raw.get("name") or raw.get("deviceDisplayName") or raw.get("modelDisplayName") or "Unknown Apple device"),
        kind="device",
        provider="icloud",
        latitude=_float_or_none(location.get("latitude")),
        longitude=_float_or_none(location.get("longitude")),
        accuracy_m=_float_or_none(location.get("horizontalAccuracy") or location.get("accuracy")),
        battery=_float_or_none(raw.get("batteryLevel")),
        battery_status=str(raw.get("batteryStatus") or raw.get("batteryStatusString") or "unknown"),
        last_seen=_timestamp_to_iso(location.get("timeStamp") or location.get("timestamp")),
        location_is_old=_bool_or_none(location.get("isOld") if "isOld" in location else raw.get("locationIsOld")),
        raw_redacted=_redact_raw(raw),
    )


def _public_asset_id(raw_id: Any) -> str:
    if raw_id in (None, ""):
        return "unknown"
    digest = hashlib.sha256(str(raw_id).encode("utf-8")).hexdigest()[:16]
    return f"icloud:{digest}"


def _iter_device_statuses(api: Any) -> Iterable[dict[str, Any]]:
    devices = getattr(api, "devices", [])
    if isinstance(devices, dict):
        iterator = devices.values()
    else:
        iterator = devices
    for device in iterator:
        if hasattr(device, "data"):
            status = device.data
        else:
            status = device.status() if hasattr(device, "status") else device
        if isinstance(status, dict):
            yield status


def _timestamp_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _redact_raw(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).replace("-", "_").lower() in SENSITIVE_RAW_KEYS:
                cleaned[key] = REDACTED
            else:
                cleaned[key] = _redact_raw(item)
        return redact_secrets(cleaned)
    if isinstance(value, list):
        return [_redact_raw(item) for item in value]
    return redact_secrets(value)
