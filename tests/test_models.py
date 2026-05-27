"""Database model tests."""

from sqlalchemy import Table

from manik_bot.db import Appointment, Base


def test_metadata_has_booking_tables() -> None:
    """Check that booking tables are registered in metadata."""
    assert {"services", "time_slots", "appointments"} <= set(Base.metadata.tables)


def test_appointment_defaults() -> None:
    """Check appointment column defaults."""
    status_default = Appointment.__table__.c.status.default
    reminder_default = Appointment.__table__.c.reminder_sent.default

    assert status_default is not None
    assert reminder_default is not None
    assert status_default.arg == "active"
    assert reminder_default.arg is False


def test_appointment_slot_unique_index_only_applies_to_active_records() -> None:
    """Check that cancelled slot history does not block rebooking."""
    table = Appointment.__table__
    assert isinstance(table, Table)

    time_slot_column = table.c.time_slot_id
    index_names = {index.name for index in table.indexes}

    assert not time_slot_column.unique
    assert "ix_appointments_active_time_slot_id" in index_names
