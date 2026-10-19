import jwt
from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.users import User
from app.schemas.auth_schema import AccessTokenResponse
from app.schemas.auth_schema import SignupRequest, UserResponse,TokenResponse,LoginRequest
from app.core.jwt import create_access_token,create_refresh_token
from app.core.pshashing import verify_password
from app.core.pshashing import hash_password
from app.core.config import settings
from app.core.enum import UserRole
from app.services.email import send_welcome_email

router = APIRouter( tags=["Auth"])


@router.post("/signup",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest,background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.email == str(data.email)))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )
    hashed_password = hash_password(data.password)
    new_user = User(
        name=data.name,
        age=data.age,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        email=str(data.email),
        phone=data.phone,
        password_hash=hashed_password,
        role=UserRole.PATIENT.value,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        background_tasks.add_task(
        send_welcome_email,
        new_user.email,
        new_user.name,
    )

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc
    return new_user
@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.email == str(data.email),
            User.is_delete.is_(False),
        )
    )

    
    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

  
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    refresh_token = create_refresh_token(
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
 
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc


    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )


    user_id = payload.get("sub")

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )


    user = db.scalar(
        select(User).where(
            User.id == int(user_id),
            User.is_delete.is_(False),
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

  
    new_access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return AccessTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
    )
