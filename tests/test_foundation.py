"""Tests for configuration and the no-cost demo provider."""

from documind.config import Settings
from documind.extraction.provider import MockProvider


def test_settings_default_to_demo(monkeypatch):
    monkeypatch.delenv("DOCUMIND_MODE", raising=False)
    monkeypatch.delenv("DOCUMIND_MODEL", raising=False)

    assert Settings.from_environment() == Settings(mode="demo", model="gpt-4o-mini")


def test_invalid_mode_falls_back_to_demo(monkeypatch):
    monkeypatch.setenv("DOCUMIND_MODE", "unexpected")

    assert Settings.from_environment().mode == "demo"


def test_settings_load_local_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DOCUMIND_MODE", raising=False)
    monkeypatch.delenv("DOCUMIND_MODEL", raising=False)
    (tmp_path / ".env").write_text(
        "DOCUMIND_MODE=live\nDOCUMIND_MODEL=local-model\n", encoding="utf-8"
    )

    assert Settings.from_environment() == Settings(mode="live", model="local-model")


def test_host_environment_overrides_local_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "DOCUMIND_MODE=live\nDOCUMIND_MODEL=local-model\n", encoding="utf-8"
    )
    monkeypatch.setenv("DOCUMIND_MODE", "demo")
    monkeypatch.setenv("DOCUMIND_MODEL", "host-model")

    assert Settings.from_environment() == Settings(mode="demo", model="host-model")


def test_demo_provider_needs_no_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DOCUMIND_MODE", raising=False)
    monkeypatch.delenv("DOCUMIND_MODEL", raising=False)

    assert Settings.from_environment().mode == "demo"
    assert MockProvider().extract("sample text").message.startswith("Demo mode")


def test_mock_provider_is_deterministic_and_does_not_echo_input():
    provider = MockProvider()

    first = provider.extract("private document text")
    second = provider.extract("different document text")

    assert first == second
    assert "private document text" not in first.message
