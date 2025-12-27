"""Telegram bot application factory and runner."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from manik_bot.bot import admin_router, client_router, router
from manik_bot.bot.reminders import REMINDER_INTERVAL_MINUTES, send_due_reminders
from manik_bot.config import Settings

logger = logging.getLogger(__name__)


async def run_bot(settings: Settings) -> None:
    """Start Telegram polling."""
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    dispatcher.include_router(admin_router)
    dispatcher.include_router(client_router)
    dispatcher.include_router(router)

    scheduler.add_job(
        send_due_reminders,
        "interval",
        minutes=REMINDER_INTERVAL_MINUTES,
        args=[bot, settings],
    )
    scheduler.start()
    logger.info("Планировщик напоминаний запущен")

    logger.info("Бот запускается")
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик напоминаний остановлен")


def run(settings: Settings) -> None:
    """Run bot in an asyncio event loop."""
    asyncio.run(run_bot(settings))
