from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enum import UserRole
from app.database.db import get_db
from app.dependencies.auth_dep import get_current_user
from app.dependencies.roles import require_roles
from app.models.appointments_model import Appointment, AppointmentStatus
from app.models.dentists_model import Dentist
from app.models.treatments_model import Treatment
from app.models.users import User
from app.schemas.appointment_schema import AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate
from app.services.email import send_appointment_email

router = APIRouter(tags=["appointments"])


def _get_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .with_for_update(of=Appointment)
    )
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


def _dentist_for_user(db: Session, user_id: int) -> Dentist:
    dentist = db.scalar(select(Dentist).where(Dentist.user_id == user_id))
    if dentist is None:
        raise HTTPException(status_code=404, detail="Dentist profile not found")
    return dentist


@router.post("/appointments/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.PATIENT.value:
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    if data.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Appointment must be in the future")

    dentist = db.scalar(
        select(Dentist)
        .where(Dentist.id == data.dentist_id)
        .with_for_update()
    )
    if dentist is None or not dentist.is_active:
        raise HTTPException(status_code=404, detail="Active dentist not found")
    treatment = db.get(Treatment, data.treatment_id)
    if treatment is None or not treatment.is_active:
        raise HTTPException(status_code=404, detail="Active treatment not found")

    starts_at = data.starts_at.astimezone(timezone.utc)
    appointment = Appointment(
        patient_id=current_user.id,
        dentist_id=dentist.id,
        treatment_id=treatment.id,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=treatment.duration_minutes),
        status=AppointmentStatus.PENDING,
        notes=data.notes,
    )
    conflicting_appointment = db.scalar(
        select(Appointment.id).where(
            Appointment.dentist_id == dentist.id,
            Appointment.status.in_(
                [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
            ),
            Appointment.starts_at < appointment.ends_at,
            Appointment.ends_at > appointment.starts_at,
        )
    )
    if conflicting_appointment is not None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dentist is already booked for this time slot",
        )

    # Keep the authenticated patient's profile up to date with the details
    # provided during booking; patient_id remains derived from the access token.
    current_user.name = data.name
    current_user.age = data.age
    current_user.phone = data.phone
    current_user.date_of_birth = data.date_of_birth
    current_user.gender = data.gender

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    dentist_user = db.get(User, dentist.user_id)
    send_appointment_email(
        email=current_user.email,
        name=current_user.name,
        appointment_id=appointment.id,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        dentist_name=dentist_user.name if dentist_user else "Your dentist",
        treatment_name=treatment.name,
    )
    return appointment


@router.get("/appointments/my", response_model=list[AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.PATIENT.value:
        raise HTTPException(status_code=403, detail="Only patients can view this list")
    return db.scalars(
        select(Appointment)
        .where(Appointment.patient_id == current_user.id)
        .order_by(Appointment.starts_at.desc())
    ).all()


@router.get("/appointments/dentist/my", response_model=list[AppointmentResponse])
def get_dentist_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.DENTIST.value:
        raise HTTPException(status_code=403, detail="Only dentists can view this list")
    dentist = _dentist_for_user(db, current_user.id)
    return db.scalars(
        select(Appointment)
        .where(Appointment.dentist_id == dentist.id)
        .order_by(Appointment.starts_at)
    ).all()


@router.get("/appointments/{id}", response_model=AppointmentResponse)
def get_appointment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.get(Appointment, id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    authorized = current_user.role == UserRole.ADMIN.value
    if current_user.role == UserRole.PATIENT.value:
        authorized = appointment.patient_id == current_user.id
    elif current_user.role == UserRole.DENTIST.value:
        dentist = _dentist_for_user(db, current_user.id)
        authorized = appointment.dentist_id == dentist.id
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to access this appointment")
    return appointment


@router.patch("/appointments/{id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.PATIENT.value:
        raise HTTPException(status_code=403, detail="Only patients can cancel appointments")
    appointment = _get_appointment(db, id)
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
    if appointment.status not in {AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED}:
        raise HTTPException(status_code=409, detail="Appointment cannot be cancelled in its current status")
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/appointments/{id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_appointment_status(
        id=id,
        data=AppointmentStatusUpdate(status=AppointmentStatus.CONFIRMED),
        db=db,
        current_user=current_user,
    )


@router.patch("/appointments/{id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    id: int,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.DENTIST.value:
        raise HTTPException(status_code=403, detail="Only dentists can update appointment status")
    dentist = _dentist_for_user(db, current_user.id)
    appointment = _get_appointment(db, id)
    if appointment.dentist_id != dentist.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    allowed_transitions = {
        AppointmentStatus.PENDING: {AppointmentStatus.CONFIRMED, AppointmentStatus.REJECTED},
        AppointmentStatus.CONFIRMED: {AppointmentStatus.COMPLETED},
    }
    if data.status not in allowed_transitions.get(appointment.status, set()):
        raise HTTPException(status_code=409, detail="Invalid appointment status transition")

    appointment.status = data.status
    db.commit()
    db.refresh(appointment)
    if data.status == AppointmentStatus.CONFIRMED:
        dentist_user = db.get(User, dentist.user_id)
        treatment = db.get(Treatment, appointment.treatment_id)
        send_appointment_email(
            email=appointment.patient.email,
            name=appointment.patient.name,
            appointment_id=appointment.id,
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            dentist_name=dentist_user.name if dentist_user else "Your dentist",
            treatment_name=treatment.name if treatment else "Dental treatment",
            confirmed=True,
        )
    return appointment


@router.get("/admin/appointments", response_model=list[AppointmentResponse])
def get_all_appointments(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.scalars(select(Appointment).order_by(Appointment.starts_at.desc())).all()
