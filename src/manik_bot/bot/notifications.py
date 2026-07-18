"""Safe Telegram notification helpers."""

import logging
from collections.abc import Iterable

from aiogram import Bot

logger = logging.getLogger(__name__)


async def send_message_safely(bot: Bot, chat_id: int, text: str) -> bool:
    """Send a Telegram message and log delivery errors."""
    try:
        await bot.send_message(chat_id, text)
    except Exception:
        logger.exception("Не удалось отправить сообщение в чат %s", chat_id)
        return False
    return True


async def send_messages_safely(bot: Bot, chat_ids: Iterable[int], text: str) -> None:
    """Send the same Telegram message to several chats."""
    for chat_id in chat_ids:
        await send_message_safely(bot, chat_id, text)
