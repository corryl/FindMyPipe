from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from collections.abc import Callable
from typing import Any

from .icloud_provider import MockProvider, Provider, PyiCloudDevicesProvider

DEFAULT_SESSION_DIR = Path.home() / ".local" / "state" / "findmypipe" / "icloud"


class ProviderConfigError(RuntimeError):
    pass


def is_pyicloud_available() -> bool:
    return importlib.util.find_spec("pyicloud") is not None


def provider_from_name(name: str = "mock") -> Provider:
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockProvider()
    if normalized in {"icloud", "icloud_devices", "pyicloud"}:
        return pyicloud_provider_from_env()
    raise ProviderConfigError(f"Unknown provider: {name}")


def provider_from_env(default: str = "mock") -> Provider:
    return provider_from_name(os.getenv("FINDMY_AGENT_PROVIDER", default))


def pyicloud_provider_from_env() -> PyiCloudDevicesProvider:
    apple_id = os.getenv("FINDMY_APPLE_ID") or os.getenv("APPLE_ID")
    password = os.getenv("FINDMY_APPLE_PASSWORD") or os.getenv("APPLE_PASSWORD")
    cookie_dir = Path(os.getenv("FINDMY_COOKIE_DIR", str(DEFAULT_SESSION_DIR))).expanduser()
    if not apple_id:
        raise ProviderConfigError("FINDMY_APPLE_ID missing")
    if not password:
        raise ProviderConfigError("FINDMY_APPLE_PASSWORD missing")
    return create_pyicloud_provider(apple_id=apple_id, password=password, cookie_dir=cookie_dir)


def create_pyicloud_provider(
    *,
    apple_id: str,
    password: str | None,
    cookie_dir: str | Path = DEFAULT_SESSION_DIR,
    code: str | None = None,
    code_provider: Callable[[], str | None] | None = None,
) -> PyiCloudDevicesProvider:
    try:
        from pyicloud import PyiCloudService  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise ProviderConfigError("pyicloud not installed; install findmypipe[live]") from exc

    cookie_path = Path(cookie_dir).expanduser()
    cookie_path.mkdir(parents=True, exist_ok=True)
    cookie_path.chmod(0o700)
    api: Any = PyiCloudService(apple_id, password, cookie_directory=str(cookie_path))

    if getattr(api, "requires_2fa", False):
        verification_code = _normalize_2fa_code(code)
        if verification_code is None and code_provider is not None:
            verification_code = _normalize_2fa_code(code_provider())
        if verification_code is None:
            raise ProviderConfigError("2FA_REQUIRED")
        ok = api.validate_2fa_code(verification_code)
        if not ok:
            raise ProviderConfigError("2FA_FAILED")
        try:
            api.trust_session()
        except Exception:
            # Trust is best-effort; listing devices can still work for this session.
            pass

    return PyiCloudDevicesProvider(api=api)


def _normalize_2fa_code(code: str | None) -> str | None:
    if code is None:
        return None
    normalized = "".join(str(code).split())
    return normalized or None
