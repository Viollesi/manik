"""Reply keyboards for Telegram menus."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_client_menu() -> ReplyKeyboardMarkup:
    """Build the main client menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Услуги"), KeyboardButton(text="Моя запись")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Build the main admin menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Услуги"), KeyboardButton(text="Расписание")],
            [KeyboardButton(text="Записи"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )
