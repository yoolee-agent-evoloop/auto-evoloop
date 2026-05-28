from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "bearer",
    "client_secret",
    "cookie",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "session",
    "token",
)


def clean_trace_file(input_path: Path, output_path: Path) -> None:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(clean_trace(data), indent=2, sort_keys=True), encoding="utf-8")


def clean_trace(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = clean_trace(item)
        return cleaned
    if isinstance(value, list):
        return [clean_trace(item) for item in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)
