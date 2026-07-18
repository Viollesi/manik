"""Base Telegram handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from manik_bot.bot.keyboards import get_admin_menu, get_client_menu
from manik_bot.config import get_settings

router = Router()


def _is_admin(message: Message) -> bool:
    """Return true when the message author is an admin."""
    if message.from_user is None:
        return False
    return get_settings().is_admin(message.from_user.id)


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Show the main menu for clients or admins."""
    if _is_admin(message):
        await message.answer(
            "Здравствуйте! Открываю меню мастера.",
            reply_markup=get_admin_menu(),
        )
        return

    await message.answer(
        "Здравствуйте! Здесь можно будет записаться на маникюр.",
        reply_markup=get_client_menu(),
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Show a short help message."""
    if _is_admin(message):
        await message.answer(
            "Вы в меню мастера. Доступны услуги, расписание и активные записи.",
            reply_markup=get_admin_menu(),
        )
        return

    await message.answer(
        "Вы в клиентском меню. Можно посмотреть услуги, записаться, отменить "
        "или перенести активную запись.",
        reply_markup=get_client_menu(),
    )


@router.message()
async def handle_unknown_message(message: Message) -> None:
    """Reply to menu buttons that are not implemented yet."""
    text = message.text or ""
    if text == "Помощь":
        await handle_help(message)
        return

    if text in {"Расписание", "Записи"} and not _is_admin(message):
        await message.answer(
            "Этот раздел доступен только мастеру.",
            reply_markup=get_client_menu(),
        )
        return

    if text in {"Услуги", "Моя запись", "Расписание", "Записи"}:
        await message.answer(
            "Откройте раздел через меню.",
            reply_markup=get_admin_menu() if _is_admin(message) else get_client_menu(),
        )
        return

    await message.answer(
        "Я пока не понимаю это сообщение. Используйте меню или команду /help.",
        reply_markup=get_admin_menu() if _is_admin(message) else get_client_menu(),
    )
