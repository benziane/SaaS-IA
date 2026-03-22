"""
User schemas for request/response validation
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
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
                "created_at": "2025-11-13T21:00:00Z"
            }
        }


class UserUpdateProfile(BaseModel):
    """Schema for updating user profile"""
    full_name: str = Field(..., min_length=1, max_length=255)

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

