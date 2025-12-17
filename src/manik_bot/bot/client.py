"""Client booking handlers."""

from datetime import datetime
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select


from manik_bot.bot.keyboards import get_booking_confirm_menu, get_client_menu

from manik_bot.bot.keyboards import (
    get_appointment_actions_menu,
    get_booking_confirm_menu,
    get_cancel_appointment_menu,
    get_client_menu,
    get_reschedule_confirm_menu,
)

from manik_bot.config import get_settings
from manik_bot.db import Appointment, Service, TimeSlot, get_session

router = Router()


class Booking(StatesGroup):
    """FSM states for client booking."""

    service_id = State()
    slot_id = State()
    confirm = State()




class CancelAppointment(StatesGroup):
    """FSM states for client appointment cancellation."""

    confirm = State()


class RescheduleAppointment(StatesGroup):
    """FSM states for client appointment rescheduling."""

    slot_id = State()
    confirm = State()



def parse_positive_int(value: str, error_message: str) -> int:
    """Parse a positive integer from client input."""
    try:
        result = int(value.strip())
    except ValueError as error:
        raise ValueError(error_message) from error
    if result <= 0:
        raise ValueError(error_message)
    return result


def format_client_service(service: Service) -> str:
    """Format service for client list."""
    return (
        f"#{service.id}: {service.title}\n"
        f"{service.description}\n"
        f"Цена: {service.price} руб.\n"
        f"Длительность: {service.duration_minutes} мин."
    )


def format_client_slot(slot: TimeSlot) -> str:
    """Format available time slot for client list."""
    start = slot.start_at.strftime("%d.%m.%Y %H:%M")
    end = slot.end_at.strftime("%H:%M")
    return f"#{slot.id}: {start}-{end}"


def format_booking_confirmation(service: Service, slot: TimeSlot) -> str:
    """Format booking confirmation text."""
    return (
        "Проверьте запись:\n\n"
        f"Услуга: {service.title}\n"
        f"Цена: {service.price} руб.\n"
        f"Время: {format_client_slot(slot).split(': ', maxsplit=1)[1]}"
    )




def format_active_appointment(
    appointment: Appointment,
    service: Service,
    slot: TimeSlot,
) -> str:
    """Format active appointment details for client."""
    return (
        "Ваша активная запись:\n\n"
        f"Услуга: {service.title}\n"
        f"Цена: {service.price} руб.\n"
        f"Время: {format_client_slot(slot).split(': ', maxsplit=1)[1]}\n"
        f"Номер записи: #{appointment.id}"
    )



def _client_name(message: Message) -> str:
    """Return readable client name from Telegram message."""
    if message.from_user is None:
        return "Клиент"
    return message.from_user.full_name


def _client_username(message: Message) -> str | None:
    """Return Telegram username from message."""
    if message.from_user is None:
        return None
    return message.from_user.username


async def _get_active_appointment(
    client_telegram_id: int,
) -> tuple[Appointment, Service, TimeSlot] | None:
    """Return active appointment with service and slot for client."""
    async for session in get_session():
        appointment = await session.scalar(
            select(Appointment).where(
                Appointment.client_telegram_id == client_telegram_id,
                Appointment.status == "active",
            ),
        )
        if appointment is None:
            return None

        service = await session.get(Service, appointment.service_id)
        slot = await session.get(TimeSlot, appointment.time_slot_id)
        if service is None or slot is None:
            return None

        return appointment, service, slot
    return None


@router.message(F.text == "Услуги")
async def start_booking(message: Message, state: FSMContext) -> None:
    """Show active services and ask client to choose one."""
    await state.clear()
    async for session in get_session():
        services = list(
            (
                await session.scalars(
                    select(Service)
                    .where(Service.is_active.is_(True))
                    .order_by(Service.id),
                )
            ).all(),
        )

    if not services:
        await message.answer(
            "Пока нет доступных услуг.",
            reply_markup=get_client_menu(),
        )
        return

    await state.set_state(Booking.service_id)
    await message.answer(
        "Выберите услугу и отправьте ее id:\n\n"
        + "\n\n".join(format_client_service(service) for service in services),
    )


@router.message(Booking.service_id)
async def choose_service(message: Message, state: FSMContext) -> None:
    """Save selected service and show available slots."""
    try:
        service_id = parse_positive_int(
            message.text or "",
            "Id услуги должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        service = await session.get(Service, service_id)
        if service is None or not service.is_active:
            await message.answer("Услуга с таким id не найдена.")
            return

        slots = list(
            (
                await session.scalars(
                    select(TimeSlot)
                    .where(TimeSlot.is_available.is_(True))
                    .order_by(TimeSlot.start_at),
                )
            ).all(),
        )

    if not slots:
        await state.clear()
        await message.answer(
            "Пока нет свободного времени для записи.",
            reply_markup=get_client_menu(),
        )
        return

    await state.update_data(service_id=service_id)
    await state.set_state(Booking.slot_id)
    await message.answer(
        "Выберите свободное время и отправьте id слота:\n\n"
        + "\n".join(format_client_slot(slot) for slot in slots),
    )


@router.message(Booking.slot_id)
async def choose_slot(message: Message, state: FSMContext) -> None:
    """Save selected slot and ask for confirmation."""
    try:
        slot_id = parse_positive_int(
            message.text or "",
            "Id слота должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    data = await state.get_data()
    service_id = int(data["service_id"])

    async for session in get_session():
        service = await session.get(Service, service_id)
        slot = await session.get(TimeSlot, slot_id)

    if service is None or not service.is_active:
        await state.clear()
        await message.answer(
            "Услуга с таким id не найдена.",
            reply_markup=get_client_menu(),
        )
        return
    if slot is None or not slot.is_available:
        await message.answer("Свободный слот с таким id не найден.")
        return

    await state.update_data(slot_id=slot_id)
    await state.set_state(Booking.confirm)
    await message.answer(
        format_booking_confirmation(service, slot),
        reply_markup=get_booking_confirm_menu(),
    )


@router.message(Booking.confirm, F.text == "Отменить запись")
async def cancel_booking(message: Message, state: FSMContext) -> None:
    """Cancel booking flow."""
    await state.clear()
    await message.answer("Запись отменена.", reply_markup=get_client_menu())


@router.message(Booking.confirm)
async def confirm_booking(message: Message, state: FSMContext) -> None:
    """Create appointment after client confirmation."""
    if message.text != "Подтвердить запись":
        await message.answer("Нажмите «Подтвердить запись» или «Отменить запись».")
        return
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    data: dict[str, Any] = await state.get_data()
    service_id = int(data["service_id"])
    slot_id = int(data["slot_id"])

    async for session in get_session():
        active_appointment = await session.scalar(
            select(Appointment).where(
                Appointment.client_telegram_id == message.from_user.id,
                Appointment.status == "active",
            ),
        )
        if active_appointment is not None:
            await state.clear()
            await message.answer(
                "У вас уже есть активная запись.",
                reply_markup=get_client_menu(),
            )
            return

        service = await session.get(Service, service_id)
        slot = await session.get(TimeSlot, slot_id)
        if service is None or not service.is_active:
            await state.clear()
            await message.answer(
                "Услуга с таким id не найдена.",
                reply_markup=get_client_menu(),
            )
            return
        if slot is None or not slot.is_available:
            await message.answer("Свободный слот с таким id не найден.")
            return

        service_title = service.title
        slot_start = slot.start_at

        appointment = Appointment(
            client_telegram_id=message.from_user.id,
            client_name=_client_name(message),
            client_username=_client_username(message),
            service_id=service.id,
            time_slot_id=slot.id,
        )
        slot.is_available = False
        session.add(appointment)
        await session.commit()

    await state.clear()
    await message.answer(
        "Вы записаны. Мастер получил уведомление.",
        reply_markup=get_client_menu(),
    )
    await _notify_admins(
        message,
        service_title=service_title,
        slot_start=slot_start,
        client_name=_client_name(message),
    )


async def _notify_admins(
    message: Message,
    service_title: str,
    slot_start: datetime,
    client_name: str,
) -> None:
    """Notify admins about new appointment."""
    text = (
        "Новая запись!\n\n"
        f"Клиент: {client_name}\n"
        f"Услуга: {service_title}\n"
        f"Время: {slot_start.strftime('%d.%m.%Y %H:%M')}"
    )
    if message.bot is None:
        return
    for admin_id in get_settings().admin_id_values:
        await message.bot.send_message(admin_id, text)



@router.message(F.text == "Назад")
async def handle_client_back(message: Message, state: FSMContext) -> None:
    """Return client to the main menu."""
    await state.clear()
    await message.answer("Главное меню.", reply_markup=get_client_menu())


@router.message(F.text == "Моя запись")
async def show_my_appointment(message: Message, state: FSMContext) -> None:
    """Show current active appointment."""
    await state.clear()
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    result = await _get_active_appointment(message.from_user.id)
    if result is None:
        await message.answer(
            "У вас нет активной записи.",
            reply_markup=get_client_menu(),
        )
        return

    appointment, service, slot = result
    await message.answer(
        format_active_appointment(appointment, service, slot),
        reply_markup=get_appointment_actions_menu(),
    )


@router.message(F.text == "Отменить мою запись")
async def start_cancel_appointment(message: Message, state: FSMContext) -> None:
    """Ask client to confirm appointment cancellation."""
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    result = await _get_active_appointment(message.from_user.id)
    if result is None:
        await message.answer(
            "У вас нет активной записи.",
            reply_markup=get_client_menu(),
        )
        return

    await state.set_state(CancelAppointment.confirm)
    await message.answer(
        "Вы уверены, что хотите отменить запись?",
        reply_markup=get_cancel_appointment_menu(),
    )


@router.message(CancelAppointment.confirm)
async def confirm_cancel_appointment(message: Message, state: FSMContext) -> None:
    """Cancel active appointment after confirmation."""
    if message.text != "Да, отменить запись":
        await message.answer("Нажмите «Да, отменить запись» или «Назад».")
        return
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    async for session in get_session():
        appointment = await session.scalar(
            select(Appointment).where(
                Appointment.client_telegram_id == message.from_user.id,
                Appointment.status == "active",
            ),
        )
        if appointment is None:
            await state.clear()
            await message.answer(
                "У вас нет активной записи.",
                reply_markup=get_client_menu(),
            )
            return

        service = await session.get(Service, appointment.service_id)
        slot = await session.get(TimeSlot, appointment.time_slot_id)
        appointment.status = "cancelled"
        if slot is not None:
            slot.is_available = True
            slot_start = slot.start_at
        else:
            slot_start = None
        service_title = service.title if service is not None else "услуга не найдена"
        await session.commit()

    await state.clear()
    await message.answer("Запись отменена.", reply_markup=get_client_menu())
    slot_time = slot_start.strftime("%d.%m.%Y %H:%M") if slot_start else "не найдено"
    await _notify_admins_text(
        message,
        "Клиент отменил запись.\n\n"
        f"Клиент: {_client_name(message)}\n"
        f"Услуга: {service_title}\n"
        f"Время: {slot_time}",
    )


@router.message(F.text == "Перенести запись")
async def start_reschedule_appointment(message: Message, state: FSMContext) -> None:
    """Show free slots and ask client to choose a new one."""
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    result = await _get_active_appointment(message.from_user.id)
    if result is None:
        await message.answer(
            "У вас нет активной записи.",
            reply_markup=get_client_menu(),
        )
        return

    async for session in get_session():
        slots = list(
            (
                await session.scalars(
                    select(TimeSlot)
                    .where(TimeSlot.is_available.is_(True))
                    .order_by(TimeSlot.start_at),
                )
            ).all(),
        )

    if not slots:
        await message.answer(
            "Пока нет свободного времени для переноса.",
            reply_markup=get_appointment_actions_menu(),
        )
        return

    await state.set_state(RescheduleAppointment.slot_id)
    await message.answer(
        "Выберите новое время и отправьте id слота:\n\n"
        + "\n".join(format_client_slot(slot) for slot in slots),
    )


@router.message(RescheduleAppointment.slot_id)
async def choose_reschedule_slot(message: Message, state: FSMContext) -> None:
    """Save new slot for appointment reschedule."""
    try:
        slot_id = parse_positive_int(
            message.text or "",
            "Id слота должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        slot = await session.get(TimeSlot, slot_id)
        if slot is None or not slot.is_available:
            await message.answer("Свободный слот с таким id не найден.")
            return
        slot_text = format_client_slot(slot).split(": ", maxsplit=1)[1]

    await state.update_data(slot_id=slot_id)
    await state.set_state(RescheduleAppointment.confirm)
    await message.answer(
        f"Перенести запись на {slot_text}?",
        reply_markup=get_reschedule_confirm_menu(),
    )


@router.message(RescheduleAppointment.confirm)
async def confirm_reschedule_appointment(message: Message, state: FSMContext) -> None:
    """Move active appointment to a new free slot."""
    if message.text != "Подтвердить перенос":
        await message.answer("Нажмите «Подтвердить перенос» или «Назад».")
        return
    if message.from_user is None:
        await message.answer("Не удалось определить клиента.")
        return

    data = await state.get_data()
    new_slot_id = int(data["slot_id"])

    async for session in get_session():
        appointment = await session.scalar(
            select(Appointment).where(
                Appointment.client_telegram_id == message.from_user.id,
                Appointment.status == "active",
            ),
        )
        if appointment is None:
            await state.clear()
            await message.answer(
                "У вас нет активной записи.",
                reply_markup=get_client_menu(),
            )
            return

        old_slot = await session.get(TimeSlot, appointment.time_slot_id)
        new_slot = await session.get(TimeSlot, new_slot_id)
        service = await session.get(Service, appointment.service_id)
        if new_slot is None or not new_slot.is_available:
            await message.answer("Свободный слот с таким id не найден.")
            return

        if old_slot is not None:
            old_slot.is_available = True
        new_slot.is_available = False
        appointment.time_slot_id = new_slot.id
        service_title = service.title if service is not None else "услуга не найдена"
        new_slot_start = new_slot.start_at
        await session.commit()

    await state.clear()
    await message.answer("Запись перенесена.", reply_markup=get_client_menu())
    await _notify_admins_text(
        message,
        "Клиент перенес запись.\n\n"
        f"Клиент: {_client_name(message)}\n"
        f"Услуга: {service_title}\n"
        f"Новое время: {new_slot_start.strftime('%d.%m.%Y %H:%M')}",
    )


async def _notify_admins_text(message: Message, text: str) -> None:
    """Send text notification to all admins."""
    if message.bot is None:
        return
    for admin_id in get_settings().admin_id_values:
        await message.bot.send_message(admin_id, text)
