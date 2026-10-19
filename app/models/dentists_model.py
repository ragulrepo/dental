
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class Dentist(Base):
    __tablename__ = "dentists"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    address: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True,
    )

    specialization: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    qualification: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    experience_years: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    is_delete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
