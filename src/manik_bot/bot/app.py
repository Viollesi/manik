"""Telegram bot application factory and runner."""

import asyncio
import logging

from aiogram import Bot, Dispatcher

from manik_bot.bot import admin_router, router
from manik_bot.config import Settings

logger = logging.getLogger(__name__)


async def run_bot(settings: Settings) -> None:
    """Start Telegram polling."""
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(admin_router)
    dispatcher.include_router(router)

    logger.info("Бот запускается")
    await dispatcher.start_polling(bot)


def run(settings: Settings) -> None:
    """Run bot in an asyncio event loop."""
    asyncio.run(run_bot(settings))
