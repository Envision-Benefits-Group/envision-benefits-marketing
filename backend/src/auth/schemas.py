# src.auth.schemas.py

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

if TYPE_CHECKING:
    pass

# Import at runtime to avoid circular imports


# Shared properties for Pydantic models
class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True
    name: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=40)
    agreed_to_terms: bool = Field(
        ..., description="Indicates the user has agreed to the Terms & Agreements."
    )

    @model_validator(mode="after")
    def ensure_terms_accepted(self):
        if not self.agreed_to_terms:
            raise ValueError("You must agree to the Terms & Agreements to sign up.")
        return self


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)
    current_password: Optional[str] = Field(default=None, min_length=8, max_length=40)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=40)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password and not self.current_password:
            raise ValueError("Current password must be provided to set a new password")
        return self


# User public-facing schema
class UserDetailResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Token response schema
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Token payload (for JWT tokens)
class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Generic message schema
class Message(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=40)
