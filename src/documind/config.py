"""Application configuration loaded from the environment and local .env file."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Gemini app settings with offline mock defaults."""

    app_env: str = "development"
    extraction_provider: str = "mock"
    gemini_api_key: str | None = field(default=None, repr=False)
    gemini_model: str = "gemini-3.5-flash-lite"

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env", override=False)
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        provider = os.getenv("EXTRACTION_PROVIDER", "mock").strip().lower()
        if provider not in {"mock", "gemini"}:
            provider = "mock"
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        return cls(
            app_env=app_env or "development",
            extraction_provider=provider,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model or "gemini-3.5-flash-lite",
        )
