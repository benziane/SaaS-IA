"""
User schemas for request/response validation
"""

import re
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import Role
from app.utils.sanitize import sanitize_string

# Minimum password complexity: at least one letter and one digit
_PASSWORD_LETTER_RE = re.compile(r"[a-zA-Z]")
_PASSWORD_DIGIT_RE = re.compile(r"\d")


def _validate_password_strength(password: str) -> str:
    """Shared password strength validation logic."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not _PASSWORD_LETTER_RE.search(password):
        raise ValueError("Password must contain at least one letter")
    if not _PASSWORD_DIGIT_RE.search(password):
        raise ValueError("Password must contain at least one digit")
    return password


def _validate_full_name(name: Optional[str]) -> Optional[str]:
    """Shared full_name validation logic."""
    if name is None:
        return None
    name = sanitize_string(name)
    if not name:
        raise ValueError("full_name must not be empty after sanitization")
    if len(name) > 255:
        raise ValueError("full_name must not exceed 255 characters")
    return name


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: Optional[str]) -> Optional[str]:
        return _validate_full_name(v)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # OAuth2 requires 'username' field
    password: str


class UserRead(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    full_name: Optional[str]
    role: Role
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "email_verified": False,
                "created_at": "2025-11-13T21:00:00Z"
            }
        }


class UserUpdateProfile(BaseModel):
    """Schema for updating user profile"""
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        result = _validate_full_name(v)
        if result is None:
            raise ValueError("full_name is required")
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Jane Doe"
            }
        }


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def check_new_password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response (legacy, kept for backward compatibility)"""
    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenResponse(BaseModel):
    """Schema for JWT token response with refresh token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenData(BaseModel):
    """Schema for token payload"""
    email: Optional[str] = None

