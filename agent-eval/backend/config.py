from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_local_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


def get_settings() -> Settings:
    _load_local_env()
    return Settings(
        api_key=os.getenv("DATAPILOT_API_KEY", ""),
        base_url=os.getenv("DATAPILOT_BASE_URL", "https://yunwu.ai/v1").rstrip("/"),
        model=os.getenv("DATAPILOT_MODEL", "gpt-5.4-nano-2026-03-17"),
        timeout_seconds=int(os.getenv("DATAPILOT_TIMEOUT_SECONDS", "120")),
    )
