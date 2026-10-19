from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import literal


class DentistCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(gt=0)
    gender: Literal["male", "female", "trans"]
    email: str = Field(min_length=5, max_length=255)
    phone: str | None = None
    address: str | None = Field(default=None, max_length=255)
    specialization: str = Field(min_length=2, max_length=100)
    qualification: str = Field(min_length=2, max_length=150)
    experience_years: int = Field(default=0, ge=0)
    bio: str | None = None


class DentistResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: Literal["male", "female", "trans"]
    user_id: int
    specialization: str
    qualification: str
    experience_years: int
    bio: str | None
    is_active: bool
    address: str | None

    # Include selected fields from the related User
    name: str
    email: str
    phone: str | None

    model_config = ConfigDict(from_attributes=True)

class DentistUpdate(BaseModel):
    specialization: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    qualification: str | None = Field(
        default=None, min_length=2, max_length=150
    )
    experience_years: int | None = Field(default=None, ge=0)
    bio: str | None = None
    is_active: bool | None = None
