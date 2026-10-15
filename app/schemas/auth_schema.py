from pydantic import BaseModel, EmailStr, Field, ConfigDict


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: str

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


from pydantic import BaseModel


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
