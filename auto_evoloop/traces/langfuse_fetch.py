from __future__ import annotations

import os


def require_langfuse_env() -> dict[str, str]:
    required = {
        "base_url": "AUTO_EVOLOOP_LANGFUSE_BASE_URL",
        "public_key": "AUTO_EVOLOOP_LANGFUSE_PUBLIC_KEY",
        "secret_key": "AUTO_EVOLOOP_LANGFUSE_SECRET_KEY",
    }
    values: dict[str, str] = {}
    missing: list[str] = []
    for logical_name, env_name in required.items():
        value = os.getenv(env_name)
        if value:
            values[logical_name] = value
        else:
            missing.append(env_name)
    if missing:
        raise RuntimeError("Missing Langfuse configuration: " + ", ".join(missing))
    return values
