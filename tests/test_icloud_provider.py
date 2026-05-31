from __future__ import annotations

from findmy_agent_bridge.icloud_provider import (
    PyiCloudDevicesProvider,
    normalize_pyicloud_device,
)


def test_normalize_pyicloud_device_redacts_raw_and_maps_location():
    raw = {
        "id": "device-1",
        "name": "Corrado iPhone",
        "deviceDisplayName": "iPhone 15",
        "location": {
            "latitude": 45.4642,
            "longitude": 9.19,
            "horizontalAccuracy": 12.5,
            "timeStamp": 1780142400000,
            "isOld": False,
        },
        "batteryLevel": 0.83,
        "batteryStatus": "Charging",
        "owner": "corrado@example.com",
        "token": "secret-token-value",
        "deviceDiscoveryId": "C4:B3:49:E7:13:3B",
        "baUUID": "9F5205D1-B31B-4486-A675-D7D64E8F689A",
        "commandLookupId": "lookup-secret-id",
    }

    asset = normalize_pyicloud_device(raw)

    assert asset.id.startswith("icloud:")
    assert asset.id != "device-1"
    assert asset.name == "Corrado iPhone"
    assert asset.kind == "device"
    assert asset.provider == "icloud"
    assert asset.latitude == 45.4642
    assert asset.longitude == 9.19
    assert asset.accuracy_m == 12.5
    assert asset.battery == 0.83
    assert asset.battery_status == "Charging"
    assert asset.last_seen == "2026-05-30T12:00:00Z"
    assert asset.location_is_old is False
    assert asset.raw_redacted["id"] == "[REDACTED]"
    assert asset.raw_redacted["deviceDiscoveryId"] == "[REDACTED]"
    assert asset.raw_redacted["baUUID"] == "[REDACTED]"
    assert asset.raw_redacted["commandLookupId"] == "[REDACTED]"
    assert "corrado@example.com" not in str(asset.raw_redacted)
    assert "secret-token-value" not in str(asset.raw_redacted)


class FakeDevice:
    def __init__(self, status: dict[str, object]):
        self._status = status

    def status(self) -> dict[str, object]:
        return {key: self._status.get(key) for key in ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]}


class FakeAppleDevice:
    def __init__(self, data: dict[str, object]):
        self.data = data

    def status(self) -> dict[str, object]:
        raise AssertionError("provider must use AppleDevice.data, not AppleDevice.status() subset")


class FakeApi:
    devices = {
        "a": FakeDevice({"id": "a", "name": "iPhone", "location": None}),
        "b": FakeDevice({"id": "b", "name": "iPad", "location": None}),
    }


class FakeAppleDeviceApi:
    devices = {
        "iphone": FakeAppleDevice(
            {
                "id": "iphone-real-id",
                "name": "iPhone",
                "location": {
                    "latitude": 41.9,
                    "longitude": 12.5,
                    "horizontalAccuracy": 7,
                    "timeStamp": 1780142400000,
                    "isOld": False,
                },
                "batteryLevel": 0.11,
                "deviceStatus": "200",
            }
        )
    }


def test_pyicloud_provider_lists_fake_devices():
    provider = PyiCloudDevicesProvider(api=FakeApi())

    assets = provider.list_assets()

    assert [asset.name for asset in assets] == ["iPhone", "iPad"]
    assert {asset.provider for asset in assets} == {"icloud"}


def test_pyicloud_provider_uses_full_apple_device_data_not_status_subset():
    provider = PyiCloudDevicesProvider(api=FakeAppleDeviceApi())

    assets = provider.list_assets()

    assert len(assets) == 1
    assert assets[0].id.startswith("icloud:")
    assert assets[0].id != "iphone-real-id"
    assert assets[0].latitude == 41.9
    assert assets[0].longitude == 12.5
    assert assets[0].accuracy_m == 7
    assert assets[0].last_seen == "2026-05-30T12:00:00Z"
