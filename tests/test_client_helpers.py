"""Client booking helper tests."""

from datetime import datetime

import pytest

from manik_bot.bot.client import (
    format_active_appointment,
    format_booking_confirmation,
    format_client_service,
    format_client_slot,
    parse_positive_int,
)
from manik_bot.db import Appointment, Service, TimeSlot


def test_parse_positive_int() -> None:
    """Check positive integer parsing."""
    assert parse_positive_int("7", "Ошибка") == 7


def test_parse_positive_int_rejects_invalid_value() -> None:
    """Check invalid integer parsing."""
    with pytest.raises(ValueError, match="Id услуги"):
        parse_positive_int("no", "Id услуги должен быть целым числом.")


def test_format_client_service() -> None:
    """Check service formatting for clients."""
    service = Service(
        id=1,
        title="Маникюр",
        description="Классический",
        price=1500,
        duration_minutes=90,
    )

    text = format_client_service(service)

    assert "#1: Маникюр" in text
    assert "1500 руб." in text


def test_format_client_slot() -> None:
    """Check slot formatting for clients."""
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
    )

    assert format_client_slot(slot) == "#2: 27.05.2026 15:00-16:30"


def test_format_booking_confirmation() -> None:
    """Check booking confirmation formatting."""
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

    text = format_booking_confirmation(service, slot)

    assert "Проверьте запись" in text
    assert "Маникюр" in text
    assert "27.05.2026 15:00-16:30" in text


def test_format_active_appointment() -> None:
    """Check active appointment formatting."""
    appointment = Appointment(id=5, client_telegram_id=123, client_name="Анна")
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

    text = format_active_appointment(appointment, service, slot)

    assert "Ваша активная запись" in text
    assert "Номер записи: #5" in text
