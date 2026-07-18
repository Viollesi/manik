"""Admin helper tests."""

from datetime import datetime

import pytest

from manik_bot.bot.admin import (
    ensure_future_datetime,
    format_admin_appointment,
    format_client_cancel_notice,
    format_client_info,
    format_client_reschedule_notice,
    format_service,
    format_slot,
    format_slot_details,
    parse_admin_datetime,
    parse_edit_service_field,
    parse_limited_positive_int,
    parse_positive_int,
    parse_service_title,
    slots_overlap,
)
from manik_bot.db import Appointment, Service, TimeSlot


def test_parse_positive_int() -> None:
    """Check positive integer parsing."""
    assert parse_positive_int("15", "Ошибка") == 15


def test_parse_positive_int_rejects_invalid_value() -> None:
    """Check that invalid integers are rejected."""
    with pytest.raises(ValueError, match="Цена должна быть целым числом."):
        parse_positive_int("abc", "Цена должна быть целым числом.")


def test_parse_limited_positive_int_rejects_too_large_value() -> None:
    """Check that excessive integers are rejected."""
    with pytest.raises(ValueError, match="Цена"):
        parse_limited_positive_int("100001", "Цена слишком большая.", 100000)


def test_parse_service_title_rejects_blank_title() -> None:
    """Check that service title cannot be blank."""
    with pytest.raises(ValueError, match="Название"):
        parse_service_title("   ")


def test_parse_service_title_strips_value() -> None:
    """Check service title normalization."""
    assert parse_service_title("  Маникюр  ") == "Маникюр"


def test_parse_edit_service_field_returns_model_field() -> None:
    """Check service edit field parsing."""
    assert parse_edit_service_field("Цена") == "price"


def test_parse_edit_service_field_rejects_unknown_value() -> None:
    """Check service edit field validation."""
    with pytest.raises(ValueError, match="Выберите"):
        parse_edit_service_field("Цвет")


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


def test_ensure_future_datetime_rejects_past_value() -> None:
    """Check that slots cannot start in the past."""
    now = datetime(2026, 5, 27, 15, 0)

    with pytest.raises(ValueError, match="будущем"):
        ensure_future_datetime(datetime(2026, 5, 27, 14, 59), now)


def test_slots_overlap_detects_intersection() -> None:
    """Check slot overlap detection."""
    assert slots_overlap(
        datetime(2026, 5, 27, 15, 0),
        datetime(2026, 5, 27, 16, 0),
        datetime(2026, 5, 27, 15, 30),
        datetime(2026, 5, 27, 16, 30),
    )


def test_slots_overlap_allows_adjacent_ranges() -> None:
    """Check that adjacent slots do not overlap."""
    assert not slots_overlap(
        datetime(2026, 5, 27, 15, 0),
        datetime(2026, 5, 27, 16, 0),
        datetime(2026, 5, 27, 16, 0),
        datetime(2026, 5, 27, 17, 0),
    )


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


def test_format_slot_details() -> None:
    """Check time slot formatting with status."""
    slot = TimeSlot(
        id=2,
        start_at=datetime(2026, 5, 27, 15, 0),
        end_at=datetime(2026, 5, 27, 16, 30),
        is_available=False,
    )

    assert format_slot_details(slot) == "#2: 27.05.2026 15:00-16:30 (закрыт или занят)"



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
