from __future__ import annotations

from datetime import UTC, datetime, timedelta

from findmy_agent_bridge.core import FindMyCore, make_error_payload
from findmy_agent_bridge.icloud_provider import MockProvider, Provider
from findmy_agent_bridge.models import FindMyAsset
from findmy_agent_bridge.redaction import redact_secrets
from findmy_agent_bridge.session_store import ensure_private_file


def test_asset_serializes_normalized_location():
    asset = FindMyAsset(
        id="abc",
        name="Tracker",
        kind="item",
        provider="mock",
        latitude=45.1,
        longitude=9.2,
        accuracy_m=12,
        battery=0.7,
        battery_status="normal",
        last_seen="2026-05-30T10:00:00Z",
        location_is_old=False,
    )

    assert asset.to_dict() == {
        "id": "abc",
        "name": "Tracker",
        "kind": "item",
        "provider": "mock",
        "latitude": 45.1,
        "longitude": 9.2,
        "accuracy_m": 12,
        "battery": 0.7,
        "battery_status": "normal",
        "last_seen": "2026-05-30T10:00:00Z",
        "location_is_old": False,
    }


def test_asset_can_include_raw_only_when_explicitly_requested():
    asset = FindMyAsset(id="abc", name="Tracker", kind="item", provider="mock", raw_redacted={"id": "[REDACTED]"})

    assert "raw_redacted" not in asset.to_dict()
    assert asset.to_dict(include_raw=True)["raw_redacted"] == {"id": "[REDACTED]"}


def test_redact_secrets_removes_credentials():
    text = "password=hello token=abc123 Bearer xyz code 123456 apple_id=user@example.com"

    redacted = redact_secrets(text)

    assert "hello" not in redacted
    assert "abc123" not in redacted
    assert "xyz" not in redacted
    assert "123456" not in redacted
    assert "user@example.com" not in redacted
    assert "[REDACTED]" in redacted


def test_ensure_private_file_sets_0600(tmp_path):
    path = tmp_path / "sessions" / "icloud.cookies"

    ensure_private_file(path, "session-data")

    assert path.read_text() == "session-data"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert oct(path.parent.stat().st_mode & 0o777) == "0o700"


# --- is_stale ---


def test_asset_is_stale_when_location_is_old():
    asset = FindMyAsset(id="a", name="Old", kind="device", provider="mock", location_is_old=True)
    assert asset.is_stale() is True


def test_asset_is_not_stale_when_location_is_fresh():
    asset = FindMyAsset(id="a", name="Fresh", kind="device", provider="mock", location_is_old=False)
    assert asset.is_stale() is False


def test_asset_is_stale_when_exceeds_max_age():
    old_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    asset = FindMyAsset(id="a", name="Old", kind="device", provider="mock", last_seen=old_time, location_is_old=False)
    assert asset.is_stale(max_age_minutes=60) is True


def test_asset_is_not_stale_within_max_age():
    recent_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    asset = FindMyAsset(id="a", name="Recent", kind="device", provider="mock", last_seen=recent_time, location_is_old=False)
    assert asset.is_stale(max_age_minutes=60) is False


def test_asset_with_no_location_is_not_stale():
    asset = FindMyAsset(id="a", name="NoLoc", kind="device", provider="mock", last_seen=None, location_is_old=None)
    assert asset.is_stale(max_age_minutes=30) is False


# --- filtering ---


class _TestProvider:
    name = "test"

    def __init__(self, assets: list[FindMyAsset] | None = None):
        self._assets = assets

    def list_assets(self) -> list[FindMyAsset]:
        return self._assets or []


def test_list_assets_filters_by_max_age():
    recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    old = (datetime.now(UTC) - timedelta(hours=3)).isoformat().replace("+00:00", "Z")

    provider = _TestProvider([
        FindMyAsset(id="r", name="Recent", kind="device", provider="test", last_seen=recent, location_is_old=False),
        FindMyAsset(id="o", name="Old", kind="device", provider="test", last_seen=old, location_is_old=False),
    ])

    core = FindMyCore(provider=provider)
    assets = core.list_assets(max_age_minutes=60)

    assert len(assets) == 1
    assert assets[0].id == "r"


def test_list_assets_filters_offline():
    provider = _TestProvider([
        FindMyAsset(id="a", name="Online", kind="device", provider="test", location_is_old=False),
        FindMyAsset(id="b", name="Offline", kind="device", provider="test", location_is_old=True),
    ])

    core = FindMyCore(provider=provider)
    assets = core.list_assets(skip_offline=True)

    assert len(assets) == 1
    assert assets[0].id == "a"


def test_locate_respects_max_age_filter():
    recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    old = (datetime.now(UTC) - timedelta(hours=3)).isoformat().replace("+00:00", "Z")

    provider = _TestProvider([
        FindMyAsset(id="r", name="Recent", kind="device", provider="test", last_seen=recent, location_is_old=False),
        FindMyAsset(id="o", name="Old Asset", kind="device", provider="test", last_seen=old, location_is_old=False),
    ])

    core = FindMyCore(provider=provider)
    found = core.locate("Old Asset", max_age_minutes=60)

    assert found is None  # filtered out


# --- make_error_payload ---


def test_make_error_payload_has_expected_shape():
    payload = make_error_payload("Something went wrong", "test_error")

    assert payload == {
        "ok": False,
        "error": "Something went wrong",
        "error_type": "test_error",
        "secret_safe": True,
    }


def test_make_error_payload_default_error_type():
    payload = make_error_payload("Generic problem")

    assert payload["error_type"] == "error"
