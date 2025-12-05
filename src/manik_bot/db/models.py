"""Database models for services, time slots and appointments."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from manik_bot.db.base import Base


class Service(Base):
    """Manicure service offered to clients."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="service")


class TimeSlot(Base):
    """Available appointment time slot."""

    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    appointment: Mapped["Appointment | None"] = relationship(back_populates="time_slot")


class Appointment(Base):
    """Client appointment for a service and time slot."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    client_name: Mapped[str] = mapped_column(String(120), nullable=False)
    client_username: Mapped[str | None] = mapped_column(String(120))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    time_slot_id: Mapped[int] = mapped_column(
        ForeignKey("time_slots.id"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    service: Mapped[Service] = relationship(back_populates="appointments")
    time_slot: Mapped[TimeSlot] = relationship(back_populates="appointment")
