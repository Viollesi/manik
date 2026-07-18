"""Reply keyboards for Telegram menus."""

from collections.abc import Iterable

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
            [
                KeyboardButton(text="Изменить услугу"),
                KeyboardButton(text="Отключить услугу"),
            ],
            [KeyboardButton(text="Включить услугу"), KeyboardButton(text="Назад")],
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
            [KeyboardButton(text="Все слоты")],
            [KeyboardButton(text="Закрыть слот"), KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )



def get_admin_appointments_menu() -> ReplyKeyboardMarkup:
    """Build the admin appointments menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Активные записи")],
            [KeyboardButton(text="Отменить запись")],
            [KeyboardButton(text="Перенести запись")],
            [KeyboardButton(text="Назад")],
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


def get_appointment_actions_menu() -> ReplyKeyboardMarkup:
    """Build active appointment actions menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перенести запись")],
            [KeyboardButton(text="Отменить мою запись")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_cancel_appointment_menu() -> ReplyKeyboardMarkup:
    """Build appointment cancellation confirmation menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, отменить запись")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_reschedule_confirm_menu() -> ReplyKeyboardMarkup:
    """Build appointment reschedule confirmation menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить перенос")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_edit_service_menu() -> ReplyKeyboardMarkup:
    """Build service edit field menu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Название"), KeyboardButton(text="Описание")],
            [KeyboardButton(text="Цена"), KeyboardButton(text="Длительность")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_id_choice_menu(ids: Iterable[int]) -> ReplyKeyboardMarkup:
    """Build a keyboard with numeric choices."""
    buttons = [KeyboardButton(text=str(item_id)) for item_id in ids]
    rows = [buttons[index : index + 3] for index in range(0, len(buttons), 3)]
    rows.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
