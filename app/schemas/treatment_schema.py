
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TreatmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    fee: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class TreatmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    duration_minutes: int
    fee: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TreatmentUpdate(BaseModel):
    name: str | None = Field(
        default=None, min_length=2, max_length=100
    )
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    fee: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    is_active: bool | None = None
