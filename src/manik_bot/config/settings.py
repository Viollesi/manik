"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(ValueError):
    """Raised when application settings are invalid."""


class Settings(BaseSettings):
    """Runtime settings for the Telegram bot."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: str) -> str:
        """Validate that the bot token is filled in."""
        if not value or value == "replace_me":
            raise ValueError("Укажите BOT_TOKEN в файле .env")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Validate timezone name."""
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Укажите корректный TIMEZONE в файле .env") from error
        return value

    @field_validator("admin_ids")
    @classmethod
    def validate_admin_ids(cls, value: str) -> str:
        """Validate comma-separated admin Telegram IDs."""
        try:
            tuple(int(item.strip()) for item in value.split(",") if item.strip())
        except ValueError as error:
            raise ValueError("Укажите ADMIN_IDS через запятую, только числа") from error
        return value

    def is_admin(self, user_id: int) -> bool:
        """Check whether Telegram user has admin access."""
        return user_id in self.admin_id_values

    @property
    def admin_id_values(self) -> tuple[int, ...]:
        """Return parsed admin Telegram IDs."""
        if not self.admin_ids.strip():
            return ()
        return tuple(int(item.strip()) for item in self.admin_ids.split(",") if item)


class DatabaseSettings(BaseSettings):
    """Database settings used by migrations and session helpers."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(alias="DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    """Load application settings or raise a readable configuration error."""
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as error:
        details = "; ".join(_format_settings_error(item) for item in error.errors())
        raise SettingsError(f"Ошибка конфигурации: {details}") from error


@lru_cache
def get_database_url() -> str:
    """Load database URL without requiring Telegram bot settings."""
    try:
        return DatabaseSettings().database_url  # type: ignore[call-arg]
    except ValidationError as error:
        details = "; ".join(_format_settings_error(item) for item in error.errors())
        raise SettingsError(f"Ошибка конфигурации БД: {details}") from error


def _format_settings_error(error: Any) -> str:
    """Format Pydantic settings error in Russian."""
    location = error.get("loc", ())
    if not isinstance(location, (list, tuple)):
        location = ()
    field = ".".join(str(part) for part in location)
    if error.get("type") == "missing":
        return f"укажите {field} в файле .env"
    return str(error.get("msg", "проверьте настройки в файле .env"))
