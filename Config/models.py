from typing import Literal, Optional

from firebase_admin import auth
from pydantic import BaseModel, EmailStr, Field, field_validator

from shared.firestore import FirestoreClient


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
    role: Literal["driver", "rider"] = Field(..., description="User role in the system")


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


class UserRecord(BaseModel):
    """Firebase UserRecord model"""

    uid: str
    email: EmailStr
    email_verified: bool
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    disabled: bool

    @classmethod
    def from_firebase_user(cls, user: auth.UserRecord):
        return cls(
            uid=user.uid,
            email=user.email,
            email_verified=user.email_verified,
            phone_number=user.phone_number,
            display_name=user.display_name,
            photo_url=user.photo_url,
            disabled=user.disabled,
        )


class UserProfile(BaseModel):
    """User profile model for Firestore collection"""

    uid: str = Field(..., description="Firebase UID")
    name: Optional[str] = Field(..., description="User's display name")
    email: EmailStr = Field(..., description="User's email address")
    role: Literal["driver", "rider"] = Field(..., description="User role in the system")
    status: Literal["online", "offline"] = Field(
        default="offline", description="User's current status"
    )
    location: Optional[dict] = Field(
        default=None, description="User's current location (lat, lng)"
    )
    phone_number: Optional[str] = Field(default=None, description="User's phone number")
    photo_url: Optional[str] = Field(
        default=None, description="User's profile photo URL"
    )

    @field_validator("location")
    def validate_location(cls, v):
        if v is not None:
            if not isinstance(v, dict) or "lat" not in v or "lng" not in v:
                raise ValueError("Location must contain 'lat' and 'lng' fields")
            if not isinstance(v["lat"], (int, float)) or not isinstance(
                v["lng"], (int, float)
            ):
                raise ValueError("Latitude and longitude must be numbers")
        return v


class User(FirestoreClient):
    """User class for Firestore operations"""

    collection_name = "users"
    model = UserProfile
