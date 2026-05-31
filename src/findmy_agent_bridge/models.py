from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

AssetKind = Literal["device", "item", "unknown"]


@dataclass(slots=True)
class FindMyAsset:
    id: str
    name: str
    kind: AssetKind
    provider: str
    latitude: float | None = None
    longitude: float | None = None
    accuracy_m: float | None = None
    battery: float | None = None
    battery_status: str = "unknown"
    last_seen: str | None = None
    location_is_old: bool | None = None
    raw_redacted: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_raw: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw_redacted", None)
        return data

    def is_stale(self, max_age_minutes: float | None = None) -> bool:
        """Return True if the location is reported as old or last_seen exceeds max_age."""
        if self.location_is_old:
            return True
        if max_age_minutes is not None and max_age_minutes > 0 and self.last_seen:
            try:
                seen = datetime.fromisoformat(self.last_seen.replace("Z", "+00:00"))
                age = (datetime.now(UTC) - seen).total_seconds() / 60
                return age > max_age_minutes
            except (ValueError, TypeError):
                pass
        return False
