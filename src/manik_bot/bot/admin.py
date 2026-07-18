"""Admin handlers for services and schedule management."""

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from manik_bot.bot.keyboards import (
    get_admin_appointments_menu,
    get_admin_menu,
    get_admin_schedule_menu,
    get_admin_services_menu,
    get_client_menu,
    get_edit_service_menu,
    get_id_choice_menu,
)
from manik_bot.bot.notifications import send_message_safely
from manik_bot.config import get_settings
from manik_bot.db import Appointment, Service, TimeSlot, get_session

router = Router()


class AdminFilter(BaseFilter):
    """Allow only admin users to pass into admin handlers."""

    async def __call__(self, message: Message) -> bool:
        """Check admin access for message author."""
        return _is_admin(message)


router.message.filter(AdminFilter())

MAX_SERVICE_PRICE = 100_000
MAX_DURATION_MINUTES = 12 * 60


class AddService(StatesGroup):
    """FSM states for adding a service."""

    title = State()
    description = State()
    price = State()
    duration = State()


class DisableService(StatesGroup):
    """FSM state for disabling a service."""

    service_id = State()


class EnableService(StatesGroup):
    """FSM state for enabling a service."""

    service_id = State()


class EditService(StatesGroup):
    """FSM states for editing a service."""

    service_id = State()
    field = State()
    value = State()


class AddSlot(StatesGroup):
    """FSM states for adding a time slot."""

    start_at = State()
    duration = State()


class CloseSlot(StatesGroup):
    """FSM state for closing a time slot."""

    slot_id = State()



class CancelClientAppointment(StatesGroup):
    """FSM state for admin appointment cancellation."""

    appointment_id = State()


class RescheduleClientAppointment(StatesGroup):
    """FSM states for admin appointment rescheduling."""

    appointment_id = State()
    slot_id = State()



def parse_positive_int(value: str, error_message: str) -> int:
    """Parse a positive integer from admin input."""
    try:
        result = int(value.strip())
    except ValueError as error:
        raise ValueError(error_message) from error
    if result <= 0:
        raise ValueError(error_message)
    return result


def parse_limited_positive_int(
    value: str,
    error_message: str,
    max_value: int,
) -> int:
    """Parse a positive integer not greater than max value."""
    result = parse_positive_int(value, error_message)
    if result > max_value:
        raise ValueError(error_message)
    return result


def parse_service_title(value: str) -> str:
    """Parse non-empty service title."""
    title = value.strip()
    if not title:
        raise ValueError("Название услуги не должно быть пустым.")
    if len(title) > 120:
        raise ValueError("Название услуги должно быть не длиннее 120 символов.")
    return title


def parse_edit_service_field(value: str) -> str:
    """Parse service field selected for editing."""
    fields = {
        "Название": "title",
        "Описание": "description",
        "Цена": "price",
        "Длительность": "duration_minutes",
    }
    try:
        return fields[value.strip()]
    except KeyError as error:
        raise ValueError("Выберите поле из меню.") from error


def _parse_service_edit_value(field: str, value: str) -> str | int:
    if field == "title":
        return parse_service_title(value)
    if field == "description":
        return value.strip()
    if field == "price":
        return parse_limited_positive_int(
            value,
            "Цена должна быть целым числом от 1 до 100000.",
            MAX_SERVICE_PRICE,
        )
    if field == "duration_minutes":
        return parse_limited_positive_int(
            value,
            "Длительность должна быть целым числом от 1 до 720.",
            MAX_DURATION_MINUTES,
        )
    raise ValueError("Выберите поле из меню.")


def parse_admin_datetime(value: str, timezone: str) -> datetime:
    """Parse admin date input in Russian-friendly format."""
    try:
        parsed = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")
    except ValueError as error:
        raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ ЧЧ:ММ.") from error
    return parsed.replace(tzinfo=ZoneInfo(timezone))


def ensure_future_datetime(value: datetime, now: datetime) -> None:
    """Check that datetime is in the future."""
    if value.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=value.tzinfo)
    if value.tzinfo is None and now.tzinfo is not None:
        value = value.replace(tzinfo=now.tzinfo)
    if value <= now:
        raise ValueError("Дата и время должны быть в будущем.")


def slots_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    """Check whether two time ranges overlap."""
    return first_start < second_end and first_end > second_start


def format_service(service: Service) -> str:
    """Format service for admin list."""
    status = "активна" if service.is_active else "отключена"
    return (
        f"#{service.id}: {service.title}\n"
        f"Цена: {service.price} руб.\n"
        f"Длительность: {service.duration_minutes} мин.\n"
        f"Статус: {status}"
    )


def format_slot(slot: TimeSlot) -> str:
    """Format time slot for admin list."""
    start = slot.start_at.strftime("%d.%m.%Y %H:%M")
    end = slot.end_at.strftime("%H:%M")
    return f"#{slot.id}: {start}-{end}"


def format_slot_details(slot: TimeSlot) -> str:
    """Format time slot with availability status."""
    status = "свободен" if slot.is_available else "закрыт или занят"
    return f"{format_slot(slot)} ({status})"


def format_client_info(appointment: Appointment) -> str:
    """Format appointment client info for admin messages."""
    username = (
        f"@{appointment.client_username}"
        if appointment.client_username
        else "без username"
    )
    return f"{appointment.client_name} ({username})"


def format_admin_appointment(
    appointment: Appointment,
    service: Service,
    slot: TimeSlot,
) -> str:
    """Format active appointment for admin list."""
    return (
        f"#{appointment.id}: {format_client_info(appointment)}\n"
        f"Услуга: {service.title}\n"
        f"Время: {format_slot(slot).split(': ', maxsplit=1)[1]}"
    )


def format_client_cancel_notice(service_title: str, slot: TimeSlot) -> str:
    """Format cancellation notice for client."""
    return (
        "Мастер отменил вашу запись.\n\n"
        f"Услуга: {service_title}\n"
        f"Время: {format_slot(slot).split(': ', maxsplit=1)[1]}"
    )


def format_client_reschedule_notice(service_title: str, slot: TimeSlot) -> str:
    """Format reschedule notice for client."""
    return (
        "Мастер перенес вашу запись.\n\n"
        f"Услуга: {service_title}\n"
        f"Новое время: {format_slot(slot).split(': ', maxsplit=1)[1]}"
    )



def _is_admin(message: Message) -> bool:
    """Check whether message author is an admin."""
    return (
        message.from_user is not None
        and get_settings().is_admin(message.from_user.id)
    )


async def _deny_non_admin(message: Message) -> bool:
    """Return true and answer when user has no admin access."""
    if _is_admin(message):
        return False
    await message.answer(
        "Этот раздел доступен только мастеру.",
        reply_markup=get_client_menu(),
    )
    return True


@router.message(F.text == "Назад")
async def handle_admin_back(message: Message, state: FSMContext) -> None:
    """Return admin to the main menu."""
    if await _deny_non_admin(message):
        return
    await state.clear()
    await message.answer("Главное меню мастера.", reply_markup=get_admin_menu())


@router.message(F.text == "Услуги")
async def handle_services_menu(message: Message) -> None:
    """Show admin services menu."""
    await message.answer("Управление услугами.", reply_markup=get_admin_services_menu())


@router.message(F.text == "Расписание")
async def handle_schedule_menu(message: Message) -> None:
    """Show admin schedule menu."""
    if await _deny_non_admin(message):
        return
    await message.answer(
        "Управление расписанием.",
        reply_markup=get_admin_schedule_menu(),
    )



@router.message(F.text == "Записи")
async def handle_appointments_menu(message: Message) -> None:
    """Show admin appointments menu."""
    await message.answer(
        "Управление записями.",
        reply_markup=get_admin_appointments_menu(),
    )


@router.message(F.text == "Добавить услугу")
async def start_add_service(message: Message, state: FSMContext) -> None:
    """Start service creation."""
    if await _deny_non_admin(message):
        return
    await state.set_state(AddService.title)
    await message.answer("Введите название услуги.")


@router.message(AddService.title)
async def add_service_title(message: Message, state: FSMContext) -> None:
    """Save service title."""
    try:
        title = parse_service_title(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(title=title)
    await state.set_state(AddService.description)
    await message.answer("Введите описание услуги.")


@router.message(AddService.description)
async def add_service_description(message: Message, state: FSMContext) -> None:
    """Save service description."""
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AddService.price)
    await message.answer("Введите цену услуги в рублях.")


@router.message(AddService.price)
async def add_service_price(message: Message, state: FSMContext) -> None:
    """Save service price."""
    try:
        price = parse_limited_positive_int(
            message.text or "",
            "Цена должна быть целым числом от 1 до 100000.",
            MAX_SERVICE_PRICE,
        )
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(price=price)
    await state.set_state(AddService.duration)
    await message.answer("Введите длительность услуги в минутах.")


@router.message(AddService.duration)
async def add_service_duration(message: Message, state: FSMContext) -> None:
    """Create service after collecting all fields."""
    try:
        duration = parse_limited_positive_int(
            message.text or "",
            "Длительность должна быть целым числом от 1 до 720.",
            MAX_DURATION_MINUTES,
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    data = await state.get_data()
    service = Service(
        title=str(data["title"]),
        description=str(data["description"]),
        price=int(data["price"]),
        duration_minutes=duration,
    )
    async for session in get_session():
        session.add(service)
        await session.commit()

    await state.clear()
    await message.answer(
        "Услуга добавлена.",
        reply_markup=get_admin_services_menu(),
    )


@router.message(F.text == "Список услуг")
async def list_services(message: Message) -> None:
    """Show all services."""
    if await _deny_non_admin(message):
        return
    async for session in get_session():
        services = list(
            (await session.scalars(select(Service).order_by(Service.id))).all(),
        )

    if not services:
        await message.answer(
            "Услуги пока не добавлены.",
            reply_markup=get_admin_services_menu(),
        )
        return

    await message.answer(
        "\n\n".join(format_service(service) for service in services),
        reply_markup=get_admin_services_menu(),
    )


@router.message(F.text == "Отключить услугу")
async def start_disable_service(message: Message, state: FSMContext) -> None:
    """Start service disabling."""
    if await _deny_non_admin(message):
        return
    await state.set_state(DisableService.service_id)
    await message.answer("Введите id услуги, которую нужно отключить.")


@router.message(DisableService.service_id)
async def disable_service(message: Message, state: FSMContext) -> None:
    """Disable service by id."""
    try:
        service_id = parse_positive_int(
            message.text or "",
            "Id должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        service = await session.get(Service, service_id)
        if service is None:
            await message.answer("Услуга с таким id не найдена.")
            return
        service.is_active = False
        await session.commit()

    await state.clear()
    await message.answer("Услуга отключена.", reply_markup=get_admin_services_menu())


@router.message(F.text == "Включить услугу")
async def start_enable_service(message: Message, state: FSMContext) -> None:
    """Start service enabling."""
    if await _deny_non_admin(message):
        return
    await state.set_state(EnableService.service_id)
    await message.answer("Введите id услуги, которую нужно включить.")


@router.message(EnableService.service_id)
async def enable_service(message: Message, state: FSMContext) -> None:
    """Enable service by id."""
    try:
        service_id = parse_positive_int(
            message.text or "",
            "Id должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        service = await session.get(Service, service_id)
        if service is None:
            await message.answer("Услуга с таким id не найдена.")
            return
        service.is_active = True
        await session.commit()

    await state.clear()
    await message.answer("Услуга включена.", reply_markup=get_admin_services_menu())


@router.message(F.text == "Изменить услугу")
async def start_edit_service(message: Message, state: FSMContext) -> None:
    """Start service editing."""
    if await _deny_non_admin(message):
        return
    await state.set_state(EditService.service_id)
    await message.answer("Введите id услуги, которую нужно изменить.")


@router.message(EditService.service_id)
async def choose_service_for_edit(message: Message, state: FSMContext) -> None:
    """Save service id for editing."""
    try:
        service_id = parse_positive_int(
            message.text or "",
            "Id должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        service = await session.get(Service, service_id)
        if service is None:
            await message.answer("Услуга с таким id не найдена.")
            return

    await state.update_data(service_id=service_id)
    await state.set_state(EditService.field)
    await message.answer("Что изменить?", reply_markup=get_edit_service_menu())


@router.message(EditService.field)
async def choose_service_field(message: Message, state: FSMContext) -> None:
    """Save service field selected for editing."""
    try:
        field = parse_edit_service_field(message.text or "")
    except ValueError as error:
        await message.answer(str(error), reply_markup=get_edit_service_menu())
        return

    await state.update_data(field=field)
    await state.set_state(EditService.value)
    await message.answer("Введите новое значение.")


@router.message(EditService.value)
async def update_service_field(message: Message, state: FSMContext) -> None:
    """Apply service field change."""
    data = await state.get_data()
    field = str(data["field"])
    try:
        value = _parse_service_edit_value(field, message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        service = await session.get(Service, int(data["service_id"]))
        if service is None:
            await message.answer("Услуга с таким id не найдена.")
            return
        setattr(service, field, value)
        await session.commit()

    await state.clear()
    await message.answer("Услуга изменена.", reply_markup=get_admin_services_menu())


@router.message(F.text == "Добавить слот")
async def start_add_slot(message: Message, state: FSMContext) -> None:
    """Start time slot creation."""
    if await _deny_non_admin(message):
        return
    await state.set_state(AddSlot.start_at)
    await message.answer("Введите дату и время начала: ДД.ММ.ГГГГ ЧЧ:ММ.")


@router.message(AddSlot.start_at)
async def add_slot_start(message: Message, state: FSMContext) -> None:
    """Save slot start datetime."""
    try:
        timezone = get_settings().timezone
        start_at = parse_admin_datetime(message.text or "", timezone)
        ensure_future_datetime(start_at, datetime.now(ZoneInfo(timezone)))
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(start_at=start_at)
    await state.set_state(AddSlot.duration)
    await message.answer("Введите длительность слота в минутах.")


@router.message(AddSlot.duration)
async def add_slot_duration(message: Message, state: FSMContext) -> None:
    """Create time slot after collecting all fields."""
    try:
        duration = parse_limited_positive_int(
            message.text or "",
            "Длительность должна быть целым числом от 1 до 720.",
            MAX_DURATION_MINUTES,
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    data: dict[str, Any] = await state.get_data()
    start_at = data["start_at"]
    if not isinstance(start_at, datetime):
        await message.answer("Дата должна быть в формате ДД.ММ.ГГГГ ЧЧ:ММ.")
        return

    end_at = start_at + timedelta(minutes=duration)
    async for session in get_session():
        overlapping_slot = await session.scalar(
            select(TimeSlot).where(
                TimeSlot.start_at < end_at,
                TimeSlot.end_at > start_at,
            ),
        )
        if overlapping_slot is not None:
            await message.answer("Этот слот пересекается с уже добавленным временем.")
            return

        slot = TimeSlot(start_at=start_at, end_at=end_at)
        session.add(slot)
        await session.commit()

    await state.clear()
    await message.answer(
        "Свободный слот добавлен.",
        reply_markup=get_admin_schedule_menu(),
    )


@router.message(F.text == "Свободные слоты")
async def list_free_slots(message: Message) -> None:
    """Show available time slots."""
    if await _deny_non_admin(message):
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
            "Свободные слоты пока не добавлены.",
            reply_markup=get_admin_schedule_menu(),
        )
        return

    await message.answer(
        "\n".join(format_slot(slot) for slot in slots),
        reply_markup=get_admin_schedule_menu(),
    )


@router.message(F.text == "Все слоты")
async def list_all_slots(message: Message) -> None:
    """Show all time slots."""
    if await _deny_non_admin(message):
        return
    async for session in get_session():
        slots = list(
            (
                await session.scalars(
                    select(TimeSlot).order_by(TimeSlot.start_at),
                )
            ).all(),
        )

    if not slots:
        await message.answer(
            "Слоты пока не добавлены.",
            reply_markup=get_admin_schedule_menu(),
        )
        return

    await message.answer(
        "\n".join(format_slot_details(slot) for slot in slots),
        reply_markup=get_admin_schedule_menu(),
    )


@router.message(F.text == "Закрыть слот")
async def start_close_slot(message: Message, state: FSMContext) -> None:
    """Start slot closing."""
    if await _deny_non_admin(message):
        return
    await state.set_state(CloseSlot.slot_id)
    await message.answer("Введите id свободного слота, который нужно закрыть.")


@router.message(CloseSlot.slot_id)
async def close_slot(message: Message, state: FSMContext) -> None:
    """Close available time slot by id."""
    try:
        slot_id = parse_positive_int(message.text or "", "Id должен быть целым числом.")
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        slot = await session.get(TimeSlot, slot_id)
        if slot is None or not slot.is_available:
            await message.answer("Свободный слот с таким id не найден.")
            return

        appointment = await session.scalar(
            select(Appointment).where(
                Appointment.time_slot_id == slot_id,
                Appointment.status == "active",
            ),
        )
        if appointment is not None:
            await message.answer("Нельзя закрыть слот, на который уже есть запись.")
            return

        slot.is_available = False
        await session.commit()

    await state.clear()
    await message.answer("Слот закрыт.", reply_markup=get_admin_schedule_menu())


@router.message(F.text == "Активные записи")
async def list_active_appointments(message: Message) -> None:
    """Show active appointments."""
    async for session in get_session():
        appointments = list(
            (
                await session.scalars(
                    select(Appointment)
                    .where(Appointment.status == "active")
                    .order_by(Appointment.id),
                )
            ).all(),
        )
        lines: list[str] = []
        for appointment in appointments:
            service = await session.get(Service, appointment.service_id)
            slot = await session.get(TimeSlot, appointment.time_slot_id)
            if service is not None and slot is not None:
                lines.append(format_admin_appointment(appointment, service, slot))

    if not lines:
        await message.answer(
            "Активных записей пока нет.",
            reply_markup=get_admin_appointments_menu(),
        )
        return

    await message.answer(
        "\n\n".join(lines),
        reply_markup=get_admin_appointments_menu(),
    )


@router.message(F.text == "Отменить запись")
async def start_cancel_client_appointment(message: Message, state: FSMContext) -> None:
    """Start client appointment cancellation by admin."""
    await state.set_state(CancelClientAppointment.appointment_id)
    await message.answer("Введите id записи, которую нужно отменить.")


@router.message(CancelClientAppointment.appointment_id)
async def cancel_client_appointment(message: Message, state: FSMContext) -> None:
    """Cancel client appointment by id."""
    try:
        appointment_id = parse_positive_int(
            message.text or "",
            "Id записи должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        if appointment is None or appointment.status != "active":
            await message.answer("Активная запись с таким id не найдена.")
            return

        service = await session.get(Service, appointment.service_id)
        slot = await session.get(TimeSlot, appointment.time_slot_id)
        if service is None or slot is None:
            await message.answer("Не удалось найти услугу или слот для записи.")
            return

        appointment.status = "cancelled"
        slot.is_available = True
        client_telegram_id = appointment.client_telegram_id
        notice = format_client_cancel_notice(service.title, slot)
        await session.commit()

    await state.clear()
    await message.answer("Запись отменена.", reply_markup=get_admin_appointments_menu())
    await _send_client_notice(message, client_telegram_id, notice)


@router.message(F.text == "Перенести запись")
async def start_reschedule_client_appointment(
    message: Message,
    state: FSMContext,
) -> None:
    """Start client appointment rescheduling by admin."""
    await state.set_state(RescheduleClientAppointment.appointment_id)
    await message.answer("Введите id записи, которую нужно перенести.")


@router.message(RescheduleClientAppointment.appointment_id)
async def choose_appointment_for_reschedule(
    message: Message,
    state: FSMContext,
) -> None:
    """Save appointment id and show free slots."""
    try:
        appointment_id = parse_positive_int(
            message.text or "",
            "Id записи должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        if appointment is None or appointment.status != "active":
            await message.answer("Активная запись с таким id не найдена.")
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
            "Свободных слотов для переноса нет.",
            reply_markup=get_admin_appointments_menu(),
        )
        return

    await state.update_data(appointment_id=appointment_id)
    await state.set_state(RescheduleClientAppointment.slot_id)
    await message.answer(
        "Выберите новый слот и отправьте его id:\n\n"
        + "\n".join(format_slot(slot) for slot in slots),
        reply_markup=get_id_choice_menu(slot.id for slot in slots),
    )


@router.message(RescheduleClientAppointment.slot_id)
async def reschedule_client_appointment(message: Message, state: FSMContext) -> None:
    """Move client appointment to another free slot."""
    try:
        slot_id = parse_positive_int(
            message.text or "",
            "Id слота должен быть целым числом.",
        )
    except ValueError as error:
        await message.answer(str(error))
        return

    data = await state.get_data()
    appointment_id = int(data["appointment_id"])

    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        new_slot = await session.get(TimeSlot, slot_id)
        if appointment is None or appointment.status != "active":
            await message.answer("Активная запись с таким id не найдена.")
            return
        if new_slot is None or not new_slot.is_available:
            await message.answer("Свободный слот с таким id не найден.")
            return

        old_slot = await session.get(TimeSlot, appointment.time_slot_id)
        service = await session.get(Service, appointment.service_id)
        if service is None:
            await message.answer("Не удалось найти услугу для записи.")
            return

        if old_slot is not None:
            old_slot.is_available = True
        new_slot.is_available = False
        appointment.time_slot_id = new_slot.id
        client_telegram_id = appointment.client_telegram_id
        notice = format_client_reschedule_notice(service.title, new_slot)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await state.clear()
            await message.answer(
                "Этот слот уже заняли. Выберите другое время.",
                reply_markup=get_admin_appointments_menu(),
            )
            return

    await state.clear()
    await message.answer(
        "Запись перенесена.",
        reply_markup=get_admin_appointments_menu(),
    )
    await _send_client_notice(message, client_telegram_id, notice)


async def _send_client_notice(
    message: Message,
    client_telegram_id: int,
    text: str,
) -> None:
    """Send appointment notice to client."""
    if message.bot is None:
        return
    await send_message_safely(message.bot, client_telegram_id, text)
