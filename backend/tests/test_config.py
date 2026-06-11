from pathlib import Path

from src.core.config import AppSettings, normalize_database_url, reload_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_load_settings_from_test_env() -> None:
    settings = reload_settings(BACKEND_DIR / "tests" / "fixtures" / "test.env")
    assert settings.port == 8099
    assert settings.chord_provider == "mock"
    assert settings.llm_model_chat == "qwen-plus"
    assert "localhost:5199" in settings.cors_origins[0]


def test_normalize_database_url_memory() -> None:
    url = normalize_database_url("sqlite+aiosqlite:///:memory:")
    assert url == "sqlite+aiosqlite:///:memory:"


def test_app_settings_defaults() -> None:
    settings = AppSettings()
    assert settings.guest_session_max_age_days == 30
