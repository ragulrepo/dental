
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.users import User
from app.schemas.auth_schema import SignupRequest, UserResponse,TokenResponse,LoginRequest
from app.core.jwt import create_access_token,create_refresh_token
from app.core.pshashing import verify_password
from app.core.pshashing import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest,db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.email == str(data.email)))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )
    hashed_password = hash_password(data.password)
    new_user = User(
        name=data.name,
        email=str(data.email),
        phone=data.phone,
        password_hash=hashed_password,
        role="patient",
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

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
    # 1. Find the user by email
    user = db.scalar(
        select(User).where(User.email == str(data.email))
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