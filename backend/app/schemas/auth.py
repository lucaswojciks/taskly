"""Pydantic schemas for the authentication feature (see docs/specs/auth.md)."""

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Body of ``POST /auth/register``."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    """Body of ``POST /auth/login``."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public representation of a user. Never exposes ``hashed_password``."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: dt.datetime


class Token(BaseModel):
    """Body of a successful ``POST /auth/login``."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
