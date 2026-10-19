"""add appointments and ratings

Revision ID: 3a7f91c2d6e4
Revises: 8bf2aea19d17
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3a7f91c2d6e4"
down_revision: Union[str, Sequence[str], None] = "8bf2aea19d17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


appointment_status = postgresql.ENUM(
    "pending",
    "confirmed",
    "rejected",
    "cancelled",
    "completed",
    name="appointment_status",
    create_type=False,
)


def upgrade() -> None:
    appointment_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("dentist_id", sa.Integer(), nullable=False),
        sa.Column("treatment_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.CheckConstraint(
            "ends_at > starts_at", name="ck_appointments_valid_time_range"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dentist_id"], ["dentists.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["treatment_id"], ["treatments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_appointments_id"), "appointments", ["id"], unique=False)
    op.create_index(
        "ix_appointments_dentist_time",
        "appointments",
        ["dentist_id", "starts_at", "ends_at"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_patient_id", "appointments", ["patient_id"], unique=False
    )

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint("score >= 1 AND score <= 5", name="ck_ratings_score_range"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id", name="uq_ratings_appointment_id"),
    )
    op.create_index(op.f("ix_ratings_id"), "ratings", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ratings_id"), table_name="ratings")
    op.drop_table("ratings")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_dentist_time", table_name="appointments")
    op.drop_index(op.f("ix_appointments_id"), table_name="appointments")
    op.drop_table("appointments")
    appointment_status.drop(op.get_bind(), checkfirst=True)
