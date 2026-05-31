from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from findmy_agent_bridge.provider_factory import ProviderConfigError, create_pyicloud_provider


class FakePyiCloudService:
    instances = []

    def __init__(self, apple_id, password, cookie_directory):
        self.apple_id = apple_id
        self.password = password
        self.cookie_directory = cookie_directory
        self.requires_2fa = True
        self.validated_codes = []
        self.trusted = False
        self.devices = []
        FakePyiCloudService.instances.append(self)

    def validate_2fa_code(self, code):
        self.validated_codes.append(code)
        if code == "123456":
            self.requires_2fa = False
            return True
        return False

    def trust_session(self):
        self.trusted = True
        return True


@pytest.fixture
def fake_pyicloud(monkeypatch):
    FakePyiCloudService.instances = []
    monkeypatch.setitem(sys.modules, "pyicloud", SimpleNamespace(PyiCloudService=FakePyiCloudService))
    return FakePyiCloudService


def test_create_pyicloud_provider_uses_callback_code_in_same_api_session(tmp_path, fake_pyicloud):
    provider = create_pyicloud_provider(
        apple_id="user@example.invalid",
        password="pw",
        cookie_dir=tmp_path,
        code_provider=lambda: "123 456",
    )

    assert provider.name == "icloud"
    assert len(fake_pyicloud.instances) == 1
    api = fake_pyicloud.instances[0]
    assert api.validated_codes == ["123456"]
    assert api.trusted is True


def test_create_pyicloud_provider_reports_2fa_required_when_no_code_provider(tmp_path, fake_pyicloud):
    with pytest.raises(ProviderConfigError, match="2FA_REQUIRED"):
        create_pyicloud_provider(apple_id="user@example.invalid", password="pw", cookie_dir=tmp_path)


def test_create_pyicloud_provider_reports_2fa_failed_for_bad_code(tmp_path, fake_pyicloud):
    with pytest.raises(ProviderConfigError, match="2FA_FAILED"):
        create_pyicloud_provider(
            apple_id="user@example.invalid",
            password="pw",
            cookie_dir=tmp_path,
            code_provider=lambda: "000000",
        )
