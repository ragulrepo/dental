from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int
    date_of_birth: date
    gender: Literal["male", "female", "trans"]
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_must_not_be_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class UserResponse(BaseModel):
    name: str
    age: int
    date_of_birth: date | None
    gender: Literal["male", "female", "trans"]
    email: EmailStr
    phone: str | None
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    age: int | None = Field(default=None, ge=0)
    date_of_birth: date | None = None
    gender: Literal["male", "female", "trans"] | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_must_not_be_in_the_future(
        cls, value: date | None
    ) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
