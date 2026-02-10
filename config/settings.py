"""
Глобальные настройки приложения.

Все параметры загружаются из .env через Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Общий конфиг приложения.

    Все поля по умолчанию читаются из переменных окружения / .env.
    """

    # Telegram
    telegram_bot_token: str

    # LLM / OpenAI / OpenRouter и т.п.
    llm_api_url: str
    llm_api_key: str
    llm_model: str

    # База данных
    database_url: str = "sqlite:///./db.sqlite3"

    # Прочие опции (по мере надобности)
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Явное соответствие имен env-переменных (если нужно подстроиться под уже существующий .env)
        env_prefix="",  # не добавляем префикс
        alias_generator=None,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Кешированный доступ к настройкам.

    Использование:
        from config.settings import get_settings
        settings = get_settings()
        token = settings.telegram_bot_token
    """

    return Settings()

