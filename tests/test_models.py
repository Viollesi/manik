"""Database model tests."""

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
