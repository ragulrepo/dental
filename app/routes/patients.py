from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enum import UserRole
from app.database.db import get_db
from app.dependencies.roles import require_roles
from app.models.dentists_model import Dentist
from app.models.users import User
from app.schemas.auth_schema import UserResponse, UserUpdate

router = APIRouter( tags=["Patients"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(
        require_roles(UserRole.PATIENT)
    ),
):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.PATIENT)
    ),
):
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )

    for field, value in updates.items():
        if value is None and field != "phone":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )

    if "email" in updates:
        updates["email"] = str(updates["email"])
        existing_user = db.scalar(
            select(User).where(
                User.email == updates["email"],
                User.id != current_user.id,
            )
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

    for field, value in updates.items():
        setattr(current_user, field, value)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update profile. Email may already be registered.",
        ) from exc

    return current_user









@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_delete.is_(False),
        )
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_delete = True
    if user.role == UserRole.DENTIST.value:
        dentist = db.scalar(
            select(Dentist).where(Dentist.user_id == user.id)
        )
        if dentist is not None:
            dentist.is_delete = True
            dentist.is_active = False

    db.commit()
    return {"message": "User deleted successfully"}

