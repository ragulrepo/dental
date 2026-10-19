
from argon2 import hash_password
from fastapi import APIRouter, Depends, HTTPException
from psycopg import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.dependencies.roles import require_roles
from app.core.enum import UserRole
from app.models.dentists_model import Dentist
from app.models.treatments_model import Treatment
from app.schemas.dentist_schema import DentistCreate, DentistUpdate
from app.schemas.treatment_schema import TreatmentUpdate
from app.models.users import User
from app.schemas.dentist_schema import DentistResponse

router = APIRouter( tags=["dentists"])

@router.post("/dentists/create", status_code=201)
def create_dentist(
    data: DentistCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    existing_user = db.scalar(
        select(User).where(User.email == str(data.email))
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    try:
        # Create the dentist's login account.
        user = User(
            name=data.name,
            age=data.age,
            gender=data.gender,
            email=str(data.email),
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.DENTIST.value,
        )

        db.add(user)
        db.flush()  # Generates user.id without committing yet.

        # Create the dentist's professional profile.
        dentist = Dentist(
            user_id=user.id,
            qualification=data.qualification,
            specialization=data.specialization,
            experience_years=data.experience_years,
            bio=data.bio,
            address=data.address,
        )

        db.add(dentist)
        db.commit()
        db.refresh(user)
        db.refresh(dentist)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create dentist. Check for duplicate details.",
        ) from exc

    return {
        "message": "Dentist created successfully",
        "dentist": {
            "id": dentist.id,
            "user_id": user.id,
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "email": user.email,
            "phone": user.phone,
            "qualification": dentist.qualification,
            "specialization": dentist.specialization,
            "experience_years": dentist.experience_years,
            "address": dentist.address,
            "is_active": dentist.is_active,
        },
    }
@router.get("/dentists", response_model=list[DentistResponse])
def get_all_dentists(
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    results = db.execute(
        select(Dentist, User)
        .join(User, Dentist.user_id == User.id)
        .where(
            Dentist.is_delete.is_(False),
            User.is_delete.is_(False),
        )
        .order_by(Dentist.id)
    ).all()

    return [
        {
            "id": dentist.id,
            "age": user.age,
            "gender": user.gender,
            "address": dentist.address,
            "user_id": dentist.user_id,
            "specialization": dentist.specialization,
            "qualification": dentist.qualification,
            "experience_years": dentist.experience_years,
            "bio": dentist.bio,
            "is_active": dentist.is_active,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
        }
        for dentist, user in results
    ]


@router.get("/dentists/{dentist_id}", response_model=DentistResponse)
def get_dentist_by_id(
    dentist_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    result = db.execute(
        select(Dentist, User)
        .join(User, Dentist.user_id == User.id)
        .where(
            Dentist.id == dentist_id,
            Dentist.is_delete.is_(False),
            User.is_delete.is_(False),
        )
    ).first()

    if not result:
        raise HTTPException(404, "Dentist not found")

    dentist, user = result

    return {
        "id": dentist.id,
        "age": user.age,
        "gender": user.gender,
        "address": dentist.address,
        "user_id": dentist.user_id,
        "specialization": dentist.specialization,
        "qualification": dentist.qualification,
        "experience_years": dentist.experience_years,
        "bio": dentist.bio,
        "is_active": dentist.is_active,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
    }

# UPDATE DENTIST
@router.patch("/dentists/{dentist_id}")
def update_dentist(
    dentist_id: int,
    data: DentistUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    dentist = db.scalar(
        select(Dentist).where(
            Dentist.id == dentist_id,
            Dentist.is_delete.is_(False),
        )
    )

    if dentist is None:
        raise HTTPException(404, "Dentist not found")

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(400, "Provide at least one field to update")

    for field, value in updates.items():
        setattr(dentist, field, value)

    db.commit()
    db.refresh(dentist)

    return {"message": "Dentist updated successfully"}


# SOFT DELETE DENTIST
@router.delete("/dentists/{dentist_id}")
def delete_dentist(
    dentist_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(UserRole.ADMIN)),
):
    dentist = db.scalar(
        select(Dentist).where(
            Dentist.id == dentist_id,
            Dentist.is_delete.is_(False),
        )
    )

    if dentist is None:
        raise HTTPException(404, "Dentist not found")

    dentist.is_delete = True
    dentist.is_active = False
    user = db.get(User, dentist.user_id)
    if user is not None:
        user.is_delete = True
    db.commit()

    return {"message": "Dentist deleted successfully"}

