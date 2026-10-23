
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.database.db import SessionLocal
from app.models.appointments_model import Appointment, AppointmentStatus
from app.models.dentists_model import Dentist
from app.models.treatments_model import Treatment
from app.models.users import User
from app.services.email import send_appointment_reminder_email

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def send_appointment_reminder_job(appointment_id: int) -> None:
    logger.info("Executing appointment reminder job for appointment #%s", appointment_id)
    db = SessionLocal()

    try:
        appointment = db.scalar(
            select(Appointment).where(Appointment.id == appointment_id)
        )

        if appointment is None:
            logger.warning("Appointment #%s not found for reminder", appointment_id)
            return

        if appointment.status not in {
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        }:
            logger.warning(
                "Skipping reminder for appointment #%s because status is %s",
                appointment_id,
                appointment.status.value,
            )
            return

        dentist = db.get(Dentist, appointment.dentist_id)
        dentist_user = db.get(User, dentist.user_id) if dentist else None
        treatment = db.get(Treatment, appointment.treatment_id)

        send_appointment_reminder_email(
            email=appointment.patient.email,
            name=appointment.patient.name,
            appointment_id=appointment.id,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            dentist_name=dentist_user.name if dentist_user else "Your dentist",
            treatment_name=treatment.name if treatment else "Dental treatment",
        )

    except Exception:
        logger.exception(
            "Failed to send reminder for appointment #%s",
            appointment_id,
        )
    finally:
        db.close()


def schedule_appointment_reminder(
    appointment_id: int,
    starts_at: datetime,
) -> None:
    if starts_at.tzinfo is None:
        starts_at_utc = starts_at.replace(tzinfo=timezone.utc)
    else:
        starts_at_utc = starts_at.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)

    if starts_at_utc <= now:
        logger.warning(
            "Appointment #%s is already in the past (%s); skipping reminder.",
            appointment_id,
            starts_at_utc.isoformat(),
        )
        return

    reminder_time = starts_at_utc - timedelta(hours=2)
    run_date = max(reminder_time, now)

    job_id = f"appointment_reminder_{appointment_id}"

    scheduler.add_job(
        func=send_appointment_reminder_job,
        trigger="date",
        run_date=run_date,
        args=[appointment_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,
    )


def cancel_appointment_reminder(appointment_id: int) -> None:
    job_id = f"appointment_reminder_{appointment_id}"

    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass


def sync_pending_appointment_reminders() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        appointments = db.scalars(
            select(Appointment).where(
                Appointment.starts_at > now,
                Appointment.status.in_(
                    [
                        AppointmentStatus.PENDING,
                        AppointmentStatus.CONFIRMED,
                    ]
                ),
            )
        ).all()

        for appt in appointments:
            schedule_appointment_reminder(appt.id, appt.starts_at)

    except Exception:
        logger.exception("Failed to sync upcoming appointment reminders.")
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        sync_pending_appointment_reminders()


def shutdown_scheduler(wait: bool = False) -> None:
    if scheduler.running:
        scheduler.shutdown(wait=wait)
