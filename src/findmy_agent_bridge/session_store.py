from __future__ import annotations

from pathlib import Path


def ensure_private_file(path: str | Path, content: str) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.parent.chmod(0o700)
    file_path.write_text(content)
    file_path.chmod(0o600)
    return file_path
