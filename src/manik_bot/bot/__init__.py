"""Telegram bot handlers and dispatching package."""


from manik_bot.bot.handlers import router

__all__ = ["router"]

from manik_bot.bot.admin import router as admin_router
from manik_bot.bot.handlers import router

__all__ = ["admin_router", "router"]
