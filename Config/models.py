from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class BasicAuthData(BaseModel):
    """Base data model for basic auth actions"""

    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class SignupData(BasicAuthData):
    """Data model for signup action"""

    display_name: Optional[str] = None


class SigninData(BasicAuthData):
    """Data model for signin action"""


class ResetPasswordData(BaseModel):
    """Data model for reset password action"""

    email: EmailStr


class ChangePasswordData(BaseModel):
    """Data model for change password action"""

    uid: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class GoogleAuthData(BaseModel):
    """Data model for Google OAuth actions"""

    id_token: str


class AuthRequest(BaseModel):
    """Main authentication request model"""

    type: str
    action: str
    data: dict  # Will be validated based on action
