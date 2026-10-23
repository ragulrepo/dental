import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def send_welcome_email(email: str, name: str) -> None:
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email credentials are not configured.")
        return

    template = jinja_env.get_template("welcome.html")
    html_content = template.render(name=name)

    message = EmailMessage()
    message["Subject"] = "Welcome to Dental Booking!"
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email

    # Plain-text fallback
    message.set_content(
        f"Hi {name},\n\n"
        "Your Dental Booking account was created successfully.\n"
        "You can now log in and book appointments.\n\n"
        "Dental Booking Team"
    )

    # HTML email
    message.add_alternative(html_content, subtype="html")

    _send_email(message, email)


def send_appointment_email(
    email: str,
    name: str,
    appointment_id: int,
    starts_at: datetime,
    ends_at: datetime,
    dentist_name: str,
    treatment_name: str,
    confirmed: bool = False,
) -> None:
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email credentials are not configured.")
        return

    if confirmed:
        subject = "Your dental appointment is confirmed"
        status_message = "Your appointment has been confirmed by the dentist."
    else:
        subject = "We received your dental appointment request"
        status_message = (
            "Your appointment request has been received and is awaiting dentist confirmation."
        )

    starts_at_utc = starts_at.astimezone(timezone.utc)
    ends_at_utc = ends_at.astimezone(timezone.utc)
    appointment_date = starts_at_utc.strftime("%A, %B %d, %Y")
    appointment_time = (
        f"{starts_at_utc.strftime('%I:%M %p')} - "
        f"{ends_at_utc.strftime('%I:%M %p')} UTC"
    )
    template = jinja_env.get_template("appointment_confirmation.html")
    html_content = template.render(
        name=name,
        appointment_id=appointment_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        dentist_name=dentist_name,
        treatment_name=treatment_name,
        confirmed=confirmed,
        status_message=status_message,
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email
    message.set_content(
        f"Hi {name},\n\n"
        f"{status_message}\n\n"
        f"Appointment: #{appointment_id}\n"
        f"Treatment: {treatment_name}\n"
        f"Dentist: {dentist_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n\n"
        "Dental Booking Team"
    )
    message.add_alternative(html_content, subtype="html")
    _send_email(message, email)


def send_appointment_reminder_email(
    email: str,
    name: str,
    appointment_id: int,
    starts_at: datetime,
    ends_at: datetime,
    dentist_name: str,
    treatment_name: str,
) -> None:
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email credentials are not configured.")
        return

    subject = f"Reminder: Your dental appointment is in 2 hours (#{appointment_id})"
    status_message = (
        "This is a friendly reminder that your dental appointment is scheduled "
        "to start in 2 hours."
    )

    starts_at_utc = starts_at.astimezone(timezone.utc)
    ends_at_utc = ends_at.astimezone(timezone.utc)
    appointment_date = starts_at_utc.strftime("%A, %B %d, %Y")
    appointment_time = (
        f"{starts_at_utc.strftime('%I:%M %p')} - "
        f"{ends_at_utc.strftime('%I:%M %p')} UTC"
    )
    template = jinja_env.get_template("appointment_reminder.html")
    html_content = template.render(
        name=name,
        appointment_id=appointment_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        dentist_name=dentist_name,
        treatment_name=treatment_name,
        status_message=status_message,
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email
    message.set_content(
        f"Hi {name},\n\n"
        f"{status_message}\n\n"
        f"Appointment: #{appointment_id}\n"
        f"Treatment: {treatment_name}\n"
        f"Dentist: {dentist_name}\n"
        f"Date: {appointment_date}\n"
        f"Time: {appointment_time}\n\n"
        "Please plan to arrive 10-15 minutes prior to your scheduled time.\n\n"
        "Dental Booking Team"
    )
    message.add_alternative(html_content, subtype="html")
    _send_email(message, email)



def _send_email(message: EmailMessage, email: str) -> None:
    try:
        with smtplib.SMTP(
            settings.MAIL_SERVER,
            settings.MAIL_PORT,
            timeout=15,
        ) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(message)

        logger.info("Email sent to %s", email)
    except (smtplib.SMTPException, OSError):
        logger.exception("Failed to send email to %s", email)
