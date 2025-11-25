"""Command-line startup for the bot."""

import logging
import sys

from manik_bot.bot.app import run
from manik_bot.config import SettingsError, get_settings
from manik_bot.utils import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """Start the Telegram bot."""
    setup_logging()
    try:
        settings = get_settings()
    except SettingsError as error:
        logger.error("%s", error)
        print(error, file=sys.stderr)
        return 1

    run(settings)
    return 0
