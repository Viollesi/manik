"""Notification helper tests."""

from typing import Any

import pytest

from manik_bot.bot.notifications import send_message_safely, send_messages_safely


class FakeBot:
    """Telegram bot test double."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **_: Any) -> None:
        """Record or reject outgoing message."""
        if self.should_fail:
            raise RuntimeError("send failed")
        self.messages.append((chat_id, text))


@pytest.mark.asyncio
async def test_send_message_safely_returns_true_after_success() -> None:
    """Check successful Telegram message delivery."""
    bot = FakeBot()

    result = await send_message_safely(bot, 123, "Привет")  # type: ignore[arg-type]

    assert result is True
    assert bot.messages == [(123, "Привет")]


@pytest.mark.asyncio
async def test_send_message_safely_returns_false_after_error() -> None:
    """Check that delivery error is handled."""
    bot = FakeBot(should_fail=True)

    result = await send_message_safely(bot, 123, "Привет")  # type: ignore[arg-type]

    assert result is False
    assert bot.messages == []


@pytest.mark.asyncio
async def test_send_messages_safely_sends_to_all_chats() -> None:
    """Check bulk Telegram message delivery."""
    bot = FakeBot()

    await send_messages_safely(bot, [1, 2], "Текст")  # type: ignore[arg-type]

    assert bot.messages == [(1, "Текст"), (2, "Текст")]
