from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import cache
from .icloud_provider import Provider
from .models import FindMyAsset
from .provider_factory import is_pyicloud_available, provider_from_env


@dataclass(slots=True)
class FindMyCore:
    provider: Provider = field(default_factory=provider_from_env)

    def doctor(self) -> dict[str, object]:
        return {
            "ok": True,
            "provider": self.provider.name,
            "transport": "local",
            "secrets_redacted": True,
            "live_probe_available": is_pyicloud_available(),
            "cache": cache.cache_info(),
        }

    def list_assets(
        self,
        *,
        max_age_minutes: float | None = None,
        skip_offline: bool = False,
    ) -> list[FindMyAsset]:
        # Try cache first
        cached = cache.load_assets()
        if cached is not None:
            assets = cached
        else:
            assets = self.provider.list_assets()
            cache.save_assets(assets)

        return self._filter_assets(assets, max_age_minutes=max_age_minutes, skip_offline=skip_offline)

    def locate(
        self,
        name: str,
        *,
        max_age_minutes: float | None = None,
        skip_offline: bool = False,
    ) -> FindMyAsset | None:
        needle = name.casefold()
        for asset in self.list_assets(max_age_minutes=max_age_minutes, skip_offline=skip_offline):
            if asset.name.casefold() == needle or asset.id.casefold() == needle:
                return asset
        return None

    @staticmethod
    def _filter_assets(
        assets: list[FindMyAsset],
        *,
        max_age_minutes: float | None = None,
        skip_offline: bool = False,
    ) -> list[FindMyAsset]:
        if not max_age_minutes and not skip_offline:
            return assets
        result: list[FindMyAsset] = []
        for asset in assets:
            if asset.is_stale(max_age_minutes=max_age_minutes):
                continue
            result.append(asset)
        return result


def make_error_payload(message: str, error_type: str = "error") -> dict[str, object]:
    """Build a consistent, privacy-safe error dict for CLI responses."""
    return {
        "ok": False,
        "error": message,
        "error_type": error_type,
        "secret_safe": True,
    }
