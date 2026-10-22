"""
Authentication request and response schemas.
"""

from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None
    role: Optional[str] = "investigator"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "analyst"
    is_active: bool = True



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int
