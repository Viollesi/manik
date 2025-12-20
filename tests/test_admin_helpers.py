"""Admin helper tests."""

from datetime import datetime

import pytest

from manik_bot.bot.admin import (
    format_admin_appointment,
    format_client_cancel_notice,
    format_client_info,
    format_client_reschedule_notice,
    format_service,
    format_slot,
    parse_admin_datetime,
    parse_positive_int,
)
from manik_bot.db import Appointment, Service, TimeSlot


def test_parse_positive_int() -> None:
    """Check positive integer parsing."""
    assert parse_positive_int("15", "Ошибка") == 15


def test_parse_positive_int_rejects_invalid_value() -> None:
    """Check that invalid integers are rejected."""
    with pytest.raises(ValueError, match="Цена должна быть целым числом."):
        parse_positive_int("abc", "Цена должна быть целым числом.")


def test_parse_admin_datetime() -> None:
    """Check admin datetime parsing."""
    parsed = parse_admin_datetime("27.05.2026 15:30", "Europe/Moscow")

    assert parsed.day == 27
    assert parsed.hour == 15
    assert parsed.tzinfo is not None


def test_parse_admin_datetime_rejects_invalid_format() -> None:
    """Check invalid admin datetime format."""
    with pytest.raises(ValueError, match="Дата должна быть"):
        parse_admin_datetime("2026-05-27", "Europe/Moscow")


def test_format_service() -> None:
    """Check service formatting."""
    service = Service(
        id=1,
        title="Маникюр",
        description="Классический",
        price=1500,
        duration_minutes=90,
        is_active=True,
    )

    assert "Маникюр" in format_service(service)
    assert "1500 руб." in format_service(service)


def test_format_slot() -> None:
    """Check time slot formatting."""
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    assert format_slot(slot) == "#2: 27.05.2026 15:00-16:30"


def test_format_client_info() -> None:
    """Check client info formatting."""
    appointment = Appointment(
        client_name="Анна",
        client_username="anna",
        client_telegram_id=123,
    )

    assert format_client_info(appointment) == "Анна (@anna)"


def test_format_admin_appointment() -> None:
    """Check appointment formatting for admin."""
    appointment = Appointment(
        id=3,
        client_name="Анна",
        client_username=None,
        client_telegram_id=123,
    )
    service = Service(
        id=1,
        title="Маникюр",
        description="Классический",
        price=1500,
        duration_minutes=90,
    )
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    text = format_admin_appointment(appointment, service, slot)

    assert "#3" in text
    assert "Маникюр" in text
    assert "27.05.2026 15:00-16:30" in text


def test_format_client_cancel_notice() -> None:
    """Check cancellation notice formatting."""
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    text = format_client_cancel_notice("Маникюр", slot)

    assert "Мастер отменил" in text
    assert "Маникюр" in text


def test_format_client_reschedule_notice() -> None:
    """Check reschedule notice formatting."""
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    text = format_client_reschedule_notice("Маникюр", slot)

    assert "Мастер перенес" in text
    assert "27.05.2026 15:00-16:30" in text
