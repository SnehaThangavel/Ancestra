"""Pydantic schemas for authentication, token refreshing, and user profiles."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing an expired access token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response schema containing issued JWT access and refresh tokens."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for authenticated user profile."""

    id: uuid.UUID
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LogoutResponse(BaseModel):
    """Response schema for logout action."""

    status: str = "success"
    message: str = "Successfully logged out. Please discard stored JWT tokens."
