"""Appointment reminder helpers and scheduler task."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manik_bot.config import Settings
from manik_bot.db import Appointment, Service, TimeSlot, get_session_factory

logger = logging.getLogger(__name__)

REMINDER_INTERVAL_MINUTES = 10
REMINDER_LOOKAHEAD = timedelta(hours=24)


def format_reminder_message(service: Service, slot: TimeSlot) -> str:
    """Format appointment reminder message for a client."""
    start = slot.start_at.strftime("%d.%m.%Y %H:%M")
    end = slot.end_at.strftime("%H:%M")
    return (
        "Напоминание о записи.\n\n"
        f"Услуга: {service.title}\n"
        f"Время: {start}-{end}\n\n"
        "Ждем вас!"
    )


def is_reminder_due(start_at: datetime, now: datetime) -> bool:
    """Check whether appointment should receive a reminder now."""
    if start_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=start_at.tzinfo)
    if start_at.tzinfo is None and now.tzinfo is not None:
        start_at = start_at.replace(tzinfo=now.tzinfo)
    return now < start_at <= now + REMINDER_LOOKAHEAD


async def send_due_reminders(bot: Bot, settings: Settings) -> None:
    """Send reminders for active appointments in the next 24 hours."""
    timezone = ZoneInfo(settings.timezone)
    now = datetime.now(timezone)

    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = await _load_due_appointments(session, now)
        for appointment, service, slot in rows:
            await _send_reminder(bot, session, appointment, service, slot)
        await session.commit()


async def _load_due_appointments(
    session: AsyncSession,
    now: datetime,
) -> list[tuple[Appointment, Service, TimeSlot]]:
    """Load appointments that need reminders."""
    result = await session.execute(
        select(Appointment, Service, TimeSlot)
        .join(Service, Appointment.service_id == Service.id)
        .join(TimeSlot, Appointment.time_slot_id == TimeSlot.id)
        .where(Appointment.status == "active")
        .where(Appointment.reminder_sent.is_(False))
        .where(TimeSlot.start_at > now)
        .where(TimeSlot.start_at <= now + REMINDER_LOOKAHEAD)
        .order_by(TimeSlot.start_at)
    )
    return [(appointment, service, slot) for appointment, service, slot in result.all()]


async def _send_reminder(
    bot: Bot,
    session: AsyncSession,
    appointment: Appointment,
    service: Service,
    slot: TimeSlot,
) -> None:
    """Send one reminder and mark it as sent after successful delivery."""
    try:
        await bot.send_message(
            appointment.client_telegram_id,
            format_reminder_message(service, slot),
        )
    except Exception:
        logger.exception(
            "Не удалось отправить напоминание по записи #%s",
            appointment.id,
        )
        return

    appointment.reminder_sent = True
    session.add(appointment)
    logger.info("Отправлено напоминание по записи #%s", appointment.id)
