"""Small, dependency-free application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Settings read from environment variables, with safe demo defaults."""

    mode: str = "demo"
    model: str = "gpt-4o-mini"

    @classmethod
    def from_environment(cls) -> "Settings":
        mode = os.getenv("DOCUMIND_MODE", "demo").strip().lower()
        if mode not in {"demo", "live"}:
            mode = "demo"
        model = os.getenv("DOCUMIND_MODEL", "gpt-4o-mini").strip()
        return cls(mode=mode, model=model or "gpt-4o-mini")
