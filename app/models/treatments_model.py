
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class Treatment(Base):
    __tablename__ = "treatments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
