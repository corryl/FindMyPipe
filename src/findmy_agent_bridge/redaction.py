from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(password\s*[=:]\s*)\S+"),
    re.compile(r"(?i)(token\s*[=:]\s*)\S+"),
    re.compile(r"(?i)(secret\s*[=:]\s*)\S+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\b\d{6}\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern in _PATTERNS:
            redacted = pattern.sub(lambda m: _replacement(m), redacted)
        return redacted
    if isinstance(value, dict):
        return {k: redact_secrets(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value


def _replacement(match: re.Match[str]) -> str:
    text = match.group(0)
    if "=" in text or ":" in text:
        sep = "=" if "=" in text else ":"
        prefix = text.split(sep, 1)[0]
        return f"{prefix}{sep}{REDACTED}"
    if text.lower().startswith("bearer"):
        return f"Bearer {REDACTED}"
    return REDACTED
