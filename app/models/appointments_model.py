from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base
from app.models.users import User


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_appointments_valid_time_range"),
        Index("ix_appointments_dentist_time", "dentist_id", "starts_at", "ends_at"),
        Index("ix_appointments_patient_id", "patient_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    patient: Mapped[User] = relationship(lazy="joined")
    dentist_id: Mapped[int] = mapped_column(
        ForeignKey("dentists.id", ondelete="RESTRICT"), nullable=False
    )
    treatment_id: Mapped[int] = mapped_column(
        ForeignKey("treatments.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(
            AppointmentStatus,
            name="appointment_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=AppointmentStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
