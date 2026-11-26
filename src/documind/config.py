"""Application configuration loaded from the environment and local .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Settings read from environment variables, with safe demo defaults."""

    mode: str = "demo"
    model: str = "gpt-4o-mini"

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env", override=False)
        mode = os.getenv("DOCUMIND_MODE", "demo").strip().lower()
        if mode not in {"demo", "live"}:
            mode = "demo"
        model = os.getenv("DOCUMIND_MODEL", "gpt-4o-mini").strip()
        return cls(mode=mode, model=model or "gpt-4o-mini")
