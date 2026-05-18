import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    role: str

    class Config:
        from_attributes = True


class AddressCreate(BaseModel):
    label: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str
    pincode: str
    phone: str
    is_default: bool = False


class AddressResponse(BaseModel):
    id: uuid.UUID
    label: str | None
    line1: str
    line2: str | None
    city: str
    state: str
    pincode: str
    phone: str
    is_default: bool

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    name: str | None = None
