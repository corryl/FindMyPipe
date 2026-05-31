from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from .core import FindMyCore, make_error_payload
from .provider_factory import (
    DEFAULT_SESSION_DIR,
    ProviderConfigError,
    create_pyicloud_provider,
    provider_from_name,
)

app = typer.Typer(no_args_is_help=True, help="Local Find My bridge for AI agents.")
ProviderOption = Annotated[str, typer.Option("--provider", help="Provider: mock or icloud.")]
JsonOption = Annotated[bool, typer.Option("--json", help="Print JSON output.")]
RawOption = Annotated[bool, typer.Option("--include-raw", help="Include debug raw payload after redaction. Off by default for privacy.")]
MaxAgeOption = Annotated[float | None, typer.Option("--max-age", help="Filter out assets older than this many minutes.")]
SkipOfflineOption = Annotated[bool, typer.Option("--skip-offline", help="Filter out assets reported as offline/stale.")]


@app.command()
def doctor(
    provider: ProviderOption = "mock",
    as_json: JsonOption = False,
) -> None:
    core = _core_or_exit(provider)
    _emit(core.doctor(), as_json)


@app.command("list")
def list_assets(
    provider: ProviderOption = "mock",
    as_json: JsonOption = False,
    include_raw: RawOption = False,
    max_age: MaxAgeOption = None,
    skip_offline: SkipOfflineOption = False,
) -> None:
    core = _core_or_exit(provider)
    assets = core.list_assets(max_age_minutes=max_age, skip_offline=skip_offline)
    payload = {"assets": [asset.to_dict(include_raw=include_raw) for asset in assets]}
    _emit(payload, as_json)


@app.command()
def locate(
    name: str,
    provider: ProviderOption = "mock",
    as_json: JsonOption = False,
    include_raw: RawOption = False,
    max_age: MaxAgeOption = None,
    skip_offline: SkipOfflineOption = False,
) -> None:
    core = _core_or_exit(provider)
    asset = core.locate(name, max_age_minutes=max_age, skip_offline=skip_offline)
    payload = {"asset": None if asset is None else asset.to_dict(include_raw=include_raw)}
    _emit(payload, as_json)


@app.command()
def login(
    apple_id: Annotated[str, typer.Option(prompt=True, hide_input=False, help="Apple ID. Never logged.")],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True, help="Apple password. Never logged.")],
    code: Annotated[str | None, typer.Option("--code", help="Optional 2FA code. If omitted and required, rerun with --code.")] = None,
    cookie_dir: Annotated[Path, typer.Option("--cookie-dir", help="Private pyicloud cookie/session directory.")] = DEFAULT_SESSION_DIR,
    as_json: JsonOption = False,
) -> None:
    try:
        provider = create_pyicloud_provider(
            apple_id=apple_id,
            password=password,
            cookie_dir=cookie_dir,
            code=code,
            code_provider=None if code else _prompt_2fa_code,
        )
        count = len(provider.list_assets())
    except ProviderConfigError as exc:
        message = str(exc)
        payload = {
            "ok": False,
            "error": message,
            "error_type": "login_error",
            "secret_safe": True,
            "next_step": "Rerun with --code <2FA>" if message == "2FA_REQUIRED" else "Check dependency/configuration",
        }
        _emit(payload, as_json)
        raise typer.Exit(code=2) from exc
    payload = {"ok": True, "provider": "icloud", "assets_seen": count, "cookie_dir": str(cookie_dir), "secret_safe": True}
    _emit(payload, as_json)


def _prompt_2fa_code() -> str:
    typer.echo("2FA challenge received. Enter the code shown on your Apple device.")
    return typer.prompt("2FA code", hide_input=False)


def _core_or_exit(provider_name: str) -> FindMyCore:
    try:
        return FindMyCore(provider=provider_from_name(provider_name))
    except ProviderConfigError as exc:
        typer.echo(json.dumps(make_error_payload(str(exc), "configuration_error"), sort_keys=True), err=True)
        raise typer.Exit(code=2) from exc


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    app()
