# =============================================================
#  app/schemas/user.py — Pydantic schemas for auth endpoints
# =============================================================

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Payload for POST /auth/signup."""
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """Payload for POST /auth/login."""
    email: EmailStr
    password: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Safe user representation — never exposes password_hash."""
    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# JWT token schemas
# ---------------------------------------------------------------------------

class Token(BaseModel):
    """Returned by POST /auth/login on success."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded inside the JWT payload."""
    sub: str  # user id as string
