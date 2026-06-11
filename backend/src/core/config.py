"""应用配置：从 backend/.env 加载，经 ConfigManager 管理。"""

from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic import Field

from pycore.core import BaseSettings, ConfigManager

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = BACKEND_DIR / ".env"

_config = ConfigManager["AppSettings"]()
_settings: "AppSettings | None" = None

DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:5199",
    "http://127.0.0.1:5199",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]


class AppSettings(BaseSettings):
    dashscope_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model_chat: str = "qwen-plus"
    llm_model_score: str = "qwen-turbo"
    database_url: str = "sqlite+aiosqlite:///./data/ai-music-companion.db"
    chord_provider: str = "mock"
    guest_session_secret: str = "change-me-guest-secret"
    guest_session_max_age_days: int = 30
    host: str = "0.0.0.0"
    port: int = 8099
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    netease_cookie_path: str = ""


def normalize_database_url(url: str, backend_dir: Path = BACKEND_DIR) -> str:
    if url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite"):
        url = "sqlite+aiosqlite:///" + url.removeprefix("sqlite:///")

    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return url

    path_part = url[len(prefix) :]
    if path_part == ":memory:":
        return url

    if path_part.startswith("/"):
        abs_path = Path(path_part)
    else:
        if path_part.startswith("./"):
            path_part = path_part[2:]
        abs_path = (backend_dir / path_part).resolve()
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{abs_path}"


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_file_to_settings_dict(env_path: Path) -> dict[str, Any]:
    if not env_path.is_file():
        raise FileNotFoundError(f"Config file not found: {env_path}")

    raw = dotenv_values(env_path)
    return {
        "dashscope_api_key": raw.get("DASHSCOPE_API_KEY", ""),
        "llm_base_url": raw.get("LLM_BASE_URL", AppSettings.model_fields["llm_base_url"].default),
        "llm_model_chat": raw.get("LLM_MODEL_CHAT", AppSettings.model_fields["llm_model_chat"].default),
        "llm_model_score": raw.get(
            "LLM_MODEL_SCORE", AppSettings.model_fields["llm_model_score"].default
        ),
        "database_url": normalize_database_url(
            raw.get("DATABASE_URL", AppSettings.model_fields["database_url"].default)  # type: ignore[arg-type]
        ),
        "chord_provider": raw.get(
            "CHORD_PROVIDER", AppSettings.model_fields["chord_provider"].default
        ),
        "guest_session_secret": raw.get("GUEST_SESSION_SECRET", "change-me-guest-secret"),
        "guest_session_max_age_days": int(
            raw.get(
                "GUEST_SESSION_MAX_AGE_DAYS",
                AppSettings.model_fields["guest_session_max_age_days"].default,
            )
        ),
        "host": raw.get("HOST", AppSettings.model_fields["host"].default),
        "port": int(raw.get("PORT", AppSettings.model_fields["port"].default)),
        "debug": str(raw.get("DEBUG", "false")).lower() in {"1", "true", "yes"},
        "cors_origins": _parse_cors_origins(raw.get("CORS_ORIGINS")),
        "netease_cookie_path": raw.get("NETEASE_COOKIE_PATH", ""),
    }


def load_settings(env_path: Path | None = None) -> AppSettings:
    global _settings
    path = env_path or DEFAULT_ENV_PATH
    _config.load_from_dict(AppSettings, _env_file_to_settings_dict(path))
    _settings = _config.settings
    return _settings


def get_settings() -> AppSettings:
    if _settings is None:
        return load_settings()
    return _settings


def reload_settings(env_path: Path) -> AppSettings:
    ConfigManager.reset()
    global _config
    _config = ConfigManager["AppSettings"]()
    return load_settings(env_path)


settings = load_settings()
