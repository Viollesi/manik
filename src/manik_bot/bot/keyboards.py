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



def get_admin_services_menu() -> ReplyKeyboardMarkup:
    """Build the admin services menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить услугу"),
                KeyboardButton(text="Список услуг"),
            ],
            [KeyboardButton(text="Отключить услугу"), KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_admin_schedule_menu() -> ReplyKeyboardMarkup:
    """Build the admin schedule menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить слот"),
                KeyboardButton(text="Свободные слоты"),
            ],
            [KeyboardButton(text="Закрыть слот"), KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_booking_confirm_menu() -> ReplyKeyboardMarkup:
    """Build booking confirmation menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить запись")],
            [KeyboardButton(text="Отменить запись")],
        ],
        resize_keyboard=True,
    )
