import json
from typer.testing import CliRunner

from findmy_agent_bridge.cli import app


runner = CliRunner()


def test_doctor_reports_mock_provider_ready():
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["transport"] == "local"
    assert payload["secrets_redacted"] is True
    assert "cache" in payload


def test_list_returns_empty_mock_assets_by_default():
    result = runner.invoke(app, ["list", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"assets": []}


def test_icloud_provider_requires_env_credentials_without_leaking_secrets(monkeypatch):
    monkeypatch.delenv("FINDMY_APPLE_ID", raising=False)
    monkeypatch.delenv("APPLE_ID", raising=False)

    result = runner.invoke(app, ["list", "--provider", "icloud", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stderr)
    assert payload == {
        "ok": False,
        "error": "FINDMY_APPLE_ID missing",
        "error_type": "configuration_error",
        "secret_safe": True,
    }


def test_list_with_max_age_flag(monkeypatch):
    result = runner.invoke(app, ["list", "--json", "--max-age", "30"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"assets": []}


def test_list_with_skip_offline_flag():
    result = runner.invoke(app, ["list", "--json", "--skip-offline"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"assets": []}


def test_locate_with_max_age_flag():
    result = runner.invoke(app, ["locate", "iPhone", "--json", "--max-age", "60"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"asset": None}


def test_locate_with_skip_offline_flag():
    result = runner.invoke(app, ["locate", "iPad", "--json", "--skip-offline"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"asset": None}
