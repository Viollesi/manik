"""Reminder helper tests."""

from datetime import datetime, timedelta

from manik_bot.bot.reminders import format_reminder_message, is_reminder_due
from manik_bot.db import Service, TimeSlot


def test_format_reminder_message() -> None:
    """Check reminder message formatting."""
    service = Service(id=1, title="Маникюр", price=1500, duration_minutes=90)
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    text = format_reminder_message(service, slot)

    assert "Напоминание о записи" in text
    assert "Маникюр" in text
    assert "27.05.2026 15:00-16:30" in text


def test_is_reminder_due_for_next_day_appointment() -> None:
    """Check that appointment in the next 24 hours needs a reminder."""
    now = datetime(2026, 5, 26, 15, 0)
    start_at = now + timedelta(hours=23, minutes=50)

    assert is_reminder_due(start_at, now) is True


def test_is_reminder_due_rejects_late_appointment() -> None:
    """Check that distant appointments are skipped."""
    now = datetime(2026, 5, 26, 15, 0)
    start_at = now + timedelta(days=2)

    assert is_reminder_due(start_at, now) is False


def test_is_reminder_due_rejects_past_appointment() -> None:
    """Check that past appointments are skipped."""
    now = datetime(2026, 5, 26, 15, 0)
    start_at = now - timedelta(minutes=1)

    assert is_reminder_due(start_at, now) is False
