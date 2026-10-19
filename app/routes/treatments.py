
from argon2 import hash_password
from fastapi import APIRouter, Depends, HTTPException
from psycopg import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.dependencies.roles import require_roles
from app.core.enum import UserRole
from app.models.treatments_model import Treatment
from app.schemas.treatment_schema import TreatmentUpdate
from app.schemas.treatment_schema import TreatmentUpdate


router = APIRouter( tags=["treatments"])

@router.post("/treatments/create", status_code=201)
def create_treatment(
    data: TreatmentUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    existing_treatment = db.scalar(
        select(Treatment).where(Treatment.name == str(data.name))
    )

    if existing_treatment:
        raise HTTPException(
            status_code=409,
            detail="Treatment with this name already exists",
        )

    treatment = Treatment(
        name=data.name,
        description=data.description,
        duration_minutes=data.duration_minutes,
        fee=data.fee,
    )

    db.add(treatment)
    db.commit()
    db.refresh(treatment)

    return {"message": "Treatment created successfully", "treatment_id": treatment.id}

@router.get("/treatments", status_code=200)
def get_treatments(
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    treatments = db.scalars(select(Treatment)).all()
    return treatments


@router.get("/treatments/{treatment_id}", status_code=200)
def get_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    treatment = db.scalar(
        select(Treatment).where(Treatment.id == treatment_id)
    )

    if treatment is None:
        raise HTTPException(404, "Treatment not found")

    return treatment
# UPDATE TREATMENT
@router.patch("/treatments/{treatment_id}")
def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    treatment = db.scalar(
        select(Treatment).where(Treatment.id == treatment_id)
    )

    if treatment is None:
        raise HTTPException(404, "Treatment not found")

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(400, "Provide at least one field to update")

    for field, value in updates.items():
        setattr(treatment, field, value)

    db.commit()
    db.refresh(treatment)

    return {"message": "Treatment updated successfully"}


# DEACTIVATE TREATMENT
@router.delete("/treatments/{treatment_id}")
def delete_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    treatment = db.scalar(
        select(Treatment).where(Treatment.id == treatment_id)
    )

    if treatment is None:
        raise HTTPException(404, "Treatment not found")

    if not treatment.is_active:
        raise HTTPException(400, "Treatment is already deactivated")

    treatment.is_active = False
    db.commit()

    return {"message": "Treatment deactivated successfully"}
