from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from app.models.appointments_model import AppointmentStatus


class AppointmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0)
    phone: str = Field(min_length=7, max_length=20)
    date_of_birth: date
    gender: Literal["male", "female", "trans"]
    dentist_id: int = Field(gt=0)
    treatment_id: int = Field(gt=0)
    starts_at: datetime
    
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("starts_at")
    @classmethod
    def starts_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("starts_at must include a timezone offset")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_must_not_be_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentPatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    phone: str | None
    date_of_birth: date | None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("gender")
    def serialize_gender(self, gender: str) -> str:
        return gender.title()


class AppointmentResponse(BaseModel):
    id: int
    patient: AppointmentPatientResponse
    dentist_id: int
    treatment_id: int
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    notes: str | None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def time_slot(self) -> str:
        start = self.starts_at.strftime("%I:%M %p")
        end = self.ends_at.strftime("%I:%M %p")
        return f"{start} - {end} UTC"


class RatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str | None = None
