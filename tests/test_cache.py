from __future__ import annotations

import json
from pathlib import Path

from findmy_agent_bridge import cache
from findmy_agent_bridge.models import FindMyAsset


def test_cache_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINDMY_CACHE_TTL", raising=False)
    monkeypatch.delenv("FINDMY_CACHE_FILE", raising=False)

    assert cache.load_assets() is None


def test_cache_disabled_when_ttl_is_zero(monkeypatch):
    monkeypatch.setenv("FINDMY_CACHE_TTL", "0")

    assert cache.load_assets() is None


def test_cache_save_and_load_roundtrip(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    assets = [
        FindMyAsset(id="a1", name="iPhone", kind="device", provider="icloud", latitude=45.1, longitude=9.2),
        FindMyAsset(id="a2", name="iPad", kind="device", provider="icloud"),
    ]

    cache.save_assets(assets)
    assert cache_file.is_file()

    loaded = cache.load_assets()
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].id == "a1"
    assert loaded[0].name == "iPhone"
    assert loaded[0].latitude == 45.1
    assert loaded[0].longitude == 9.2
    assert loaded[1].id == "a2"
    assert loaded[1].name == "iPad"


def test_cache_expired_returns_none(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    fake_now = [1000.0]
    monkeypatch.setattr(cache, "_now", lambda: fake_now[0])

    assets = [FindMyAsset(id="a1", name="iPhone", kind="device", provider="icloud")]
    cache.save_assets(assets)

    # Advance time past TTL
    fake_now[0] = 1000.0 + 301

    loaded = cache.load_assets()
    assert loaded is None


def test_cache_corrupt_file_returns_none(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    cache_file.write_text("not valid json")

    loaded = cache.load_assets()
    assert loaded is None


def test_cache_file_permissions(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    assets = [FindMyAsset(id="a1", name="iPhone", kind="device", provider="icloud")]
    cache.save_assets(assets)

    assert oct(cache_file.stat().st_mode & 0o777) == "0o600"
    assert oct(cache_file.parent.stat().st_mode & 0o777) == "0o700"


def test_cache_info_reports_disabled_when_ttl_zero(monkeypatch):
    monkeypatch.setenv("FINDMY_CACHE_TTL", "0")

    info = cache.cache_info()
    assert info["enabled"] is False
    assert info["state"] == "empty"


def test_cache_info_reports_fresh_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    fake_now = [1000.0]
    monkeypatch.setattr(cache, "_now", lambda: fake_now[0])

    payload = {
        "_cached_at": fake_now[0],
        "_ttl": 300,
        "assets": [{"id": "a1", "name": "iPhone", "kind": "device", "provider": "icloud"}],
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload))
    cache_file.chmod(0o600)

    info = cache.cache_info()
    assert info["enabled"] is True
    assert info["state"] == "fresh"
    assert info["asset_count"] == 1


def test_cache_info_reports_stale_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "1")

    fake_now = [1000.0]
    monkeypatch.setattr(cache, "_now", lambda: fake_now[0])

    payload = {
        "_cached_at": fake_now[0] - 10,  # 10 seconds ago
        "_ttl": 1,
        "assets": [],
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload))
    cache_file.chmod(0o600)

    info = cache.cache_info()
    assert info["state"] == "stale"


def test_cache_info_reports_corrupt_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "300")

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("broken")
    cache_file.chmod(0o600)

    info = cache.cache_info()
    assert info["state"] == "corrupt"


def test_save_cache_skipped_when_ttl_zero(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("FINDMY_CACHE_FILE", str(cache_file))
    monkeypatch.setenv("FINDMY_CACHE_TTL", "0")

    assets = [FindMyAsset(id="a1", name="iPhone", kind="device", provider="icloud")]
    cache.save_assets(assets)

    assert not cache_file.exists()
