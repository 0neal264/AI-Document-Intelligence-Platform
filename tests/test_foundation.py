"""Tests for Gemini configuration and the offline mock provider."""

from documind.config import Settings
from documind.extraction import MockProvider

CONFIG_ENV = (
    "APP_ENV",
    "EXTRACTION_PROVIDER",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
)


def test_settings_default_to_offline_mock(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)

    assert Settings.from_environment() == Settings()


def test_invalid_provider_falls_back_to_mock(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("EXTRACTION_PROVIDER", "unknown")

    assert Settings.from_environment().extraction_provider == "mock"


def test_settings_load_local_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "APP_ENV=development\n"
        "EXTRACTION_PROVIDER=gemini\n"
        "GEMINI_API_KEY=local-test-key\n"
        "GEMINI_MODEL=gemini-test-model\n",
        encoding="utf-8",
    )

    settings = Settings.from_environment()
    assert settings.app_env == "development"
    assert settings.extraction_provider == "gemini"
    assert settings.gemini_api_key == "local-test-key"
    assert settings.gemini_model == "gemini-test-model"
    assert "local-test-key" not in repr(settings)


def test_host_environment_overrides_local_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "APP_ENV=production\n"
        "EXTRACTION_PROVIDER=gemini\n"
        "GEMINI_API_KEY=dotenv-key\n"
        "GEMINI_MODEL=dotenv-model\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EXTRACTION_PROVIDER", "mock")
    monkeypatch.setenv("GEMINI_API_KEY", "host-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "host-model")

    settings = Settings.from_environment()
    assert settings.app_env == "development"
    assert settings.extraction_provider == "mock"
    assert settings.gemini_api_key == "host-test-key"
    assert settings.gemini_model == "host-model"


def test_mock_provider_needs_no_gemini_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)

    assert not (tmp_path / ".env").exists()
    assert Settings.from_environment().gemini_api_key is None
    assert MockProvider().extract("sample text").message.startswith("Demo mode")


def test_mock_provider_works_without_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = MockProvider().extract("sample text")

    assert result.message.startswith("Demo mode")


def test_mock_provider_is_deterministic_and_does_not_echo_input():
    provider = MockProvider()

    first = provider.extract("private document text")
    second = provider.extract("different document text")

    assert first == second
    assert "private document text" not in first.message
