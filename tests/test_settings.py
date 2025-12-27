"""Settings tests."""

import pytest

from manik_bot.config.settings import Settings


def test_settings_parses_admin_ids() -> None:
    """Check that admin IDs are parsed from an environment-like value."""
    settings = Settings(
        BOT_TOKEN="123456:test-token",
        ADMIN_IDS="1,2,3",
        DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/app",
        TIMEZONE="Europe/Moscow",
    )

    assert settings.admin_id_values == (1, 2, 3)
    assert settings.is_admin(2)
    assert not settings.is_admin(4)


def test_settings_rejects_placeholder_token() -> None:
    """Check that placeholder token is not accepted."""
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        Settings(
            BOT_TOKEN="replace_me",
            ADMIN_IDS="1",
            DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/app",
            TIMEZONE="Europe/Moscow",
        )
